import { apiClient } from "./client";

export function listWarnings(guildId, userId) {
  return apiClient.get(`/guilds/${guildId}/warnings`, userId ? { user_id: userId } : undefined);
}

export function deleteWarning(guildId, warningId) {
  return apiClient.delete(`/guilds/${guildId}/warnings/${warningId}`);
}

export function clearWarnings(guildId, userId) {
  return apiClient.delete(`/guilds/${guildId}/users/${userId}/warnings`);
}

export function listChannelRules(guildId) {
  return apiClient.get(`/guilds/${guildId}/channel-rules`);
}

export function setChannelRule(guildId, channelId, rule, enabled) {
  return apiClient.put(`/guilds/${guildId}/channel-rules/${channelId}`, undefined, {
    rule,
    enabled,
  });
}

export function listWhitelist(guildId, restrictionType) {
  return apiClient.get(
    `/guilds/${guildId}/whitelist`,
    restrictionType ? { restriction_type: restrictionType } : undefined
  );
}

export function addWhitelistEntry(guildId, targetId, restrictionType) {
  return apiClient.post(`/guilds/${guildId}/whitelist`, {
    target_id: targetId,
    restriction_type: restrictionType,
  });
}

export function removeWhitelistEntry(guildId, targetId, restrictionType) {
  return apiClient.delete(`/guilds/${guildId}/whitelist/${targetId}`, {
    restriction_type: restrictionType,
  });
}
