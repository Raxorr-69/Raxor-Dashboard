from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    value: int


class ActivityPoint(BaseModel):
    date: str
    value: int


class ChannelStatEntry(BaseModel):
    channel_id: str
    value: int


class StatisticsOverview(BaseModel):
    total_messages: int
    total_voice_seconds: int
    tracked_users: int
    period_days: int


class InviteLeaderboardEntry(BaseModel):
    rank: int
    inviter_id: str
    invite_count: int
