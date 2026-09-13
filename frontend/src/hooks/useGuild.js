import { useParams } from "react-router-dom";

import { findGuild, isBotInstalled } from "../lib/permissions";
import { useAuth } from "./useAuth";

/**
 * Resolve the `:guildId` route param against the logged-in user's
 * manageable guild list from their session.
 */
export function useGuild() {
  const { guildId } = useParams();
  const { guilds } = useAuth();

  const guild = findGuild(guilds, guildId);

  return {
    guildId,
    guild,
    isBotPresent: isBotInstalled(guilds, guildId),
  };
}
