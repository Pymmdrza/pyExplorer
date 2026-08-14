import { Link, NavLink, Outlet } from 'react-router-dom'

import { useTheme } from '../theme/useTheme'

export function Layout() {
  const { theme, toggleTheme } = useTheme()
  const nextThemeLabel = theme === 'dark' ? 'Use light theme' : 'Use dark theme'

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__inner">
          <Link className="brand" to="/" aria-label="pyExplorer home">
            <span className="brand-mark" aria-hidden="true">PX</span>
            <span className="brand-copy">
              <strong>pyExplorer</strong>
              <small>Bitcoin network explorer</small>
            </span>
          </Link>

          <div className="topbar-actions">
            <nav className="primary-nav" aria-label="Primary navigation">
              <NavLink to="/" end>Overview</NavLink>
              <a href="/#network">Network</a>
              <a href="/#live">Transactions</a>
              <a href="/#providers">Sources</a>
            </nav>
            <button
              className="theme-toggle"
              type="button"
              onClick={toggleTheme}
              aria-label={nextThemeLabel}
              title={nextThemeLabel}
            >
              {theme === 'dark' ? 'Dark' : 'Light'}
            </button>
          </div>
        </div>
      </header>

      <main className="page-shell">
        <Outlet />
      </main>

      <footer className="site-footer">
        <span>pyExplorer</span>
        <span>Independent Bitcoin network data interface</span>
      </footer>
    </div>
  )
}
