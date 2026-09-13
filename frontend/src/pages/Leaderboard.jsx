import { useState } from "react";

import Card from "../components/common/Card";
import ErrorState from "../components/common/ErrorState";
import Leaderboard from "../components/leveling/Leaderboard";
import Loader from "../components/common/Loader";
import Select from "../components/common/Select";
import { LEADERBOARD_TYPES, RANK_PERIODS } from "../lib/constants";
import { getLeaderboard } from "../api/leaderboard";
import { formatDuration } from "../lib/formatters";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";

// The dashboard's /leaderboard endpoint only ranks "messages" and
// "voice" (see services/statistics_service.py -> get_leaderboard);
// RANK_CATEGORIES' extra values are for the bot's own commands.
const CATEGORY_OPTIONS = LEADERBOARD_TYPES.map((category) => ({
  value: category,
  label: category[0].toUpperCase() + category.slice(1),
}));

export default function LeaderboardPage() {
  const { guildId } = useGuild();
  const [category, setCategory] = useState("messages");
  const [period, setPeriod] = useState("weekly");

  const { data, loading, error, refetch } = useApi(
    () => getLeaderboard(guildId, { category, period }),
    [guildId, category, period]
  );

  const formatValue = category === "voice" ? formatDuration : undefined;

  return (
    <div>
      <div className="card-header">
        <h1>Leaderboard</h1>
        <div className="inline-form">
          <Select
            label="Category"
            options={CATEGORY_OPTIONS}
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          />
          <Select
            label="Period"
            options={RANK_PERIODS}
            value={period}
            onChange={(event) => setPeriod(event.target.value)}
          />
        </div>
      </div>

      <Card>
        {error ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : loading ? (
          <Loader label="Loading leaderboard…" />
        ) : (
          <Leaderboard entries={data} formatValue={formatValue} />
        )}
      </Card>
    </div>
  );
}
