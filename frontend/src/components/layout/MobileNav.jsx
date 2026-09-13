import { NavLink } from "react-router-dom";

import { NAV_ITEMS } from "../../lib/constants";

export default function MobileNav({ guildId }) {
  return (
    <nav className="mobile-nav">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={`/dashboard/${guildId}/${item.to}`}
          end={item.to === ""}
          className={({ isActive }) => `mobile-nav-link ${isActive ? "active" : ""}`.trim()}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
