import { apiClient } from "./client";

export function listLevelRewards(guildId) {
  return apiClient.get(`/guilds/${guildId}/level-rewards`);
}

export function addLevelReward(guildId, level, roleId) {
  return apiClient.post(`/guilds/${guildId}/level-rewards`, { level, role_id: roleId });
}

export function removeLevelReward(guildId, level, roleId) {
  return apiClient.delete(`/guilds/${guildId}/level-rewards/${level}/${roleId}`);
}

export function getLeaderboardRewards(guildId) {
  return apiClient.get(`/guilds/${guildId}/leaderboard-rewards`);
}

export function setLeaderboardReward(guildId, leaderboardType, roleId) {
  return apiClient.put(`/guilds/${guildId}/leaderboard-rewards`, {
    leaderboard_type: leaderboardType,
    role_id: roleId,
  });
}

export function removeLeaderboardReward(guildId, leaderboardType) {
  return apiClient.delete(`/guilds/${guildId}/leaderboard-rewards/${leaderboardType}`);
}
