import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <section className="detail-hero not-found-card">
      <p className="eyebrow">404</p>
      <h1>Explorer route not found.</h1>
      <p className="hero-copy">
        The explorer currently supports the dashboard plus transaction, address, and block detail
        pages.
      </p>
      <Link className="pill-link" to="/">
        Return to dashboard
      </Link>
    </section>
  )
}
