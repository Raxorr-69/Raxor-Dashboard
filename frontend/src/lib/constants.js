// In the single-service Render deployment the browser and API share the
// same origin. VITE_API_BASE_URL remains supported for local development
// or a future split deployment.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || window.location.origin;

export const STORAGE_TOKEN_KEY = "raxor_token";

export const NAV_ITEMS = [
  { to: "", label: "Overview" },
  { to: "statistics", label: "Statistics" },
  { to: "leaderboard", label: "Leaderboard" },
  { to: "leveling", label: "Leveling" },
  { to: "moderation", label: "Moderation" },
  { to: "automod", label: "AutoMod" },
  { to: "users", label: "Users" },
  { to: "invites", label: "Invites" },
  { to: "afk", label: "AFK" },
  { to: "recovery", label: "Recovery" },
  { to: "settings", label: "Settings" },
];

export const MODERATION_ACTIONS = [
  "warn",
  "delete",
  "timeout",
];

export const RESTRICTION_TYPES = [
  "image_only",
  "clips_only",
];

export const LEADERBOARD_TYPES = [
  "messages",
  "voice",
];

export const RANK_PERIODS = [
  "weekly",
  "monthly",
  "all",
];