import StatCard from "../statistics/StatCard";
import { formatDuration, formatNumber } from "../../lib/formatters";

export default function UserProfile({ user }) {
  if (!user) return null;

  return (
    <div>
      <h3>
        <code>{user.user_id}</code>
      </h3>
      <div className="stat-grid">
        <StatCard label="Level" value={user.level} />
        <StatCard label="XP" value={formatNumber(user.xp)} />
        <StatCard label="Messages" value={formatNumber(user.message_count)} />
        <StatCard label="Voice time" value={formatDuration(user.voice_seconds)} />
        <StatCard label="Warnings" value={user.warnings} />
      </div>
    </div>
  );
}
