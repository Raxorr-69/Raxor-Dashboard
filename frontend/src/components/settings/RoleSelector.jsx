import Input from "../common/Input";
import Select from "../common/Select";
import { getGuildRoles } from "../../api/discord";
import { useApi } from "../../hooks/useApi";
import { useGuild } from "../../hooks/useGuild";

/**
 * Real role dropdown, backed by a live Discord API call (see
 * backend/api/routes/guilds.py's /discord/roles — requires the
 * backend's BOT_INTERNAL_API_URL / DASHBOARD_INTERNAL_KEY to be set). Falls back to a plain ID
 * input if that list comes back empty, e.g. because the token isn't
 * configured or the request failed — this stays usable either way.
 */
export default function RoleSelector({ label, value, onChange, hint, allowBlank = false, allowAutoCreate = false, autoLabel = "Auto-create on Save" }) {
  const { guildId } = useGuild();
  const { data: roles, error, loading } = useApi(() => getGuildRoles(guildId), [guildId]);

  if (loading) {
    return <Select label={label} options={[{ value: "", label: "Loading roles…" }]} disabled value="" onChange={() => {}} />;
  }

  // Same reasoning as ChannelSelector: only fall back to manual entry on
  // a real failure/not-configured integration, not on a genuinely empty
  // (but successfully fetched) role list.
  if (error || !roles) {
    return (
      <Input
        label={label}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Role ID"
        hint={hint ?? (allowAutoCreate ? "Leave Auto-create on Save selected, or enter a role ID manually." : "Right-click a role in Server Settings and Copy ID (Developer Mode required).")}
      />
    );
  }

  const options = [
    ...(allowAutoCreate ? [{ value: "__auto__", label: autoLabel }] : []),
    ...(allowBlank ? [{ value: "", label: "— None —" }] : []),
    ...roles
      .slice()
      .sort((a, b) => b.position - a.position)
      .map((role) => ({ value: role.id, label: `@${role.name}` })),
  ];

  return (
    <Select
      label={label}
      options={options}
      value={value ?? ""}
      onChange={(event) => onChange(event.target.value)}
      hint={hint}
    />
  );
}
