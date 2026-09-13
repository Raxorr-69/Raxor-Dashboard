import { MODERATION_ACTIONS } from "../../lib/constants";
import Input from "../common/Input";
import Select from "../common/Select";

const ACTION_OPTIONS = MODERATION_ACTIONS.map((action) => ({
  value: action,
  label: action[0].toUpperCase() + action.slice(1),
}));

/**
 * The limit/action/timeout trio shared by spam, emoji-spam, and link
 * protection — mirrors the bot's ₹spamaction / ₹emojiconfig / ₹linkconfig
 * commands.
 */
export default function AutoModRule({
  title,
  limitLabel,
  limit,
  onLimitChange,
  windowLabel,
  windowValue,
  onWindowChange,
  action,
  onActionChange,
  timeoutSeconds,
  onTimeoutChange,
}) {
  return (
    <div className="automod-rule">
      <h4>{title}</h4>
      <div className="automod-rule-grid">
        {limitLabel && (
          <Input
            label={limitLabel}
            type="number"
            min="1"
            value={limit}
            onChange={(event) => onLimitChange(Number(event.target.value))}
          />
        )}
        {windowLabel && (
          <Input
            label={windowLabel}
            type="number"
            min="1"
            value={windowValue}
            onChange={(event) => onWindowChange(Number(event.target.value))}
          />
        )}
        <Select
          label="Action"
          options={ACTION_OPTIONS}
          value={action}
          onChange={(event) => onActionChange(event.target.value)}
        />
        {action === "timeout" && (
          <Input
            label="Timeout (seconds)"
            type="number"
            min="1"
            value={timeoutSeconds}
            onChange={(event) => onTimeoutChange(Number(event.target.value))}
          />
        )}
      </div>
    </div>
  );
}
