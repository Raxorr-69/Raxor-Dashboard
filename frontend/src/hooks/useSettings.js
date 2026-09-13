import { useCallback, useState } from "react";

import { getSettings, updateSettings } from "../api/settings";
import { useApi } from "./useApi";

/**
 * Loads a guild's settings and exposes a `save` function that PATCHes
 * only the changed fields and merges the (validated) result back in.
 */
export function useSettings(guildId) {
  const { data, error, loading, refetch } = useApi(
    () => getSettings(guildId),
    [guildId]
  );

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const save = useCallback(
    async (updates) => {
      setSaving(true);
      setSaveError(null);
      try {
        await updateSettings(guildId, updates);
        await refetch();
        return true;
      } catch (err) {
        setSaveError(err);
        return false;
      } finally {
        setSaving(false);
      }
    },
    [guildId, refetch]
  );

  return { settings: data, error, loading, saving, saveError, save, refetch };
}
