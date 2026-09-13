import { apiClient } from "./client";

export function getAutoModSettings(guildId) {
  return apiClient.get(`/guilds/${guildId}/automod`);
}

export function updateAutoModSettings(guildId, updates) {
  return apiClient.patch(`/guilds/${guildId}/automod`, updates);
}
