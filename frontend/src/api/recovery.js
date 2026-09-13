import { apiClient } from "./client";

export function listRecoveryState(guildId) {
  return apiClient.get(`/guilds/${guildId}/recovery`);
}

/** Queue an on-demand rescan of a channel. Raxor's own poll loop picks
 * this up within ~20 seconds — see backend/api/routes/recovery.py. */
export function triggerRescan(guildId, channelId) {
  return apiClient.post(`/guilds/${guildId}/recovery/${channelId}/rescan`);
}
