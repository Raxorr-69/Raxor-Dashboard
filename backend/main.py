from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from api.routes import (
    afk,
    automod,
    auth,
    guilds,
    invites,
    leaderboard,
    leveling,
    moderation,
    recovery,
    settings,
    statistics,
    users,
)
from core.config import CORS_ORIGINS, ENVIRONMENT
from core.hardening import rate_limit, security_headers
from db import sessions as session_repo
from db.database import create_database_pool, close_database_pool
from utils.validators import InvalidSnowflakeError


# The production Docker image builds the React app into frontend/dist.
# FastAPI serves that build so the whole dashboard can run as ONE Render
# web service instead of requiring a separate static-site deployment.
FRONTEND_DIST = (Path(__file__).resolve().parent.parent / "frontend" / "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the shared database pool on startup, close it on shutdown.

    Also ensures the dashboard's own session table exists — see
    db/sessions.py's module docstring for why sessions live in Postgres
    (survives restarts, works across multiple API workers) rather than
    in an in-memory dict, and why this is the one table the dashboard
    creates for itself instead of only reading tables the bot created.
    """

    app.state.pool = await create_database_pool()
    await session_repo.ensure_schema(app.state.pool)
    yield
    await close_database_pool(app.state.pool)


app = FastAPI(
    title="Raxor Dashboard API",
    description=(
        "Web dashboard for the Raxor Discord bot. Reads and writes the "
        "same Postgres database as the bot; does not share any code with it."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Keep the public API usable while making credential and write endpoints
    # substantially harder to brute-force or spam.
    path = request.url.path
    if path in {"/auth/login", "/auth/exchange"}:
        limited = rate_limit(request, limit=10, window_seconds=60, scope=path)
        if limited:
            return limited
    elif request.method in {"POST", "PUT", "PATCH", "DELETE"} and path.startswith("/guilds/"):
        limited = rate_limit(request, limit=120, window_seconds=60, scope="guild-write")
        if limited:
            return limited

    response = await call_next(request)
    for name, value in security_headers(production=ENVIRONMENT == "production").items():
        response.headers.setdefault(name, value)
    return response


@app.exception_handler(InvalidSnowflakeError)
async def invalid_snowflake_handler(request: Request, exc: InvalidSnowflakeError):
    """A malformed Discord id (guild/user/channel/role) in a path, query,
    or body param should read as a normal 400, not bubble up into a 500.
    In practice `require_guild_access` already filters most bad
    `guild_id`s out (see api/dependencies.py), so this mostly guards ids
    that appear further down in a request, e.g. an invalid `user_id`
    filter or a garbage id typed into a whitelist/level-reward form."""

    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


# =========================
# Routers
# =========================

app.include_router(auth.router)
app.include_router(guilds.router)
app.include_router(settings.router)
app.include_router(automod.router)
app.include_router(moderation.router)
app.include_router(leveling.router)
app.include_router(leaderboard.router)
app.include_router(statistics.router)
app.include_router(users.router)
app.include_router(afk.router)
app.include_router(invites.router)
app.include_router(recovery.router)


@app.get("/config.js", include_in_schema=False)
async def runtime_config():
    """Expose only non-secret browser configuration at runtime.

    Keeping the Discord OAuth client id here avoids baking a Render secret/build
    argument into the Docker image. Client IDs are public by design; the OAuth
    client secret remains backend-only.
    """
    from core.config import DISCORD_CLIENT_ID
    body = (
        "window.__RAXOR_CONFIG__ = "
        + __import__("json").dumps({"discordClientId": DISCORD_CLIENT_ID})
        + ";"
    )
    from fastapi.responses import Response
    return Response(content=body, media_type="application/javascript", headers={"Cache-Control": "no-store"})


@app.get("/health")
async def health():
    """Simple liveness check for uptime monitoring / hosting platforms."""

    return {"status": "ok"}


@app.get("/{full_path:path}", include_in_schema=False)
async def frontend(full_path: str):
    """Serve the React SPA from the same Render service as FastAPI.

    API/auth routes are registered above this catch-all, so they keep their
    normal FastAPI behaviour. Existing frontend files are served directly;
    every other browser route falls back to index.html for React Router.

    A path that looks like an API call to a router with no frontend
    route of its own (`/guilds/...`, `/health`) but didn't match
    anything gets a real 404 here instead of silently falling through to
    index.html — otherwise a typo in an API path would come back as an
    HTML page with a 200 status, which `fetch().json()` on the frontend
    would fail to parse in a confusing way rather than surfacing as a
    clean 404. This deliberately does NOT do the same for `/auth/...`:
    the frontend's own `/auth/callback` route (see App.jsx) lives at
    that exact prefix, so blocking it here would break login instead of
    protecting anything — the backend's actual auth endpoints
    (`/auth/login`, `/auth/discord/callback`, `/auth/exchange`,
    `/auth/me`, `/auth/logout`) are all registered above this catch-all
    and already take priority over it regardless.
    """

    if full_path == "health" or full_path.startswith("guilds"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")

    if not FRONTEND_DIST.is_dir():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Frontend build is not available.",
        )

    requested = (FRONTEND_DIST / full_path).resolve()
    try:
        requested.relative_to(FRONTEND_DIST.resolve())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")

    if requested.is_file():
        return FileResponse(requested)

    return FileResponse(FRONTEND_DIST / "index.html")
