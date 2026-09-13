from pydantic import BaseModel


class GuildOut(BaseModel):
    """Basic info for the guild selector."""

    id: str
    name: str
    icon_url: str | None = None
    member_count: int | None = None
    is_bot_present: bool


class GuildDetailOut(GuildOut):
    """Guild info plus a snapshot used on the Overview page."""

    message_tracking_enabled: bool
    voice_tracking_enabled: bool
    leveling_enabled: bool
    spam_enabled: bool
    link_protection_enabled: bool
