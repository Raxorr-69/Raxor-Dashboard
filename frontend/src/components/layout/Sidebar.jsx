import { NavLink } from "react-router-dom";

import { NAV_ITEMS } from "../../lib/constants";

export default function Sidebar({ guildId }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">Raxor</div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={`/dashboard/${guildId}/${item.to}`}
            end={item.to === ""}
            className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`.trim()}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <NavLink to="/" className="sidebar-switch">
        Switch server
      </NavLink>
    </aside>
  );
}
