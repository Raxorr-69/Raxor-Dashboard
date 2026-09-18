// In the single-service Render deployment the browser and API share the
// same origin. VITE_API_BASE_URL remains supported for local development
// or a future split deployment.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || window.location.origin;

export const STORAGE_TOKEN_KEY = "raxor_token";