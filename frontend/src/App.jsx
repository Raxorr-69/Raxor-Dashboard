import { useEffect } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";

import ProtectedRoute from "./auth/ProtectedRoute";
import Login from "./auth/Login";
import AuthLayout from "./layouts/AuthLayout";
import DashboardLayout from "./layouts/DashboardLayout";
import Loader from "./components/common/Loader";
import { useAuth } from "./hooks/useAuth";

import Home from "./pages/Home";
import ServerSelect from "./pages/ServerSelect";
import Overview from "./pages/Overview";
import Statistics from "./pages/Statistics";
import Leaderboard from "./pages/Leaderboard";
import Leveling from "./pages/Leveling";
import Moderation from "./pages/Moderation";
import AutoMod from "./pages/AutoMod";
import Users from "./pages/Users";
import Invites from "./pages/Invites";
import Afk from "./pages/Afk";
import Recovery from "./pages/Recovery";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

/**
 * Landing spot for the backend's OAuth redirect
 * (`${FRONTEND_URL}/auth/callback?login_code=...`). AuthProvider's own
 * effect already reads the `login_code` param, exchanges it for a
 * session token, and loads the session no matter which route it lands
 * on — this view just waits for that to finish and then sends the
 * browser on to the server list.
 */
function AuthCallback() {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading) {
      navigate(isAuthenticated ? "/servers" : "/login", { replace: true });
    }
  }, [loading, isAuthenticated, navigate]);

  return <Loader label="Signing you in…" fullscreen />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />

      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route path="/servers" element={<ServerSelect />} />

        <Route path="/dashboard/:guildId" element={<DashboardLayout />}>
          <Route index element={<Overview />} />
          <Route path="statistics" element={<Statistics />} />
          <Route path="leaderboard" element={<Leaderboard />} />
          <Route path="leveling" element={<Leveling />} />
          <Route path="moderation" element={<Moderation />} />
          <Route path="automod" element={<AutoMod />} />
          <Route path="users" element={<Users />} />
          <Route path="users/:userId" element={<Users />} />
          <Route path="invites" element={<Invites />} />
          <Route path="afk" element={<Afk />} />
          <Route path="recovery" element={<Recovery />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Route>

      <Route path="/404" element={<NotFound />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}
