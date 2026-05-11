import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { GraduationCap, ListChecks, ScrollText, Menu, X } from 'lucide-react'
import styles from './Layout.module.css'

const NAV_LINKS = [
  { to: '/', label: 'Monitor', Icon: GraduationCap, exact: true },
  { to: '/registrations', label: 'Registrations', Icon: ListChecks },
  { to: '/admin/logs', label: 'Admin Logs', Icon: ScrollText },
]

export default function Layout({ children }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  return (
    <div className={styles.root}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.brand}>
            <span className={styles.brandIcon}>🎓</span>
            <span className={styles.brandName}>SEE Monitor</span>
          </div>

          {/* Desktop nav */}
          <nav className={styles.desktopNav}>
            {NAV_LINKS.map(({ to, label, Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`
                }
              >
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Mobile hamburger */}
          <button
            className={styles.menuBtn}
            onClick={() => setMenuOpen((p) => !p)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <nav className={styles.mobileNav}>
            {NAV_LINKS.map(({ to, label, Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `${styles.mobileNavLink} ${isActive ? styles.mobileNavLinkActive : ''}`
                }
                onClick={() => setMenuOpen(false)}
              >
                <Icon size={18} />
                {label}
              </NavLink>
            ))}
          </nav>
        )}
      </header>

      {/* Main content */}
      <main className={styles.main}>{children}</main>

      {/* Footer */}
      <footer className={styles.footer}>
        <p>SEE Result Monitor &bull; Built for Nepal students &bull; {new Date().getFullYear()}</p>
        <p className={styles.footerSub}>
          Checks&nbsp;
          <a href="https://see.ntc.net.np" target="_blank" rel="noreferrer">see.ntc.net.np</a>,&nbsp;
          <a href="https://result.neb.gov.np" target="_blank" rel="noreferrer">result.neb.gov.np</a>&nbsp;&amp;&nbsp;
          <a href="https://see.edusanjal.com" target="_blank" rel="noreferrer">see.edusanjal.com</a>
        </p>
      </footer>
    </div>
  )
}
