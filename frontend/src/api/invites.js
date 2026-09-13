import { apiClient } from "./client";

export function getInviteLeaderboard(guildId, limit) {
  return apiClient.get(`/guilds/${guildId}/invites/leaderboard`, { limit });
}

export function getMemberInviter(guildId, userId) {
  return apiClient.get(`/guilds/${guildId}/invites/${userId}`);
}
