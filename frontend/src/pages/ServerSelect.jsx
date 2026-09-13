import GuildSelector from "../components/guild/GuildSelector";
import { useAuth } from "../hooks/useAuth";

export default function ServerSelect() {
  const { guilds } = useAuth();

  return (
    <div className="server-select">
      <h1>Choose a server</h1>
      <p>Pick a server to manage. Servers without the bot installed link to an invite instead.</p>
      <GuildSelector guilds={guilds} />
    </div>
  );
}
