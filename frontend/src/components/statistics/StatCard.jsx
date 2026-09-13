export default function StatCard({ label, value, hint }) {
  return (
    <div className="stat-card hud-frame">
      <span className="stat-card-label">{label}</span>
      <span className="stat-card-value">{value}</span>
      {hint && <span className="stat-card-hint">{hint}</span>}
    </div>
  );
}
