export default function Select({ label, error, hint, options = [], className = "", id, ...rest }) {
  const selectId = id || rest.name;

  return (
    <div className={`field ${className}`.trim()}>
      {label && (
        <label className="field-label" htmlFor={selectId}>
          {label}
        </label>
      )}
      <select id={selectId} className={`select ${error ? "input-error" : ""}`.trim()} {...rest}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {hint && !error && <span className="field-hint">{hint}</span>}
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}
