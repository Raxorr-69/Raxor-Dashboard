import { apiClient } from "./client";

export function getSettings(guildId) {
  return apiClient.get(`/guilds/${guildId}/settings`);
}

export function updateSettings(guildId, updates) {
  return apiClient.patch(`/guilds/${guildId}/settings`, updates);
}
