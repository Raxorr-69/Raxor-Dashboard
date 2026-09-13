from pydantic import BaseModel


class GuildAccess(BaseModel):
    """A guild the logged-in user is allowed to manage on the dashboard."""

    id: str
    name: str
    icon_url: str | None = None
    is_bot_present: bool


class UserOut(BaseModel):
    id: str
    username: str
    avatar_url: str | None = None
    is_developer: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    guilds: list[GuildAccess]
