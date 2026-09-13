import { API_BASE_URL } from "../lib/constants";
import { apiClient } from "./client";

export function getLoginUrl() {
  return `${API_BASE_URL}/auth/login`;
}

export function fetchCurrentUser() {
  return apiClient.get("/auth/me");
}

/** Trade the one-time `login_code` left in the URL by the OAuth
 * redirect for the real session token — see auth/AuthProvider.jsx and
 * backend/api/routes/auth.py's /callback + /exchange. The code itself
 * never carries the actual session, so it's safe for it to have
 * briefly appeared in the URL/browser history. */
export function exchangeLoginCode(loginCode) {
  return apiClient.post("/auth/exchange", { login_code: loginCode });
}

export function logout() {
  return apiClient.post("/auth/logout");
}
