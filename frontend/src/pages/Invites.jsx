import Card from "../components/common/Card";
import ErrorState from "../components/common/ErrorState";
import InviteStats from "../components/invites/InviteStats";
import Loader from "../components/common/Loader";
import { getInviteLeaderboard } from "../api/invites";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";

export default function Invites() {
  const { guildId } = useGuild();
  const { data, loading, error, refetch } = useApi(
    () => getInviteLeaderboard(guildId),
    [guildId]
  );

  if (loading) return <Loader label="Loading invite stats…" />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div>
      <h1>Invites</h1>
      <p>Top inviters tracked for this server.</p>

      <Card title="Top inviters">
        <InviteStats entries={data} />
      </Card>
    </div>
  );
}
