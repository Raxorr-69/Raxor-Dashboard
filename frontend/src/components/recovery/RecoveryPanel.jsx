import Button from "../common/Button";
import EmptyState from "../common/EmptyState";
import { formatRelativeTime } from "../../lib/formatters";

export default function RecoveryPanel({ channels = [], onRescan, rescanningId }) {
  if (channels.length === 0) {
    return (
      <EmptyState
        title="No recovery activity recorded"
        description="The bot records a scan timestamp per channel after recovering messages it may have missed while offline."
      />
    );
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Channel</th>
          <th>Last scanned</th>
          <th>Status</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {channels.map((channel) => {
          const pending = channel.rescan_pending || rescanningId === channel.channel_id;
          return (
            <tr key={channel.channel_id}>
              <td>#{channel.channel_id}</td>
              <td>{formatRelativeTime(channel.last_scanned_at)}</td>
              <td>{pending ? "Rescanning…" : "Up to date"}</td>
              <td>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={pending}
                  onClick={() => onRescan?.(channel.channel_id)}
                >
                  Rescan
                </Button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
