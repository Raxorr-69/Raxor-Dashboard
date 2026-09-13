export default function EmptyState({ title = "Nothing here yet", description, action }) {
  return (
    <div className="empty-state">
      <h4>{title}</h4>
      {description && <p>{description}</p>}
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  );
}
