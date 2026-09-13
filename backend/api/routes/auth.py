import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from api.dependencies import get_current_session, get_db_pool, refresh_session_guilds
from core.config import (
    BOT_OWNER_ID,
    DISCORD_CLIENT_ID,
    DISCORD_REDIRECT_URI,
    ENVIRONMENT,
    FRONTEND_URL,
)
from core.constants import DISCORD_OAUTH_AUTHORIZE_URL, DISCORD_OAUTH_SCOPES
from core.security import (
    consume_login_code,
    create_login_code,
    mint_session_jwt,
    new_session_id,
    session_expiry,
)
from db import sessions as session_repo
from services.discord import (
    DiscordOAuthError,
    exchange_code_for_token,
    fetch_current_user,
    fetch_current_user_guilds,
)
from services.guild_service import resolve_manageable_guilds


router = APIRouter(prefix="/auth", tags=["auth"])


DISCORD_CDN = "https://cdn.discordapp.com"
OAUTH_STATE_COOKIE = "oauth_state"


class ExchangeRequest(BaseModel):
    login_code: str


def _avatar_url(user: dict) -> str | None:
    if not user.get("avatar"):
        return None
    return f"{DISCORD_CDN}/avatars/{user['id']}/{user['avatar']}.png"


@router.get("/login")
async def login():
    """Redirect the browser to Discord's OAuth2 consent screen.

    A random `state` value is generated here, sent to Discord, and
    stashed in an httponly cookie. `/discord/callback` below requires
    the value Discord echoes back to match that cookie before it
    exchanges anything — without this, an attacker could get a victim
    to complete *the attacker's own* OAuth flow inside the victim's
    browser, linking the victim's dashboard session to the attacker's
    Discord account (a standard OAuth login-CSRF).
    """

    state = secrets.token_urlsafe(32)

    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": DISCORD_OAUTH_SCOPES,
        "prompt": "consent",
        "state": state,
    }

    redirect = RedirectResponse(f"{DISCORD_OAUTH_AUTHORIZE_URL}?{urlencode(params)}")
    redirect.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        max_age=600,
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
    )
    return redirect


@router.get("/discord/callback")
async def callback(code: str, state: str, request: Request):
    """Handle Discord's OAuth2 redirect.

    Lives at `/auth/discord/callback`, not `/auth/callback` — the
    frontend's own client-side route for landing after login is
    `/auth/callback` (see App.jsx), and in the single-service Docker
    deployment (see ../../Dockerfile) frontend and backend share one
    origin. If this route were also `/auth/callback`, it would shadow
    the frontend's route entirely (FastAPI's routers are registered
    before the SPA catch-all in main.py), so the second leg of login —
    the browser landing back on `/auth/callback?login_code=...` — would
    hit this handler instead of the React app, with a 422 for missing
    `code`/`state` instead of a working login.

    Verifies `state` against the cookie set in `/login`, exchanges the
    code for an access token, resolves which guilds the user can
    manage, and opens a session (a row in db/sessions.py's
    dashboard_sessions table).

    The redirect back to the frontend carries a one-time `login_code`
    (see core/security.py), NOT the session JWT itself — a JWT sitting
    in a URL would end up in browser history and potentially in
    server/proxy access logs. The frontend (see
    auth/AuthProvider.jsx) immediately exchanges that code for the real
    token via `POST /auth/exchange`, which never puts anything in a URL.
    """

    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if not cookie_state or not secrets.compare_digest(cookie_state, state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired login attempt. Please try logging in again.",
        )

    pool = request.app.state.pool

    try:
        token_data = await exchange_code_for_token(code)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")

        discord_user = await fetch_current_user(access_token)
        discord_guilds = await fetch_current_user_guilds(access_token)
    except DiscordOAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    manageable_guilds = await resolve_manageable_guilds(pool, discord_guilds)

    session_id = new_session_id()
    await session_repo.insert_session(
        pool,
        session_id=session_id,
        discord_user_id=discord_user["id"],
        username=discord_user["username"],
        avatar=_avatar_url(discord_user),
        is_developer=discord_user["id"] == str(BOT_OWNER_ID),
        access_token=access_token,
        refresh_token=refresh_token,
        guilds=manageable_guilds,
        expires_at=session_expiry(),
    )

    login_code = create_login_code(session_id)

    redirect_url = f"{FRONTEND_URL}/auth/callback?{urlencode({'login_code': login_code})}"
    response = RedirectResponse(redirect_url)
    response.delete_cookie(OAUTH_STATE_COOKIE)
    return response


@router.post("/exchange")
async def exchange(payload: ExchangeRequest):
    """Trade a one-time `login_code` (from the `/callback` redirect URL)
    for the real session JWT. Single-use: calling this twice with the
    same code fails the second time (see core/security.py's
    consume_login_code) — the code is only ever meant to survive the
    instant between the OAuth redirect landing and this call firing.
    """

    session_id = consume_login_code(payload.login_code)
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This login link has expired or already been used. Please log in again.",
        )

    return {"token": mint_session_jwt(session_id)}


@router.get("/me")
async def me(
    session: dict = Depends(get_current_session),
    pool=Depends(get_db_pool),
):
    """Return the logged-in user's profile and manageable guild list.

    This is the dashboard's own bootstrap call (see
    auth/AuthProvider.jsx), so the guild list is always refreshed live
    here rather than served from cache — it's the first place a revoked
    permission or a server the bot just got kicked from should stop
    showing up.
    """

    await refresh_session_guilds(session, pool)

    return {
        "id": session["discord_user_id"],
        "username": session["username"],
        "avatar_url": session["avatar"],
        "is_developer": session.get("is_developer", False),
        "guilds": session.get("guilds", []),
    }


@router.post("/logout")
async def logout(
    session: dict = Depends(get_current_session),
    pool=Depends(get_db_pool),
):
    """Invalidate the current session immediately by deleting its row —
    unlike a stateless JWT, this takes effect right away rather than
    waiting for the token's own expiry."""

    await session_repo.delete_session(pool, session["session_id"])
    return {"detail": "Logged out."}
