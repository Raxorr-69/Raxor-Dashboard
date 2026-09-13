# Raxor Dashboard

Web dashboard for the [Raxor](../Raxor) Discord bot. It is a **separate
codebase** from the bot — different language runtime (FastAPI + React vs.
discord.py), its own repo-worthy `backend/` and `frontend/` folders, its
own `.env` — that happens to read and write the **same PostgreSQL
database** the bot uses. Nothing here imports bot code, and nothing in
the bot imports dashboard code.

```
┌─────────────────┐        HTTP (OAuth2, REST)        ┌──────────────────┐
│  frontend (Vite) │ ─────────────────────────────────▶│ backend (FastAPI) │
│  localhost:5173  │◀─────────────────────────────────  │  localhost:8000   │
└─────────────────┘                                    └─────────┬────────┘
                                                                  │ asyncpg
                                                                  ▼
                                                         ┌──────────────────┐
                                                         │   PostgreSQL     │
                                                         │ (same DATABASE_ │
                                                         │  URL as the bot) │
                                                         └─────────┬────────┘
                                                                  ▲
                                                                  │ asyncpg
                                                         ┌────────┴─────────┐
                                                         │   Raxor bot      │
                                                         │ (discord.py)     │
                                                         └──────────────────┘
```

## How the two projects connect

1. **Shared database, mostly one-directional.** Point the dashboard's
   `backend/.env` `DATABASE_URL` at the exact same Postgres database as
   the bot's `Raxor/.env`. The bot owns almost the entire schema
   (`database/models.py` creates every one of its tables); the
   dashboard only ever reads/writes rows in those tables — it never
   migrates or alters them. The one exception is
   `dashboard_sessions` (see `backend/db/sessions.py`), a table the
   dashboard creates and owns entirely for its own login sessions,
   since a logged-in dashboard user isn't something the bot's schema
   has (or needs) any concept of. Table and column names in the bot's
   tables are kept in sync by hand (see
   `backend/db/repositories.py`'s module docstring) — if you rename a
   column in the bot's `database/models.py`, mirror the change there.
2. **Independent processes.** Run the bot (`python main.py` from
   `Raxor/`), the dashboard API (`uvicorn main:app` from
   `dashboard/backend/`), and the dashboard UI (`npm run dev` from
   `dashboard/frontend/`) as three separate processes, in three separate
   virtualenvs/installs. Restarting or redeploying one never requires
   touching the others.
3. **Discord OAuth, not the bot token.** The dashboard authenticates
   users with their own Discord login (OAuth2 `identify guilds` scope),
   *not* the bot's token — `DISCORD_CLIENT_ID`/`DISCORD_CLIENT_SECRET` in
   `backend/.env` come from the same Discord application as the bot
   (Developer Portal → your app → OAuth2), but the bot's `DISCORD_TOKEN`
   is never given to the dashboard. A user can only manage a server on
   the dashboard if they're the server owner or have Administrator /
   Manage Server there — the same bar the bot's own admin commands use
   (`config/permissions.py` in the bot, `services/discord.py` in the
   dashboard backend).
4. **`BOT_OWNER_ID` matches.** Set the same `BOT_OWNER_ID` in both
   `.env` files so the dashboard shows the "Developer" badge for the
   same account the bot treats as its owner.
5. **`DASHBOARD_INTERNAL_KEY` (optional) is a separate secret, not the
   bot's token.** Set the exact same random value in both `.env` files
   to enable live channel/role dropdowns and username search — these
   need Discord data a user's own OAuth login can't see (a guild's full
   channel/role list, member search), which the dashboard gets by
   calling Raxor's own already-running process
   (`Raxor/web/internal.py`) over plain HTTP, not by calling Discord
   directly. The dashboard never holds Raxor's actual `DISCORD_TOKEN`.
   Leave `DASHBOARD_INTERNAL_KEY` (or `BOT_INTERNAL_API_URL`) unset and
   those three features fall back to plain manual ID/ID-prefix entry
   instead of erroring.
6. **On-demand recovery rescans go through the bot, not around it.**
   The dashboard's Recovery page can queue a rescan, but it only ever
   writes a row to a `recovery_requests` table — Raxor's own
   `recovery_request_poll_loop` (`bot/events.py`) is what actually
   walks Discord message history and updates `message_recovery_state`.
   The dashboard never touches that table directly, so the bot stays
   the single writer of its own recovery state.

## Ports & URLs, out of the box

| Service           | Default address          | Configured by |
|-------------------|---------------------------|---------------|
| Dashboard frontend | http://localhost:5173     | `vite.config.js` |
| Dashboard backend  | http://localhost:8000     | how you invoke `uvicorn` |
| Bot health server  | http://localhost:8080     | `PORT` in `Raxor/.env` (optional) |

The defaults in `backend/.env.example` (`FRONTEND_URL`, `CORS_ORIGINS`,
`DISCORD_REDIRECT_URI=http://localhost:8000/auth/discord/callback`) and
`frontend/.env.example` (`VITE_API_BASE_URL=http://localhost:8000`)
already line up with each other and with the bot's default health-check
port, so a fresh checkout works locally without editing anything beyond
filling in secrets. If you change one side's port, update the matching
value on the other side.

## Setup

**Backend**
```
cd backend
cp .env.example .env   # fill in DATABASE_URL, Discord OAuth creds, JWT_SECRET_KEY, SESSION_ENCRYPTION_KEY, BOT_OWNER_ID
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**
```
cd frontend
cp .env.example .env   # fill in VITE_DISCORD_CLIENT_ID
npm install
npm run dev
```

Add `http://localhost:8000/auth/discord/callback` as a redirect URL on
the Discord application in the Developer Portal, or the OAuth login
will be rejected by Discord before it ever reaches this backend. Note
this is `/auth/discord/callback`, not `/auth/callback` — see
`api/routes/auth.py`'s `/discord/callback` docstring for why the two
can't share a path once frontend and backend share an origin (as they
do in the Render deployment below).

