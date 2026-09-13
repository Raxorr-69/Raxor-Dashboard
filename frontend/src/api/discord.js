import { apiClient } from "./client";

/** Live channel/role lists straight from Discord (via the bot's own
 * token on the backend — see backend/services/discord.py). Both
 * endpoints return an empty list instead of erroring when the backend
 * has no DISCORD_BOT_TOKEN configured, so callers should treat an
 * empty result as "fall back to manual ID entry", not as "this guild
 * has no channels". */
export function getGuildChannels(guildId) {
  return apiClient.get(`/guilds/${guildId}/discord/channels`);
}

export function getGuildRoles(guildId) {
  return apiClient.get(`/guilds/${guildId}/discord/roles`);
}
