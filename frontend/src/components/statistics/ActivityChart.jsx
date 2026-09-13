import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/**
 * `series` is an array of { date, value } points (see
 * services/statistics_service.py -> get_activity). `formatValue` lets the
 * caller render voice-seconds as "1h 23m" etc. in the tooltip.
 */
export default function ActivityChart({ series = [], color = "#5865f2", formatValue }) {
  if (series.length === 0) {
    return <div className="chart-empty">No activity recorded for this period yet.</div>;
  }

  const format = formatValue || ((value) => value.toLocaleString());

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={series} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
        <YAxis stroke="var(--text-muted)" fontSize={12} tickFormatter={format} width={56} />
        <Tooltip
          formatter={(value) => format(value)}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
          }}
        />
        <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
