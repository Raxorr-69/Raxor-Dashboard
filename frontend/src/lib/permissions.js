/**
 * The backend already filters the guild list in the session token down
 * to servers the user is actually allowed to manage (owner, or
 * Administrator / Manage Server permission) — see api/dependencies.py.
 * These helpers just read that already-trusted data on the client.
 */

export function findGuild(guilds, guildId) {
  return guilds?.find((guild) => guild.id === guildId) ?? null;
}

export function canManageGuild(guilds, guildId) {
  return findGuild(guilds, guildId) !== null;
}

export function isBotInstalled(guilds, guildId) {
  return findGuild(guilds, guildId)?.is_bot_present ?? false;
}
