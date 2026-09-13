import { apiClient } from "./client";

export function listAfkUsers(guildId) {
  return apiClient.get(`/guilds/${guildId}/afk`);
}

export function clearAfk(guildId, userId) {
  return apiClient.delete(`/guilds/${guildId}/afk/${userId}`);
}
