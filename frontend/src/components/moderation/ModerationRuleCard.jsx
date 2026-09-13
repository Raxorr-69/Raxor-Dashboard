import Card from "../common/Card";
import Toggle from "../common/Toggle";

/**
 * A single on/off automod switch with a short description — used for the
 * top-level "Spam protection" / "Link protection" toggles.
 */
export default function ModerationRuleCard({ title, description, enabled, onToggle, disabled }) {
  return (
    <Card>
      <div className="rule-card">
        <div>
          <h4>{title}</h4>
          <p>{description}</p>
        </div>
        <Toggle checked={enabled} onChange={onToggle} disabled={disabled} />
      </div>
    </Card>
  );
}
