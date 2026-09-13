import Input from "../common/Input";
import Select from "../common/Select";
import { getGuildChannels } from "../../api/discord";
import { useApi } from "../../hooks/useApi";
import { useGuild } from "../../hooks/useGuild";

/**
 * Real channel dropdown, backed by a live Discord API call (see
 * backend/api/routes/guilds.py's /discord/channels — requires the
 * backend's BOT_INTERNAL_API_URL / DASHBOARD_INTERNAL_KEY to be set). Falls back to a plain ID
 * input if that list comes back empty, e.g. because the token isn't
 * configured or the request failed — this stays usable either way.
 */
export default function ChannelSelector({ label, value, onChange, hint, allowBlank = true, allowAutoCreate = false, autoLabel = "Auto-create on Save" }) {
  const { guildId } = useGuild();
  const { data: channels, error, loading } = useApi(() => getGuildChannels(guildId), [guildId]);

  if (loading) {
    return <Select label={label} options={[{ value: "", label: "Loading channels…" }]} disabled value="" onChange={() => {}} />;
  }

  // Only fall back to manual entry when the live list is actually
  // unavailable (the call failed, or bot-integration isn't configured
  // so it never returned an array at all) — not just because a guild
  // genuinely has zero text-capable channels, which would otherwise
  // wrongly hide the Auto-create option too.
  if (error || !channels) {
    return (
      <Input
        label={label}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Channel ID"
        hint={hint ?? "Right-click a channel in Discord and Copy ID (Developer Mode required)."}
      />
    );
  }

  const options = [
    ...(allowAutoCreate ? [{ value: "__auto__", label: autoLabel }] : []),
    ...(allowBlank ? [{ value: "", label: "— None —" }] : []),
    ...channels
      .slice()
      .sort((a, b) => a.position - b.position)
      .map((channel) => ({ value: channel.id, label: `#${channel.name}` })),
  ];

  return (
    <Select
      label={label}
      options={options}
      value={value ?? ""}
      onChange={(event) => onChange(event.target.value || null)}
      hint={hint}
    />
  );
}
