# =========================
# Discord API
# =========================

DISCORD_API_BASE_URL = "https://discord.com/api/v10"
DISCORD_OAUTH_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
DISCORD_OAUTH_TOKEN_URL = "https://discord.com/api/oauth2/token"

# "identify" to read the user's profile, "guilds" to read which servers
# they're in (and their permission level in each).
DISCORD_OAUTH_SCOPES = "identify guilds"


# =========================
# Discord Permission Bits
# =========================
# https://discord.com/developers/docs/topics/permissions

PERMISSION_ADMINISTRATOR = 0x8
PERMISSION_MANAGE_GUILD = 0x20


# =========================
# Guild Settings — Allowed Values
# =========================
#
# Mirrors the constraints enforced by the bot itself (see the bot's
# database/repositories.py) so the dashboard can never write a value the
# bot doesn't understand.

MODERATION_ACTIONS = {"warn", "delete", "timeout"}
LINK_ACTIONS = {"warn", "delete", "timeout"}

RESTRICTION_TYPES = {
    "image_only",
    "clips_only",
}

LEADERBOARD_TYPES = {"messages", "voice"}

RANK_CATEGORIES = {"messages", "voice", "text", "voicechannel", "level"}
RANK_PERIODS = {"weekly", "monthly", "all"}


# =========================
# Pagination
# =========================

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
