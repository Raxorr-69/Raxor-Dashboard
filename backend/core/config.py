import os
import base64
import hashlib

from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# =========================
# Database
# =========================
#
# The dashboard reads and writes the SAME Postgres database as the Raxor
# bot (see the bot's database/models.py for the table definitions). The
# dashboard does not create or migrate tables — the bot owns the schema.

DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# Discord OAuth2
# =========================

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

# Where to send the browser after a successful login
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# =========================
# Sessions (JWT)
# =========================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
# Short on purpose: the JWT itself only references a server-side session
# (see core/security.py) which re-verifies the user's Discord guild
# permissions on its own schedule, so this mainly bounds how long a
# stolen/leaked token stays usable, not how fresh permissions are.
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))  # 1 hour


# =========================
# Bot Identity
# =========================
#
# Used only to label the developer/owner in the dashboard UI (e.g. show a
# "Developer" badge). This does not grant extra API access by itself.

BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))


# =========================
# Bot Integration (optional)
# =========================
#
# Lets the dashboard ask Raxor's already-running process for read-only
# guild data (channel list, role list, member search) that a user's own
# Discord OAuth login can't see — backs the channel/role selectors and
# username search (see services/discord.py). This calls the bot's own
# small internal HTTP API (Raxor/web/internal.py), not Discord's API
# directly, and DASHBOARD_INTERNAL_KEY is a separate secret with no
# Discord privileges of its own — it is NOT the bot's Discord token,
# and the dashboard never holds that token. If a compromised dashboard
# leaked this key, the worst case is "read channels/roles/members of
# guilds Raxor is in", not control of the bot.
#
# Leave either unset and the channel/role selectors and username search
# fall back to plain manual ID entry instead of erroring.

BOT_INTERNAL_API_URL = os.getenv("BOT_INTERNAL_API_URL")  # e.g. http://localhost:8080
DASHBOARD_INTERNAL_KEY = os.getenv("DASHBOARD_INTERNAL_KEY")
SESSION_ENCRYPTION_KEY = os.getenv("SESSION_ENCRYPTION_KEY")
if SESSION_ENCRYPTION_KEY:
    SESSION_ENCRYPTION_FERNET_KEY = base64.urlsafe_b64encode(
        hashlib.sha256(SESSION_ENCRYPTION_KEY.encode("utf-8")).digest()
    )
else:
    SESSION_ENCRYPTION_FERNET_KEY = None


# =========================
# Application
# =========================

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

_cors_origins = os.getenv("CORS_ORIGINS", FRONTEND_URL)
CORS_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]


# =========================
# Validation
# =========================

_required = {
    "DATABASE_URL": DATABASE_URL,
    "DISCORD_CLIENT_ID": DISCORD_CLIENT_ID,
    "DISCORD_CLIENT_SECRET": DISCORD_CLIENT_SECRET,
    "DISCORD_REDIRECT_URI": DISCORD_REDIRECT_URI,
    "JWT_SECRET_KEY": JWT_SECRET_KEY,
    "SESSION_ENCRYPTION_KEY": SESSION_ENCRYPTION_KEY,
}

_missing = [name for name, value in _required.items() if not value]

if _missing:
    raise ValueError(
        f"Missing required environment variables: {', '.join(_missing)}"
    )

if ENVIRONMENT == "production":
    if len(JWT_SECRET_KEY or "") < 32:
        raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production.")
    if len(SESSION_ENCRYPTION_KEY or "") < 32:
        raise ValueError("SESSION_ENCRYPTION_KEY must be at least 32 characters in production.")
    if not FRONTEND_URL.startswith("https://"):
        raise ValueError("FRONTEND_URL must use HTTPS in production.")
    if not DISCORD_REDIRECT_URI.startswith("https://"):
        raise ValueError("DISCORD_REDIRECT_URI must use HTTPS in production.")
    if BOT_INTERNAL_API_URL and not BOT_INTERNAL_API_URL.startswith("https://"):
        raise ValueError("BOT_INTERNAL_API_URL must use HTTPS in production.")
    if "*" in CORS_ORIGINS:
        raise ValueError("CORS_ORIGINS cannot contain '*' in production.")
    # Bot integration is optional (see the comment block above) — only
    # enforce a strong key when the deployment has actually opted in by
    # setting BOT_INTERNAL_API_URL. Requiring it unconditionally would
    # break every production deployment that doesn't use this feature.
    if BOT_INTERNAL_API_URL and (not DASHBOARD_INTERNAL_KEY or len(DASHBOARD_INTERNAL_KEY) < 32):
        raise ValueError(
            "DASHBOARD_INTERNAL_KEY must be at least 32 characters in production "
            "when BOT_INTERNAL_API_URL is set."
        )
