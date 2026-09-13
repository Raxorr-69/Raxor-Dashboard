from pydantic import BaseModel, Field


class GuildSettingsOut(BaseModel):
    """Full snapshot of a guild's `guilds` row, camel-free (matches the
    bot's column names exactly so there's no name-mapping to get wrong)."""

    guild_id: str

    message_tracking_enabled: bool
    voice_tracking_enabled: bool

    spam_enabled: bool
    link_protection_enabled: bool

    spam_message_limit: int
    spam_message_window: int
    emoji_spam_limit: int

    spam_action: str
    spam_timeout_seconds: int

    emoji_spam_action: str
    emoji_spam_timeout_seconds: int

    link_action: str
    link_timeout_seconds: int

    leveling_enabled: bool
    xp_min: int
    xp_max: int

    level_up_messages_enabled: bool
    level_up_channel_id: str | None = None
    announcement_channel_id: str | None = None

    welcome_enabled: bool
    welcome_channel_id: str | None = None
    welcome_message: str = "Welcome {user} to {server}! 🎉"
    welcome_gif_url: str | None = None
    leave_enabled: bool
    leave_channel_id: str | None = None
    leave_message: str = "{username} has left {server}. 👋"
    leave_gif_url: str | None = None
    level_up_message: str = "{user} reached **Level {level}**! 🎉"
    level_up_gif_url: str | None = None

    verification_enabled: bool
    verification_channel_id: str | None = None
    verification_role_id: str | None = None


class GuildSettingsUpdate(BaseModel):
    """PATCH body — every field optional, only provided fields are written.

    Each field is validated the same way the bot validates it (see
    db/repositories.py: update_guild_setting) before being persisted.
    """

    message_tracking_enabled: bool | None = None
    voice_tracking_enabled: bool | None = None

    spam_enabled: bool | None = None
    link_protection_enabled: bool | None = None

    spam_message_limit: int | None = Field(default=None, ge=1)
    spam_message_window: int | None = Field(default=None, ge=1)
    emoji_spam_limit: int | None = Field(default=None, ge=1)

    spam_action: str | None = None
    spam_timeout_seconds: int | None = Field(default=None, ge=1)

    emoji_spam_action: str | None = None
    emoji_spam_timeout_seconds: int | None = Field(default=None, ge=1)

    link_action: str | None = None
    link_timeout_seconds: int | None = Field(default=None, ge=1)

    leveling_enabled: bool | None = None
    xp_min: int | None = Field(default=None, ge=1)
    xp_max: int | None = Field(default=None, ge=1)

    level_up_messages_enabled: bool | None = None
    level_up_channel_id: str | None = None
    announcement_channel_id: str | None = None
    welcome_enabled: bool | None = None
    welcome_channel_id: str | None = None
    welcome_message: str | None = Field(default=None, max_length=4096)
    welcome_gif_url: str | None = Field(default=None, max_length=1000)
    leave_enabled: bool | None = None
    leave_channel_id: str | None = None
    leave_message: str | None = Field(default=None, max_length=4096)
    leave_gif_url: str | None = Field(default=None, max_length=1000)
    level_up_message: str | None = Field(default=None, max_length=4096)
    level_up_gif_url: str | None = Field(default=None, max_length=1000)
    verification_enabled: bool | None = None
    verification_channel_id: str | None = None
    verification_role_id: str | None = None
