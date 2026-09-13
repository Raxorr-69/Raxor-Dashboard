import { getLoginUrl } from "../api/auth";

export default function Login() {
  return (
    <div className="auth-screen">
      <div className="auth-card hud-frame">
        <h1>Raxor Dashboard</h1>
        <p>Sign in with Discord to manage your servers.</p>
        <a className="btn btn-primary btn-discord" href={getLoginUrl()}>
          Continue with Discord
        </a>
      </div>
    </div>
  );
}
