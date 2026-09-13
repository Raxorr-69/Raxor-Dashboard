export function formatNumber(value) {
  if (value === null || value === undefined) return "0";
  return new Intl.NumberFormat().format(value);
}

export function formatDuration(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds || 0));

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  if (minutes > 0) {
    return `${minutes}m`;
  }

  return `${seconds}s`;
}

export function formatDate(isoString) {
  if (!isoString) return "—";

  return new Date(isoString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelativeTime(isoString) {
  if (!isoString) return "Never";

  const then = new Date(isoString).getTime();
  const now = Date.now();
  const diffSeconds = Math.round((now - then) / 1000);

  const divisions = [
    { amount: 60, unit: "second" },
    { amount: 60, unit: "minute" },
    { amount: 24, unit: "hour" },
    { amount: 7, unit: "day" },
    { amount: 4.34524, unit: "week" },
    { amount: 12, unit: "month" },
    { amount: Number.POSITIVE_INFINITY, unit: "year" },
  ];

  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

  let duration = diffSeconds;
  for (const division of divisions) {
    if (Math.abs(duration) < division.amount) {
      return rtf.format(-Math.round(duration), division.unit);
    }
    duration /= division.amount;
  }

  return "—";
}

export function discordAvatarFallback(userId) {
  const index = Number(BigInt(userId) % 5n);
  return `https://cdn.discordapp.com/embed/avatars/${index}.png`;
}

export function truncate(text, maxLength = 80) {
  if (!text) return "";
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text;
}
