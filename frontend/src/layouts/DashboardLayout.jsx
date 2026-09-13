import { Outlet } from "react-router-dom";

import MobileNav from "../components/layout/MobileNav";
import Sidebar from "../components/layout/Sidebar";
import Topbar from "../components/layout/Topbar";
import { useGuild } from "../hooks/useGuild";
import EmptyState from "../components/common/EmptyState";
import Button from "../components/common/Button";

export default function DashboardLayout() {
  const { guildId, guild, isBotPresent } = useGuild();

  if (!isBotPresent) {
    return (
      <div className="dashboard-shell">
        <div className="dashboard-main dashboard-main-centered">
          <EmptyState
            title="Raxor isn't in this server yet"
            description="Add the bot to this server before managing it from the dashboard."
            action={
              <Button as="a" href="/">
                Back to server list
              </Button>
            }
          />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-shell">
      <Sidebar guildId={guildId} />

      <div className="dashboard-main">
        <Topbar guild={guild} />

        <div className="dashboard-content">
          <Outlet />
        </div>

        <MobileNav guildId={guildId} />
      </div>
    </div>
  );
}
