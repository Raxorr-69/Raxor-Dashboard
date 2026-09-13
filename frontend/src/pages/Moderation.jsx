import { useEffect, useState } from "react";

import Button from "../components/common/Button";
import Card from "../components/common/Card";
import ChannelSelector from "../components/settings/ChannelSelector";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import Input from "../components/common/Input";
import Loader from "../components/common/Loader";
import Select from "../components/common/Select";
import Toast from "../components/common/Toast";
import Toggle from "../components/common/Toggle";
import { RESTRICTION_TYPES } from "../lib/constants";
import {
  addWhitelistEntry,
  clearWarnings,
  deleteWarning,
  listChannelRules,
  listWarnings,
  listWhitelist,
  removeWhitelistEntry,
  setChannelRule,
} from "../api/moderation";
import { formatDate } from "../lib/formatters";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";

const RESTRICTION_OPTIONS = RESTRICTION_TYPES.map((type) => ({
  value: type,
  label: type.split("_").map((word) => word[0].toUpperCase() + word.slice(1)).join(" "),
}));

function WarningsSection({ guildId }) {
  const { data, loading, error, refetch } = useApi(() => listWarnings(guildId), [guildId]);
  const [clearUserId, setClearUserId] = useState("");
  const [clearing, setClearing] = useState(false);

  const handleDelete = async (warningId) => { await deleteWarning(guildId, warningId); await refetch(); };
  const handleClearUser = async (event) => {
    event.preventDefault();
    if (!clearUserId) return;
    setClearing(true);
    try { await clearWarnings(guildId, clearUserId.trim()); setClearUserId(""); await refetch(); }
    finally { setClearing(false); }
  };

  return (
    <Card title="Warnings" description="Warnings are actions and are applied immediately.">
      <form className="inline-form" onSubmit={handleClearUser}>
        <Input label="Clear all warnings for user ID" value={clearUserId} onChange={(e) => setClearUserId(e.target.value)} placeholder="123456789012345678" />
        <Button type="submit" variant="danger" loading={clearing}>Clear all</Button>
      </form>
      {error ? <ErrorState error={error} onRetry={refetch} /> : loading ? <Loader label="Loading warnings…" /> :
        data.length === 0 ? <EmptyState title="No warnings" description="No members have been warned yet." /> :
        <table className="table"><thead><tr><th>Member</th><th>Moderator</th><th>Reason</th><th>Date</th><th /></tr></thead>
          <tbody>{data.map((warning) => <tr key={warning.warning_id}>
            <td><code>{warning.user_id}</code></td><td><code>{warning.moderator_id}</code></td><td>{warning.reason || "—"}</td><td>{formatDate(warning.created_at)}</td>
            <td><Button variant="danger" size="sm" onClick={() => handleDelete(warning.warning_id)}>Remove</Button></td>
          </tr>)}</tbody></table>}
    </Card>
  );
}

function ChannelRulesSection({ guildId, draftRules, setDraftRules }) {
  const [channelId, setChannelId] = useState("");
  const [rule, setRule] = useState(RESTRICTION_TYPES[0]);

  const setRuleDraft = (channel, targetRule, enabled) => {
    setDraftRules((prev) => {
      const next = prev.map((item) => item.channel_id === channel ? { ...item, [targetRule]: enabled } : item);
      if (!prev.some((item) => item.channel_id === channel)) {
        const item = { channel_id: channel, image_only: false, clips_only: false, [targetRule]: enabled };
        return [...prev, item];
      }
      return next;
    });
  };

  const addDraft = (event) => {
    event.preventDefault();
    if (!channelId) return;
    setRuleDraft(String(channelId).trim(), rule, true);
    setChannelId("");
  };

  const removeDraft = (channel) => setDraftRules((prev) => prev.filter((item) => item.channel_id !== channel));

  return (
    <Card title="Channel rules" description="Changes stay pending until Save changes.">
      <form className="inline-form" onSubmit={addDraft}>
        <ChannelSelector label="Channel" value={channelId} onChange={setChannelId} allowBlank={false} allowAutoCreate autoLabel="Auto-create channel on Save" />
        <Select label="Rule" options={RESTRICTION_OPTIONS} value={rule} onChange={(e) => setRule(e.target.value)} />
        <Button type="submit">Add</Button>
      </form>
      {draftRules.length === 0 ? <EmptyState title="No channel rules" description="No channels are restricted yet." /> :
        <table className="table"><thead><tr><th>Channel</th><th>Image only</th><th>Clips only</th><th /></tr></thead>
          <tbody>{draftRules.map((r) => <tr key={r.channel_id}>
            <td>#{r.channel_id}</td>
            <td><Toggle checked={!!r.image_only} onChange={(v) => setRuleDraft(r.channel_id, "image_only", v)} /></td>
            <td><Toggle checked={!!r.clips_only} onChange={(v) => setRuleDraft(r.channel_id, "clips_only", v)} /></td>
            <td><Button variant="danger" size="sm" onClick={() => removeDraft(r.channel_id)}>Remove</Button></td>
          </tr>)}</tbody></table>}
    </Card>
  );
}

