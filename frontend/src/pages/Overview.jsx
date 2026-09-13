import ActivityChart from "../components/statistics/ActivityChart";
import Card from "../components/common/Card";
import ErrorState from "../components/common/ErrorState";
import Loader from "../components/common/Loader";
import StatCard from "../components/statistics/StatCard";
import { getGuildOverview } from "../api/guilds";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";
import { formatDuration, formatNumber } from "../lib/formatters";

export default function Overview() {
  const { guildId } = useGuild();
  const { data, loading, error, refetch } = useApi(() => getGuildOverview(guildId), [guildId]);

  if (loading) return <Loader label="Loading overview…" />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;

  const { stats, activity } = data;

  return (
    <div>
      <h1>Overview</h1>
      <p>Last {stats.period_days} days.</p>

      <div className="stat-grid">
        <StatCard label="Messages" value={formatNumber(stats.total_messages)} />
        <StatCard label="Voice time" value={formatDuration(stats.total_voice_seconds)} />
        <StatCard label="Tracked members" value={formatNumber(stats.tracked_users)} />
      </div>

      <Card title="Message activity">
        <ActivityChart series={activity.messages} formatValue={(v) => v.toLocaleString()} />
      </Card>

      <Card title="Voice activity">
        <ActivityChart series={activity.voice} color="#39ff9e" formatValue={formatDuration} />
      </Card>
    </div>
  );
}