## What lives where

- `backend/` — FastAPI app. Auth (Discord OAuth2 → its own JWT session),
  and one router per feature (`api/routes/`) backed by `services/` and
  raw `asyncpg` queries in `db/repositories.py`.
- `frontend/` — Vite + React app. One page per sidebar item
  (`src/pages/`), a small typed API client per feature (`src/api/`), and
  shared UI in `src/components/`.

## Security notes

- **Session model.** Login opens a session — a row in Postgres
  (`db/sessions.py`'s `dashboard_sessions` table, a table the dashboard
  creates and owns for itself; see that file's docstring for why). The
  JWT handed to the browser only references that row by id; the actual
  Discord access/refresh token and a cached guild-permission snapshot
  live in the row, not in the token. Being in Postgres instead of an
  in-memory dict means a restart or redeploy doesn't log everyone out,
  and multiple API workers/processes all see the same sessions. The
  snapshot is re-verified against Discord whenever it's older than
  `GUILD_CACHE_TTL_SECONDS` (60s), and `require_guild_access` separately
  re-checks bot presence straight from the database on every request.
- **The session JWT never appears in a URL.** The OAuth redirect
  (`/auth/discord/callback`) can only hand the frontend something
  through the URL, so instead of putting the real token there, it
  mints a random, single-use `login_code` (60-second lifetime,
  in-memory, forgotten the instant it's used — see `core/security.py`)
  and redirects with that. The frontend immediately trades it for the
  real JWT via a POST body (`POST /auth/exchange`), which never
  touches a URL, browser history, or an access log.
- **OAuth login is CSRF-protected** via a `state` value round-tripped
  through an httponly cookie (`/auth/login` → `/auth/discord/callback`).
- **Session length** defaults to 1 hour (`JWT_EXPIRE_MINUTES`) — this
  bounds how long a leaked JWT stays redeemable; logging out
  (`POST /auth/logout`) deletes the session row and invalidates it
  immediately regardless of that expiry.
- **Discord access/refresh tokens are encrypted at rest.** Every
  `dashboard_sessions` row's `access_token`/`refresh_token` is encrypted
  with `SESSION_ENCRYPTION_KEY` (Fernet) before being written to
  Postgres, and decrypted on read (see `db/sessions.py`). Legacy
  plaintext rows from before this was added are transparently migrated
  to encrypted form the next time the app starts.
- **The dashboard never holds Raxor's Discord bot token.** Live
  channel/role selectors and username search call Raxor's own running
  process directly (`Raxor/web/internal.py`) over a separate secret,
  `DASHBOARD_INTERNAL_KEY`, that has no Discord privileges beyond those
  three read-only lookups. If the dashboard is ever fully compromised,
  the worst case is "read channels/roles/members of guilds Raxor is
  in" — not a stolen bot token capable of sending messages, banning
  members, or anything else Raxor itself can do.
- **Known limitation: this repo hasn't been through an actual `npm run
  build`.** Everything here has been checked for syntax correctness and
  that every import resolves, but not run through Vite (this
  environment has no network access to install packages). Run
  `npm install && npm run build` yourself before deploying, the normal
  way you'd verify any change to the frontend.


## Render deployment — one Dashboard service

The dashboard is configured to deploy as **one Render Web Service**. The
`Dockerfile` builds the Vite frontend and copies its `dist/` output into the
FastAPI image. FastAPI then serves the React SPA and API from the same origin.
This means the complete project needs only two deployments: **Raxor bot** and
**Raxor Dashboard**.

### Render settings for Dashboard

- Runtime: **Docker**
- Dockerfile: `Dockerfile` (from this project root)
- No separate Static Site is required.
- Render's `PORT` is passed directly to Uvicorn by the Docker `CMD`.
- The frontend defaults to the same origin as the API, so `VITE_API_BASE_URL`
  is not required in production.

Set these Dashboard environment variables in Render:

```text
DATABASE_URL=<same PostgreSQL URL used by Raxor>
DISCORD_CLIENT_ID=<same Discord application client id>
DISCORD_CLIENT_SECRET=<Discord OAuth client secret>
DISCORD_REDIRECT_URI=https://<your-dashboard-domain>/auth/discord/callback
FRONTEND_URL=https://<your-dashboard-domain>
CORS_ORIGINS=https://<your-dashboard-domain>
JWT_SECRET_KEY=<long random secret>
JWT_EXPIRE_MINUTES=60
SESSION_ENCRYPTION_KEY=<different long random secret — see note below>
BOT_OWNER_ID=<your Discord user id>
ENVIRONMENT=production
BOT_INTERNAL_API_URL=<reachable Raxor internal API URL over HTTPS, if enabled>
DASHBOARD_INTERNAL_KEY=<same random secret configured on Raxor, if enabled>
VITE_DISCORD_CLIENT_ID=<same Discord application client id — see note below>
```

`SESSION_ENCRYPTION_KEY` is required (the app refuses to start without it,
in every environment, not just production) — it encrypts the Discord
access/refresh tokens stored in the `dashboard_sessions` table at rest
(see `db/sessions.py`). Generate it the same way as `JWT_SECRET_KEY`, but
use a different value:
```
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
In production it must be at least 32 characters, same as `JWT_SECRET_KEY`.

If `BOT_INTERNAL_API_URL` is set in production, it must start with
`https://` — a plain `http://` internal/private-network URL will fail
startup validation.

`VITE_DISCORD_CLIENT_ID` is a frontend build-time variable, not a
backend runtime one — Render automatically passes every environment
variable you set as a matching Docker build arg (see the `ARG` line in
`Dockerfile`), so setting it here is enough; nothing else to configure.
It's only used to build the "install the bot" link for servers that
don't have Raxor yet (`components/guild/GuildCard.jsx`) — everything
else works fine without it, so it's safe to leave unset if you'd rather
not bother.

If the optional bot internal API is not publicly/reliably reachable from the
Dashboard service, leave `BOT_INTERNAL_API_URL` and
`DASHBOARD_INTERNAL_KEY` unset; the UI falls back to manual ID entry as designed.

Also add the exact `DISCORD_REDIRECT_URI` to the Discord application's OAuth2
redirect URLs — note it ends in `/auth/discord/callback`, not `/auth/callback`
(see `api/routes/auth.py`'s `/discord/callback` docstring for why).

### Automatic channel setup

When **Level-up messages** are enabled and no level-up channel is selected, pressing **Save changes** asks the Raxor bot's authenticated internal API to create (or reuse) a `#level-up` text channel. The returned Discord channel ID is then persisted in PostgreSQL. No Discord channel is created merely by opening the page or changing the toggle; it happens only on Save.
