import { useAuth } from "../../hooks/useAuth";
import { discordAvatarFallback } from "../../lib/formatters";

export default function Topbar({ guild }) {
  const { user, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="topbar-guild">
        {guild?.icon_url ? (
          <img className="topbar-guild-icon" src={guild.icon_url} alt="" />
        ) : (
          <div className="topbar-guild-icon topbar-guild-icon-fallback">
            {guild?.name?.[0] ?? "?"}
          </div>
        )}
        <span className="topbar-guild-name">{guild?.name ?? "Loading…"}</span>
      </div>

      <div className="topbar-user">
        {user && (
          <img
            className="topbar-avatar"
            src={user.avatarUrl || discordAvatarFallback(user.id)}
            alt=""
          />
        )}
        <span className="topbar-username">{user?.username}</span>
        {user?.isDeveloper && <span className="badge badge-developer">Developer</span>}
        <button type="button" className="btn btn-ghost btn-sm" onClick={logout}>
          Log out
        </button>
      </div>
    </header>
  );
}