function WhitelistSection({ guildId, draftEntries, setDraftEntries }) {
  const [targetId, setTargetId] = useState("");
  const [restrictionType, setRestrictionType] = useState(RESTRICTION_TYPES[0]);

  const addDraft = (event) => {
    event.preventDefault();
    if (!targetId) return;
    const entry = { target_id: targetId.trim(), restriction_type: restrictionType };
    setDraftEntries((prev) => prev.some((e) => e.target_id === entry.target_id && e.restriction_type === entry.restriction_type) ? prev : [...prev, entry]);
    setTargetId("");
  };

  return (
    <Card title="Restriction whitelist" description="Changes stay pending until Save changes.">
      <form className="inline-form" onSubmit={addDraft}>
        <Input label="User or role ID" value={targetId} onChange={(e) => setTargetId(e.target.value)} placeholder="123456789012345678" />
        <Select label="Restriction" options={RESTRICTION_OPTIONS} value={restrictionType} onChange={(e) => setRestrictionType(e.target.value)} />
        <Button type="submit">Add</Button>
      </form>
      {draftEntries.length === 0 ? <EmptyState title="No whitelist entries" description="Everyone is subject to channel rules." /> :
        <table className="table"><thead><tr><th>ID</th><th>Restriction</th><th /></tr></thead>
          <tbody>{draftEntries.map((entry) => <tr key={`${entry.target_id}-${entry.restriction_type}`}>
            <td><code>{entry.target_id}</code></td><td>{entry.restriction_type}</td>
            <td><Button variant="danger" size="sm" onClick={() => setDraftEntries((prev) => prev.filter((e) => !(e.target_id === entry.target_id && e.restriction_type === entry.restriction_type)))}>Remove</Button></td>
          </tr>)}</tbody></table>}
    </Card>
  );
}

export default function Moderation() {
  const { guildId } = useGuild();
  const channelApi = useApi(() => listChannelRules(guildId), [guildId]);
  const whitelistApi = useApi(() => listWhitelist(guildId), [guildId]);
  const [draftRules, setDraftRules] = useState([]);
  const [draftEntries, setDraftEntries] = useState([]);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => { if (channelApi.data) setDraftRules(channelApi.data); }, [channelApi.data]);
  useEffect(() => { if (whitelistApi.data) setDraftEntries(whitelistApi.data); }, [whitelistApi.data]);

  const save = async () => {
    setSaving(true);
    try {
      const originalRules = channelApi.data || [];
      const originalByChannel = new Map(originalRules.map((r) => [r.channel_id, r]));
      const desiredByChannel = new Map(draftRules.map((r) => [r.channel_id, r]));
      for (const [channel, old] of originalByChannel) {
        const desired = desiredByChannel.get(channel);
        for (const rule of ["image_only", "clips_only"]) {
          const oldEnabled = !!old[rule], newEnabled = !!desired?.[rule];
          if (oldEnabled !== newEnabled) await setChannelRule(guildId, channel, rule, newEnabled);
        }
      }
      for (const [channel, desired] of desiredByChannel) {
        if (!originalByChannel.has(channel)) {
          for (const rule of ["image_only", "clips_only"]) if (desired[rule]) await setChannelRule(guildId, channel, rule, true);
        }
      }

      const originalEntries = whitelistApi.data || [];
      const key = (e) => `${e.target_id}-${e.restriction_type}`;
      const desiredKeys = new Set(draftEntries.map(key));
      for (const e of originalEntries) if (!desiredKeys.has(key(e))) await removeWhitelistEntry(guildId, e.target_id, e.restriction_type);
      const originalKeys = new Set(originalEntries.map(key));
      for (const e of draftEntries) if (!originalKeys.has(key(e))) await addWhitelistEntry(guildId, e.target_id, e.restriction_type);

      await Promise.all([channelApi.refetch(), whitelistApi.refetch()]);
      setToast({ message: "Moderation changes saved.", variant: "success" });
    } catch (err) {
      setToast({ message: err.message || "Couldn't save moderation changes.", variant: "error" });
    } finally { setSaving(false); }
  };

  if (channelApi.loading || whitelistApi.loading) return <Loader label="Loading moderation settings…" />;
  if (channelApi.error) return <ErrorState error={channelApi.error} onRetry={channelApi.refetch} />;
  if (whitelistApi.error) return <ErrorState error={whitelistApi.error} onRetry={whitelistApi.refetch} />;

  return (
    <div>
      <div className="card-header">
        <div><h1>Moderation</h1><p>Configuration changes stay pending until you press Save changes.</p></div>
        <Button onClick={save} loading={saving}>Save changes</Button>
      </div>
      <WarningsSection guildId={guildId} />
      <ChannelRulesSection guildId={guildId} draftRules={draftRules} setDraftRules={setDraftRules} />
      <WhitelistSection guildId={guildId} draftEntries={draftEntries} setDraftEntries={setDraftEntries} />
      <Toast message={toast?.message} variant={toast?.variant} onDismiss={() => setToast(null)} />
    </div>
  );
}
