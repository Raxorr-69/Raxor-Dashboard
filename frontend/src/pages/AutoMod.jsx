import { useEffect, useState } from "react";

import AutoModRule from "../components/moderation/AutoModRule";
import Button from "../components/common/Button";
import ErrorState from "../components/common/ErrorState";
import Loader from "../components/common/Loader";
import ModerationRuleCard from "../components/moderation/ModerationRuleCard";
import Toast from "../components/common/Toast";
import { getAutoModSettings, updateAutoModSettings } from "../api/automod";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";

export default function AutoMod() {
  const { guildId } = useGuild();
  const { data, loading, error, refetch } = useApi(
    () => getAutoModSettings(guildId),
    [guildId]
  );

  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (data) setDraft(data);
  }, [data]);

  const set = (field) => (value) => setDraft((prev) => ({ ...prev, [field]: value }));

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateAutoModSettings(guildId, draft);
      setDraft(updated);
      setToast({ message: "Auto-mod settings saved.", variant: "success" });
    } catch (err) {
      setToast({ message: err.message, variant: "error" });
    } finally {
      setSaving(false);
    }
  };

  if (loading || !draft) return <Loader label="Loading auto-mod settings…" />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div>
      <div className="card-header">
        <h1>Auto-Mod</h1>
        <Button onClick={handleSave} loading={saving}>
          Save changes
        </Button>
      </div>
      <p>Automatic spam, emoji-spam, and link protection — mirrors the bot's ₹spamaction / ₹emojiconfig / ₹linkconfig commands.</p>

      <ModerationRuleCard
        title="Spam protection"
        description="Warn, delete, or time out members who post too many messages too quickly."
        enabled={draft.spam_enabled}
        onToggle={set("spam_enabled")}
      />

      <ModerationRuleCard
        title="Link protection"
        description="Warn, delete, or time out members who post links outside whitelisted channels."
        enabled={draft.link_protection_enabled}
        onToggle={set("link_protection_enabled")}
      />

      <AutoModRule
        title="Spam"
        limitLabel="Message limit"
        limit={draft.spam_message_limit}
        onLimitChange={set("spam_message_limit")}
        windowLabel="Window (seconds)"
        windowValue={draft.spam_message_window}
        onWindowChange={set("spam_message_window")}
        action={draft.spam_action}
        onActionChange={set("spam_action")}
        timeoutSeconds={draft.spam_timeout_seconds}
        onTimeoutChange={set("spam_timeout_seconds")}
      />

      <AutoModRule
        title="Emoji spam"
        limitLabel="Emoji limit"
        limit={draft.emoji_spam_limit}
        onLimitChange={set("emoji_spam_limit")}
        action={draft.emoji_spam_action}
        onActionChange={set("emoji_spam_action")}
        timeoutSeconds={draft.emoji_spam_timeout_seconds}
        onTimeoutChange={set("emoji_spam_timeout_seconds")}
      />

      <AutoModRule
        title="Link protection"
        action={draft.link_action}
        onActionChange={set("link_action")}
        timeoutSeconds={draft.link_timeout_seconds}
        onTimeoutChange={set("link_timeout_seconds")}
      />

      <Toast
        message={toast?.message}
        variant={toast?.variant}
        onDismiss={() => setToast(null)}
      />
    </div>
  );
}
