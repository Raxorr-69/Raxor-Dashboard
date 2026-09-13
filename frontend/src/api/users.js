import { apiClient } from "./client";

export function listUsers(guildId, { sort = "xp", search, limit, offset } = {}) {
  return apiClient.get(`/guilds/${guildId}/users`, { sort, search, limit, offset });
}

export function getUserProfile(guildId, userId) {
  return apiClient.get(`/guilds/${guildId}/users/${userId}`);
}
