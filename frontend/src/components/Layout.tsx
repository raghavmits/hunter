import { NavLink, Outlet } from "react-router";
import styles from "./Layout.module.css";

const NAV_ITEMS = [
  { to: "/", label: "Digest" },
  { to: "/threads", label: "Threads" },
  { to: "/funnel", label: "Funnel" },
  { to: "/corpus", label: "Corpus" },
];

export function Layout() {
  return (
    <div className={styles.layout}>
      <nav className={styles.nav}>
        <span className={styles.brand}>Hunter</span>
        <ul className={styles.navList}>
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) => (isActive ? styles.navLinkActive : styles.navLink)}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
