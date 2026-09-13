import { useEffect, useState } from "react";

import Button from "../components/common/Button";
import Card from "../components/common/Card";
import ErrorState from "../components/common/ErrorState";
import LevelRewardTable from "../components/leveling/LevelRewardTable";
import Loader from "../components/common/Loader";
import RoleSelector from "../components/settings/RoleSelector";
import Select from "../components/common/Select";
import Toast from "../components/common/Toast";
import { LEADERBOARD_TYPES } from "../lib/constants";
import {
  addLevelReward,
  getLeaderboardRewards,
  listLevelRewards,
  removeLeaderboardReward,
  removeLevelReward,
  setLeaderboardReward,
} from "../api/leveling";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";

const LEADERBOARD_TYPE_OPTIONS = LEADERBOARD_TYPES.map((type) => ({
  value: type,
  label: type[0].toUpperCase() + type.slice(1),
}));

function WeeklyLeaderboardRewards({ rewards = {}, onChange }) {
  const [type, setType] = useState(LEADERBOARD_TYPES[0]);
  const [roleId, setRoleId] = useState("");

  const handleSet = (event) => {
    event.preventDefault();
    // Blank means create/reuse the managed role on Save.
    onChange({ ...rewards, [type]: roleId.trim() });
    setRoleId("");
  };

  return (
    <div>
      <form className="inline-form" onSubmit={handleSet}>
        <Select
          label="Leaderboard"
          options={LEADERBOARD_TYPE_OPTIONS}
          value={type}
          onChange={(event) => setType(event.target.value)}
        />
        <RoleSelector label="Role" value={roleId} onChange={setRoleId} allowAutoCreate autoLabel="Auto-create role on Save" />
        <Button type="submit">Add / change</Button>
      </form>

      <table className="table">
        <thead><tr><th>Leaderboard</th><th>Role</th><th /></tr></thead>
        <tbody>
          {LEADERBOARD_TYPES.map((leaderboardType) => (
            <tr key={leaderboardType}>
              <td>{leaderboardType[0].toUpperCase() + leaderboardType.slice(1)}</td>
              <td>{rewards[leaderboardType] ? <code>{rewards[leaderboardType]}</code> : "—"}</td>
              <td>
                {rewards[leaderboardType] && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => {
                      const next = { ...rewards };
                      delete next[leaderboardType];
                      onChange(next);
                    }}
                  >
                    Remove
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Leveling() {
  const { guildId } = useGuild();
  const levelApi = useApi(() => listLevelRewards(guildId), [guildId]);
  const leaderboardApi = useApi(() => getLeaderboardRewards(guildId), [guildId]);
  const [draftRewards, setDraftRewards] = useState([]);
  const [draftLeaderboard, setDraftLeaderboard] = useState({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (levelApi.data) setDraftRewards(levelApi.data);
  }, [levelApi.data]);

  useEffect(() => {
    if (leaderboardApi.data) setDraftLeaderboard(leaderboardApi.data);
  }, [leaderboardApi.data]);

  const addReward = (level, roleId) => {
    setDraftRewards((prev) => {
      if (prev.some((r) => Number(r.level) === Number(level) && String(r.role_id) === String(roleId))) return prev;
      return [...prev, { level, role_id: roleId }];
    });
    return true;
  };

  const removeReward = (level, roleId) => {
    setDraftRewards((prev) =>
      prev.filter((r) => !(Number(r.level) === Number(level) && String(r.role_id) === String(roleId)))
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const original = levelApi.data || [];
      const desiredKeys = new Set(draftRewards.map((r) => `${r.level}-${r.role_id}`));
      for (const r of original) {
        if (!desiredKeys.has(`${r.level}-${r.role_id}`)) {
          await removeLevelReward(guildId, r.level, r.role_id);
        }
      }
      const originalKeys = new Set(original.map((r) => `${r.level}-${r.role_id}`));
      for (const r of draftRewards) {
        if (!originalKeys.has(`${r.level}-${r.role_id}`)) {
          await addLevelReward(guildId, r.level, r.role_id);
        }
      }

      const originalLeaderboard = leaderboardApi.data || {};
      for (const type of LEADERBOARD_TYPES) {
        const oldRole = originalLeaderboard[type];
        const newRole = draftLeaderboard[type];
        if (oldRole && !newRole) await removeLeaderboardReward(guildId, type);
        else if (newRole && newRole !== oldRole) await setLeaderboardReward(guildId, type, newRole);
      }

      await Promise.all([levelApi.refetch(), leaderboardApi.refetch()]);
      setToast({ message: "Leveling changes saved.", variant: "success" });
    } catch (err) {
      setToast({ message: err.message || "Couldn't save leveling changes.", variant: "error" });
    } finally {
      setSaving(false);
    }
  };

  if (levelApi.loading || leaderboardApi.loading) return <Loader label="Loading leveling settings…" />;
  if (levelApi.error) return <ErrorState error={levelApi.error} onRetry={levelApi.refetch} />;
  if (leaderboardApi.error) return <ErrorState error={leaderboardApi.error} onRetry={leaderboardApi.refetch} />;

  return (
    <div>
      <div className="card-header">
        <div>
          <h1>Leveling</h1>
          <p>Changes stay pending until you press Save changes.</p>
        </div>
        <Button onClick={handleSave} loading={saving}>Save changes</Button>
      </div>

      <Card title="Level rewards" description="Members keep every role they've earned as they level up.">
        <LevelRewardTable rewards={draftRewards} onAdd={addReward} onRemove={removeReward} saving={false} />
      </Card>

      <Card title="Weekly leaderboard rewards" description="Given to whoever's #1 on the weekly messages/voice leaderboard when it resets.">
        <WeeklyLeaderboardRewards rewards={draftLeaderboard} onChange={setDraftLeaderboard} />
      </Card>

      <Toast message={toast?.message} variant={toast?.variant} onDismiss={() => setToast(null)} />
    </div>
  );
}
