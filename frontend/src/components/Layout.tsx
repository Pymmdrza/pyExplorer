import { Link, Outlet } from 'react-router-dom'

export function Layout() {
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
        <nav aria-label="Primary navigation">
          <Link to="/">Dashboard</Link>
          <Link to="/#network">Network</Link>
          <Link to="/#live">Live feed</Link>
          <Link to="/#providers">Providers</Link>
        </nav>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  )
}
