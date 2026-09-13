import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h1>404</h1>
        <p>This page doesn't exist.</p>
        <Link className="btn btn-secondary btn-md" to="/">
          Back home
        </Link>
      </div>
    </div>
  );
}
