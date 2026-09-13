import { apiClient } from "./client";

export function getLeaderboard(guildId, { category = "messages", period = "weekly", limit } = {}) {
  return apiClient.get(`/guilds/${guildId}/leaderboard`, { category, period, limit });
}
