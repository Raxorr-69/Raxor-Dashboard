export default function Toggle({ checked, onChange, label, disabled = false }) {
  return (
    <label className={`toggle ${disabled ? "toggle-disabled" : ""}`.trim()}>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange?.(event.target.checked)}
      />
      <span className="toggle-track">
        <span className="toggle-thumb" />
      </span>
      {label && <span className="toggle-label">{label}</span>}
    </label>
  );
}
