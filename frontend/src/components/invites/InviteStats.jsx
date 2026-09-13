import EmptyState from "../common/EmptyState";

export default function InviteStats({ entries = [] }) {
  if (entries.length === 0) {
    return (
      <EmptyState
        title="No tracked invites yet"
        description="Once members start joining through invite links, the top inviters show up here."
      />
    );
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Rank</th>
          <th>Inviter</th>
          <th>Members invited</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.inviter_id}>
            <td>
              <span className={`rank-badge rank-${entry.rank <= 3 ? entry.rank : "other"}`}>
                #{entry.rank}
              </span>
            </td>
            <td>
              <code>{entry.inviter_id}</code>
            </td>
            <td>{entry.invite_count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
