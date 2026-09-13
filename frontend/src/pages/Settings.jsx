import { useEffect, useState } from "react";

import Button from "../components/common/Button";
import Card from "../components/common/Card";
import ChannelSelector from "../components/settings/ChannelSelector";
import RoleSelector from "../components/settings/RoleSelector";
import ErrorState from "../components/common/ErrorState";
import Input from "../components/common/Input";
import Loader from "../components/common/Loader";
import SettingCard from "../components/settings/SettingCard";
import Toast from "../components/common/Toast";
import { useGuild } from "../hooks/useGuild";
import { useSettings } from "../hooks/useSettings";

export default function Settings() {
  const { guildId } = useGuild();
  const { settings, loading, error, saving, save, refetch } = useSettings(guildId);

  const [draft, setDraft] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (settings) setDraft(settings);
  }, [settings]);

  const set = (field) => (value) => setDraft((prev) => ({ ...prev, [field]: value }));

  const handleSave = async () => {
    const ok = await save(draft);
    setToast(
      ok
        ? { message: "Settings saved.", variant: "success" }
        : { message: "Couldn't save settings.", variant: "error" }
    );
  };

  if (loading || !draft) return <Loader label="Loading settings…" />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div>
      <div className="card-header">
        <h1>Settings</h1>
        <Button onClick={handleSave} loading={saving}>
          Save changes
        </Button>
      </div>

      <Card title="Activity tracking">
        <SettingCard
          title="Message tracking"
          description="Count messages toward statistics, XP, and leaderboards."
          checked={draft.message_tracking_enabled}
          onToggle={set("message_tracking_enabled")}
        />
        <SettingCard
          title="Voice tracking"
          description="Count time spent in voice channels toward statistics and leaderboards."
          checked={draft.voice_tracking_enabled}
          onToggle={set("voice_tracking_enabled")}
        />
      </Card>

      <Card title="Leveling">
        <SettingCard
          title="Leveling"
          description="Award XP for activity and let members level up."
          checked={draft.leveling_enabled}
          onToggle={set("leveling_enabled")}
        />
        <div className="inline-form">
          <Input
            label="Min XP per message"
            type="number"
            min="1"
            value={draft.xp_min}
            onChange={(event) => set("xp_min")(Number(event.target.value))}
          />
          <Input
            label="Max XP per message"
            type="number"
            min="1"
            value={draft.xp_max}
            onChange={(event) => set("xp_max")(Number(event.target.value))}
          />
        </div>
        <SettingCard
          title="Level-up messages"
          description="Announce it when a member levels up."
          checked={draft.level_up_messages_enabled}
          onToggle={set("level_up_messages_enabled")}
        />
        <ChannelSelector
          label="Level-up channel"
          value={draft.level_up_channel_id}
          onChange={set("level_up_channel_id")}
          hint="Choose a channel, or choose Auto-create on Save. Discord is not changed until Save changes."
          allowAutoCreate
          autoLabel="Auto-create #level-up on Save"
        />
      </Card>

      <Card title="Welcome messages" description="Customize the existing welcome embed without changing its visual style. Changes apply only when you press Save changes.">
        <SettingCard
          title="Welcome system"
          description="Send the welcome embed when a human member joins."
          checked={!!draft.welcome_enabled}
          onToggle={set("welcome_enabled")}
        />
        <ChannelSelector label="Welcome channel" value={draft.welcome_channel_id} onChange={set("welcome_channel_id")} allowAutoCreate autoLabel="Auto-create #welcome on Save" />
        <label className="field-label">Welcome message</label>
        <textarea className="input" rows="4" value={draft.welcome_message || ""} onChange={(e) => set("welcome_message")(e.target.value)} placeholder="Welcome {user} to {server}! 🎉" />
        <Input label="Welcome GIF / image URL" value={draft.welcome_gif_url || ""} onChange={(e) => set("welcome_gif_url")(e.target.value || null)} placeholder="https://.../welcome.gif" hint="Optional. Must be a direct HTTP(S) media URL." />
        <div className="field-hint">Variables: {'{user}'} {'{username}'} {'{displayname}'} {'{server}'} {'{member_count}'} {'{user_id}'} {'{user_avatar}'}</div>
      </Card>

      <Card title="Leave messages" description="Use the same final embed style for member leave messages, with optional custom text and GIF.">
        <SettingCard title="Leave system" description="Send the leave embed when a human member leaves." checked={!!draft.leave_enabled} onToggle={set("leave_enabled")} />
        <ChannelSelector label="Leave channel" value={draft.leave_channel_id} onChange={set("leave_channel_id")} allowAutoCreate autoLabel="Auto-create #leave on Save" />
        <label className="field-label">Leave message</label>
        <textarea className="input" rows="4" value={draft.leave_message || ""} onChange={(e) => set("leave_message")(e.target.value)} placeholder="{username} has left {server}. 👋" />
        <Input label="Leave GIF / image URL" value={draft.leave_gif_url || ""} onChange={(e) => set("leave_gif_url")(e.target.value || null)} placeholder="https://.../leave.gif" />
      </Card>

      <Card title="Announcements">
        <ChannelSelector label="Announcement channel" value={draft.announcement_channel_id} onChange={set("announcement_channel_id")} allowAutoCreate autoLabel="Auto-create #announcements on Save" />
      </Card>

      <Card title="Level-up embed" description="Customize only the message and optional GIF; the existing Level Up! embed style remains intact.">
        <label className="field-label">Level-up message</label>
        <textarea className="input" rows="4" value={draft.level_up_message || ""} onChange={(e) => set("level_up_message")(e.target.value)} placeholder="{user} reached **Level {level}**! 🎉" />
        <Input label="Level-up GIF / image URL" value={draft.level_up_gif_url || ""} onChange={(e) => set("level_up_gif_url")(e.target.value || null)} placeholder="https://.../levelup.gif" />
        <div className="field-hint">Use {'{user}'} for the member mention and {'{level}'} for the new level.</div>
      </Card>

      <Card title="Verification" description="New members can verify with a persistent button. Nothing is changed in Discord until you press Save changes.">
        <SettingCard
          title="Member verification"
          description="Create/reuse a verification channel and Verified role, then post the Verify button."
          checked={!!draft.verification_enabled}
          onToggle={set("verification_enabled")}
        />
        <ChannelSelector
          label="Verification channel"
          value={draft.verification_channel_id}
          onChange={set("verification_channel_id")}
          allowAutoCreate
          autoLabel="Auto-create #verification on Save"
        />
        <RoleSelector
          label="Verified role"
          value={draft.verification_role_id}
          onChange={set("verification_role_id")}
          allowAutoCreate
          autoLabel="Auto-create @Verified on Save"
        />
      </Card>

      <Toast
        message={toast?.message}
        variant={toast?.variant}
        onDismiss={() => setToast(null)}
      />
    </div>
  );
}
