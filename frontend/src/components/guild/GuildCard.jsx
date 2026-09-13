import { Link } from "react-router-dom";

const DISCORD_CLIENT_ID = window.__RAXOR_CONFIG__?.discordClientId || "";

export default function GuildCard({ guild }) {
  const content = (
    <>
      {guild.icon_url ? (
        <img className="guild-card-icon" src={guild.icon_url} alt="" />
      ) : (
        <div className="guild-card-icon guild-card-icon-fallback">{guild.name[0]}</div>
      )}
      <div className="guild-card-body">
        <span className="guild-card-name">{guild.name}</span>
        {typeof guild.member_count === "number" && (
          <span className="guild-card-members">
            {guild.member_count.toLocaleString()} members
          </span>
        )}
      </div>
      {!guild.is_bot_present && <span className="badge badge-muted">Not installed</span>}
    </>
  );

  if (!guild.is_bot_present) {
    return (
      <a
        className="guild-card guild-card-disabled"
        href={`https://discord.com/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&scope=bot&guild_id=${guild.id}`}
        target="_blank"
        rel="noreferrer"
      >
        {content}
      </a>
    );
  }

  return (
    <Link className="guild-card" to={`/dashboard/${guild.id}`}>
      {content}
    </Link>
  );
}
