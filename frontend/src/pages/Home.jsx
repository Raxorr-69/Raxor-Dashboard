import { Navigate } from "react-router-dom";

import Button from "../components/common/Button";
import { getLoginUrl } from "../api/auth";
import { useAuth } from "../hooks/useAuth";

const FEATURES = [
  { title: "Moderation", body: "Review warnings, manage channel rules, and clear restrictions without touching Discord." },
  { title: "Auto-Mod", body: "Tune spam, emoji-spam, and link-protection thresholds and actions in real time." },
  { title: "Leveling", body: "Configure XP rewards and manage level-up and weekly leaderboard roles." },
  { title: "Statistics", body: "Track message and voice activity across your server and its channels." },
];

export default function Home() {
  const { isAuthenticated, loading } = useAuth();

  if (!loading && isAuthenticated) {
    return <Navigate to="/servers" replace />;
  }

  return (
    <div className="home-hero">
      <div className="home-hero-content hud-frame">
        <h1>Run your server from the command line you didn't know you had.</h1>
        <p>
          Raxor's dashboard gives server admins live control over moderation,
          auto-mod, leveling, and activity — everything the bot tracks, in
          one console.
        </p>
        <Button as="a" href={getLoginUrl()} size="md">
          Continue with Discord
        </Button>
      </div>

      <div className="home-feature-grid">
        {FEATURES.map((feature) => (
          <div key={feature.title} className="home-feature card">
            <h4>{feature.title}</h4>
            <p>{feature.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
