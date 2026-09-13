import Card from "../common/Card";
import Toggle from "../common/Toggle";

/**
 * A single setting row: a label/description on the left, an arbitrary
 * control on the right. When `checked` is provided it renders as a
 * toggle; otherwise pass `children` for a custom control (an input,
 * a ChannelSelector, etc).
 */
export default function SettingCard({ title, description, checked, onToggle, disabled, children }) {
  return (
    <Card>
      <div className="rule-card">
        <div>
          <h4>{title}</h4>
          {description && <p>{description}</p>}
        </div>
        {children ?? <Toggle checked={checked} onChange={onToggle} disabled={disabled} />}
      </div>
    </Card>
  );
}
