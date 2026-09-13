import EmptyState from "../common/EmptyState";

export default function ChannelStatsTable({ rows = [], formatValue }) {
  if (rows.length === 0) {
    return <EmptyState title="No channel activity" description="Nothing tracked for this period yet." />;
  }

  const format = formatValue || ((value) => value.toLocaleString());

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Channel</th>
          <th>Activity</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.channel_id}>
            <td>#{row.channel_id}</td>
            <td>{format(row.value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
