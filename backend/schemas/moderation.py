from pydantic import BaseModel


class WarningOut(BaseModel):
    warning_id: int
    user_id: str
    moderator_id: str
    reason: str | None = None
    created_at: str


class ChannelRuleOut(BaseModel):
    channel_id: str
    image_only: bool
    clips_only: bool


class ChannelRuleUpdate(BaseModel):
    rule: str  # "image_only" | "clips_only"
    enabled: bool


class WhitelistEntryOut(BaseModel):
    target_id: str
    restriction_type: str


class WhitelistEntryIn(BaseModel):
    target_id: str
    restriction_type: str


class AfkUserOut(BaseModel):
    user_id: str
    reason: str | None = None
    started_at: str
