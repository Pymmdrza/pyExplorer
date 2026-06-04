interface MetricCardProps {
  label: string
  value: string
  detail: string
  tone?: 'amber' | 'blue' | 'green' | 'violet'
}

export function MetricCard({ label, value, detail, tone = 'blue' }: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <span className="metric-card__label">{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  )
}
