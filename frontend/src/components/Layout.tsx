import { Link, Outlet } from 'react-router-dom'

import { useTheme } from '../theme/useTheme'

export function Layout() {
  const { theme, toggleTheme } = useTheme()
  const nextThemeLabel = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/" aria-label="pyExplorer home">
          <span className="brand-mark" aria-hidden="true">
            ₿
          </span>
          <span>
            <strong>pyExplorer</strong>
            <small>Bitcoin intelligence console</small>
          </span>
        </Link>
        <div className="topbar-actions">
          <nav aria-label="Primary navigation">
            <Link to="/">Dashboard</Link>
            <Link to="/#network">Network</Link>
            <Link to="/#live">Live feed</Link>
            <Link to="/#providers">Data sources</Link>
          </nav>
          <button
            className="theme-toggle"
            type="button"
            onClick={toggleTheme}
            aria-label={nextThemeLabel}
            title={nextThemeLabel}
          >
            <span aria-hidden="true">{theme === 'dark' ? '☾' : '☼'}</span>
            {theme === 'dark' ? 'Dark' : 'Light'}
          </button>
        </div>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  )
}
