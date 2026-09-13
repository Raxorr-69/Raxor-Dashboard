export default function Input({ label, error, hint, className = "", id, ...rest }) {
  const inputId = id || rest.name;

  return (
    <div className={`field ${className}`.trim()}>
      {label && (
        <label className="field-label" htmlFor={inputId}>
          {label}
        </label>
      )}
      <input id={inputId} className={`input ${error ? "input-error" : ""}`.trim()} {...rest} />
      {hint && !error && <span className="field-hint">{hint}</span>}
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}
