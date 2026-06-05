import { Link } from 'react-router-dom'

interface DetailHeaderProps {
  eyebrow: string
  title: string
  description: string
}

interface KeyValueProps {
  label: string
  value: string | number | null | undefined
}

export function DetailHeader({ eyebrow, title, description }: DetailHeaderProps) {
  return (
    <section className="detail-hero">
      <Link className="back-link" to="/">
        ← Back to dashboard
      </Link>
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p className="hero-copy">{description}</p>
    </section>
  )
}

export function LoadingPanel({ label = 'Loading explorer data…' }: { label?: string }) {
  return (
    <div className="section-card empty-state" role="status">
      <strong>{label}</strong>
      <span>Retrieving the latest explorer data.</span>
    </div>
  )
}

export function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="section-card inline-alert" role="alert">
      <strong>Unable to load this resource.</strong>
      <span>{message}</span>
    </div>
  )
}

export function KeyValue({ label, value }: KeyValueProps) {
  return (
    <div className="key-value">
      <dt>{label}</dt>
      <dd>{value ?? '—'}</dd>
    </div>
  )
}
