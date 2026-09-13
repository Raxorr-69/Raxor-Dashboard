import { Link } from "react-router-dom";

import EmptyState from "../common/EmptyState";
import Select from "../common/Select";
import { formatDuration, formatNumber } from "../../lib/formatters";

const SORT_OPTIONS = [
  { value: "xp", label: "XP" },
  { value: "level", label: "Level" },
  { value: "messages", label: "Messages" },
  { value: "voice", label: "Voice time" },
  { value: "warnings", label: "Warnings" },
];

export default function UserTable({ guildId, users = [], sort, onSortChange }) {
  return (
    <div>
      <div className="inline-form">
        <Select
          label="Sort by"
          options={SORT_OPTIONS}
          value={sort}
          onChange={(event) => onSortChange(event.target.value)}
        />
      </div>

      {users.length === 0 ? (
        <EmptyState title="No tracked members" description="No activity recorded yet." />
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Level</th>
              <th>XP</th>
              <th>Messages</th>
              <th>Voice time</th>
              <th>Warnings</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.user_id}>
                <td>
                  <Link to={`/dashboard/${guildId}/users/${user.user_id}`}>
                    <code>{user.user_id}</code>
                  </Link>
                </td>
                <td>{user.level}</td>
                <td>{formatNumber(user.xp)}</td>
                <td>{formatNumber(user.message_count)}</td>
                <td>{formatDuration(user.voice_seconds)}</td>
                <td>{user.warnings}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
