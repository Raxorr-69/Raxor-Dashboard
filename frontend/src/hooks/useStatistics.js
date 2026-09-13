import { useState } from "react";

import { getActivity, getChannelStats, getOverview } from "../api/statistics";
import { useApi } from "./useApi";

/**
 * Overview totals + activity trend for a guild, with a switchable
 * period ("weekly" | "monthly" | "all") for the activity chart and
 * channel breakdown.
 */
export function useStatistics(guildId) {
  const [period, setPeriod] = useState("weekly");

  const overview = useApi(() => getOverview(guildId), [guildId]);
  const activity = useApi(() => getActivity(guildId, period), [guildId, period]);
  const channels = useApi(() => getChannelStats(guildId, period), [guildId, period]);

  return {
    period,
    setPeriod,
    overview: overview.data,
    overviewLoading: overview.loading,
    activity: activity.data,
    activityLoading: activity.loading,
    channels: channels.data,
    channelsLoading: channels.loading,
    error: overview.error || activity.error || channels.error,
  };
}
