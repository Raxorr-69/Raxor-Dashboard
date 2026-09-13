import { apiClient } from "./client";

export function listGuilds() {
  return apiClient.get("/guilds");
}

export function getGuild(guildId) {
  return apiClient.get(`/guilds/${guildId}`);
}

export function getGuildOverview(guildId) {
  return apiClient.get(`/guilds/${guildId}/overview`);
}
