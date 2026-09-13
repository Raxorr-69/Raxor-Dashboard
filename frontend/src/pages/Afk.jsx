import { useState } from "react";

import AfkSettings from "../components/afk/AfkSettings";
import Card from "../components/common/Card";
import ErrorState from "../components/common/ErrorState";
import Loader from "../components/common/Loader";
import { clearAfk, listAfkUsers } from "../api/afk";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";

export default function Afk() {
  const { guildId } = useGuild();
  const { data, loading, error, refetch } = useApi(() => listAfkUsers(guildId), [guildId]);
  const [clearingId, setClearingId] = useState(null);

  const handleClear = async (userId) => {
    setClearingId(userId);
    try {
      await clearAfk(guildId, userId);
      await refetch();
    } finally {
      setClearingId(null);
    }
  };

  if (loading) return <Loader label="Loading AFK members…" />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div>
      <h1>AFK</h1>
      <p>Members currently marked AFK in this server.</p>

      <Card>
        <AfkSettings users={data} onClear={handleClear} clearingId={clearingId} />
      </Card>
    </div>
  );
}
