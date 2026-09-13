import ActivityChart from "../components/statistics/ActivityChart";
import Card from "../components/common/Card";
import ChannelStatsTable from "../components/statistics/ChannelStatsTable";
import ErrorState from "../components/common/ErrorState";
import Loader from "../components/common/Loader";
import Select from "../components/common/Select";
import StatCard from "../components/statistics/StatCard";
import { RANK_PERIODS } from "../lib/constants";
import { getChannelStats } from "../api/statistics";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";
import { useStatistics } from "../hooks/useStatistics";
import { formatDuration, formatNumber } from "../lib/formatters";

export default function Statistics() {
  const { guildId } = useGuild();
  const {
    period,
    setPeriod,
    overview,
    overviewLoading,
    activity,
    activityLoading,
    error,
  } = useStatistics(guildId);

  const channels = useApi(() => getChannelStats(guildId, period), [guildId, period]);

  if (error) return <ErrorState error={error} />;

  return (
    <div>
      <div className="card-header">
        <h1>Statistics</h1>
        <Select
          options={RANK_PERIODS}
          value={period}
          onChange={(event) => setPeriod(event.target.value)}
        />
      </div>

      {overviewLoading || !overview ? (
        <Loader label="Loading stats…" />
      ) : (
        <div className="stat-grid">
          <StatCard label="Messages" value={formatNumber(overview.total_messages)} />
          <StatCard label="Voice time" value={formatDuration(overview.total_voice_seconds)} />
          <StatCard label="Tracked members" value={formatNumber(overview.tracked_users)} />
        </div>
      )}

      <Card title="Message activity">
        {activityLoading || !activity ? (
          <Loader label="Loading chart…" />
        ) : (
          <ActivityChart series={activity.messages} formatValue={(v) => v.toLocaleString()} />
        )}
      </Card>

      <Card title="Voice activity">
        {activityLoading || !activity ? (
          <Loader label="Loading chart…" />
        ) : (
          <ActivityChart series={activity.voice} color="#39ff9e" formatValue={formatDuration} />
        )}
      </Card>

      <Card title="Top channels — messages">
        {channels.loading ? (
          <Loader label="Loading channels…" />
        ) : (
          <ChannelStatsTable rows={channels.data?.messages} />
        )}
      </Card>

      <Card title="Top channels — voice">
        {channels.loading ? (
          <Loader label="Loading channels…" />
        ) : (
          <ChannelStatsTable rows={channels.data?.voice} formatValue={formatDuration} />
        )}
      </Card>
    </div>
  );
}
