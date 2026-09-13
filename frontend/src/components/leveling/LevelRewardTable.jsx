import { useState } from "react";

import Button from "../common/Button";
import EmptyState from "../common/EmptyState";
import Input from "../common/Input";
import RoleSelector from "../settings/RoleSelector";

export default function LevelRewardTable({ rewards = [], onAdd, onRemove, saving }) {
  const [level, setLevel] = useState("");
  const [roleId, setRoleId] = useState("");

  const handleAdd = async (event) => {
    event.preventDefault();
    if (!level) return;

    const added = await onAdd(Number(level), roleId.trim());
    if (added) {
      setLevel("");
      setRoleId("");
    }
  };

  return (
    <div>
      <form className="inline-form" onSubmit={handleAdd}>
        <Input
          label="Level"
          type="number"
          min="1"
          value={level}
          onChange={(event) => setLevel(event.target.value)}
          placeholder="5"
        />
        <RoleSelector label="Role" value={roleId} onChange={setRoleId} allowAutoCreate autoLabel="Auto-create role on Save" />
        <Button type="submit" loading={saving}>
          Add reward
        </Button>
      </form>

      {rewards.length === 0 ? (
        <EmptyState
          title="No level rewards configured"
          description="Members won't receive a role automatically for leveling up until you add one."
        />
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Level</th>
              <th>Role</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rewards.map((reward) => (
              <tr key={`${reward.level}-${reward.role_id}`}>
                <td>{reward.level}</td>
                <td>
                  <code>{reward.role_id}</code>
                </td>
                <td>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => onRemove(reward.level, reward.role_id)}
                  >
                    Remove
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
