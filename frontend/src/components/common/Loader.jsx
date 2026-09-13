export default function Loader({ label = "Loading…", fullscreen = false }) {
  return (
    <div className={fullscreen ? "loader-fullscreen" : "loader"}>
      <span className="spinner" aria-hidden="true" />
      <span className="loader-label">{label}</span>
    </div>
  );
}
