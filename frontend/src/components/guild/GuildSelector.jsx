import EmptyState from "../common/EmptyState";
import GuildCard from "./GuildCard";

export default function GuildSelector({ guilds }) {
  if (!guilds || guilds.length === 0) {
    return (
      <EmptyState
        title="No manageable servers found"
        description="You need Administrator or Manage Server permission in a server Raxor is in."
      />
    );
  }

  return (
    <div className="guild-grid">
      {guilds.map((guild) => (
        <GuildCard key={guild.id} guild={guild} />
      ))}
    </div>
  );
}
