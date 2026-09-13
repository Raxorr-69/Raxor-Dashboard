import { createContext, useCallback, useEffect, useRef, useState } from "react";

import { exchangeLoginCode, fetchCurrentUser, logout as logoutRequest } from "../api/auth";
import { clearToken, getToken, setToken } from "../lib/storage";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [guilds, setGuilds] = useState([]);
  const [loading, setLoading] = useState(true);
  // StrictMode/fast refresh can mount this twice; a login_code is
  // single-use, so a duplicate exchange call would fail the second
  // time and log the user right back out.
  const exchangedRef = useRef(false);

  const loadUser = useCallback(async () => {
    const token = getToken();

    if (!token) {
      setUser(null);
      setGuilds([]);
      setLoading(false);
      return;
    }

    try {
      const me = await fetchCurrentUser();
      setUser({
        id: me.id,
        username: me.username,
        avatarUrl: me.avatar_url,
        isDeveloper: me.is_developer,
      });
      setGuilds(me.guilds || []);
    } catch {
      clearToken();
      setUser(null);
      setGuilds([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Pick up ?login_code=... left by the backend's OAuth redirect,
    // wherever in the app it lands, and trade it for the real session
    // token via a POST body — the login_code itself is single-use and
    // short-lived, so it's fine for it to have briefly been in the URL;
    // the actual token never is. See backend/api/routes/auth.py.
    const params = new URLSearchParams(window.location.search);
    const loginCode = params.get("login_code");

    const cleanUrl = () => {
      params.delete("login_code");
      const cleanSearch = params.toString();
      window.history.replaceState(
        {},
        "",
        window.location.pathname + (cleanSearch ? `?${cleanSearch}` : "")
      );
    };

    if (loginCode && !exchangedRef.current) {
      exchangedRef.current = true;
      exchangeLoginCode(loginCode)
        .then(({ token }) => {
          setToken(token);
          cleanUrl();
          loadUser();
        })
        .catch(() => {
          cleanUrl();
          setLoading(false);
        });
      return;
    }

    loadUser();
  }, [loadUser]);

  const logout = useCallback(() => {
    // Best-effort: invalidate the session server-side too, not just
    // locally, so the token can't be replayed after "logging out".
    logoutRequest().catch(() => {});
    clearToken();
    setUser(null);
    setGuilds([]);
  }, []);

  const value = {
    user,
    guilds,
    loading,
    isAuthenticated: user !== null,
    logout,
    refetch: loadUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
