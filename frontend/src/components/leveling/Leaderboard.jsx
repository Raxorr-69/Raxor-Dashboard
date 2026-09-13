import EmptyState from "../common/EmptyState";

export default function Leaderboard({ entries = [], formatValue }) {
  if (entries.length === 0) {
    return (
      <EmptyState
        title="No activity yet"
        description="No one has ranked for this category and period yet."
      />
    );
  }

  const format = formatValue || ((value) => value.toLocaleString());

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Rank</th>
          <th>Member</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.user_id}>
            <td>
              <span className={`rank-badge rank-${entry.rank <= 3 ? entry.rank : "other"}`}>
                #{entry.rank}
              </span>
            </td>
            <td>
              <code>{entry.user_id}</code>
            </td>
            <td>{format(entry.value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
