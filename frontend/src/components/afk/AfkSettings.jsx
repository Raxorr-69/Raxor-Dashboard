import Button from "../common/Button";
import EmptyState from "../common/EmptyState";
import { formatRelativeTime } from "../../lib/formatters";

export default function AfkSettings({ users = [], onClear, clearingId }) {
  if (users.length === 0) {
    return (
      <EmptyState
        title="No one is AFK"
        description="Members who set an AFK status will show up here until they return."
      />
    );
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Member</th>
          <th>Reason</th>
          <th>Since</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {users.map((user) => (
          <tr key={user.user_id}>
            <td>
              <code>{user.user_id}</code>
            </td>
            <td>{user.reason || "—"}</td>
            <td>{formatRelativeTime(user.started_at)}</td>
            <td>
              <Button
                variant="secondary"
                size="sm"
                loading={clearingId === user.user_id}
                onClick={() => onClear(user.user_id)}
              >
                Clear
              </Button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
