import { apiClient } from "./client";

export function getOverview(guildId) {
  return apiClient.get(`/guilds/${guildId}/statistics/overview`);
}

export function getActivity(guildId, period = "weekly") {
  return apiClient.get(`/guilds/${guildId}/statistics/activity`, { period });
}

export function getChannelStats(guildId, period = "weekly", limit) {
  return apiClient.get(`/guilds/${guildId}/statistics/channels`, { period, limit });
}
