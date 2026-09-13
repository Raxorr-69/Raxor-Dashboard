from pydantic import BaseModel, Field


class LevelRewardOut(BaseModel):
    level: int
    role_id: str = ""


class LevelRewardIn(BaseModel):
    # Matches the bot's own "Level N" role-name regex (web/internal.py):
    # 1-4 digits, no leading zero, so 1-9999.
    level: int = Field(ge=1, le=9999)
    role_id: str = ""


class LeaderboardRewardOut(BaseModel):
    leaderboard_type: str
    role_id: str = ""


class LeaderboardRewardIn(BaseModel):
    leaderboard_type: str  # "messages" | "voice"
    role_id: str = ""


class UserProfileOut(BaseModel):
    user_id: str
    xp: int
    level: int
    message_count: int
    voice_seconds: int
    warnings: int
