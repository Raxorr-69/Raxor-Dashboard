import { useState } from "react";

import Card from "../components/common/Card";
import ErrorState from "../components/common/ErrorState";
import Loader from "../components/common/Loader";
import RecoveryPanel from "../components/recovery/RecoveryPanel";
import { listRecoveryState, triggerRescan } from "../api/recovery";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";

export default function Recovery() {
  const { guildId } = useGuild();
  const { data, loading, error, refetch } = useApi(
    () => listRecoveryState(guildId),
    [guildId]
  );
  const [rescanningId, setRescanningId] = useState(null);

  const handleRescan = async (channelId) => {
    setRescanningId(channelId);
    try {
      await triggerRescan(guildId, channelId);
      await refetch();
    } finally {
      setRescanningId(null);
    }
  };

  if (loading) return <Loader label="Loading recovery state…" />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div>
      <h1>Recovery</h1>
      <p>
        Per-channel status of the bot's missed-message recovery scans. Queuing
        a rescan asks Raxor itself to re-check a channel's history — it's
        picked up within about 20 seconds, not run by the dashboard directly.
      </p>

      <Card title="Channels">
        <RecoveryPanel
          channels={data}
          onRescan={handleRescan}
          rescanningId={rescanningId}
        />
      </Card>
    </div>
  );
}
