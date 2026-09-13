export default function ErrorState({ error, onRetry }) {
  const message =
    error?.message || "Something went wrong while loading this page.";

  return (
    <div className="error-state">
      <h4>Couldn't load this</h4>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn btn-secondary btn-sm" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
