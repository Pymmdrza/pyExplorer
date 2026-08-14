import { useState } from 'react'
import { Link } from 'react-router-dom'

interface DetailHeaderProps {
  eyebrow: string
  title: string
  description: string
  identifier?: string
  identifierLabel?: string
}

interface KeyValueProps {
  label: string
  value: string | number | null | undefined
  mono?: boolean
}

export function DetailHeader({
  eyebrow,
  title,
  description,
  identifier,
  identifierLabel,
}: DetailHeaderProps) {
  return (
    <header className="record-header">
      <div className="record-header__topline">
        <Link className="back-link" to="/">Overview</Link>
        <span className="record-header__divider" aria-hidden="true" />
        <span className="eyebrow">{eyebrow}</span>
      </div>
      <h1>{title}</h1>
      <p className="record-header__description">{description}</p>
      {identifier ? (
        <IdentifierBlock label={identifierLabel ?? 'Identifier'} value={identifier} />
      ) : null}
    </header>
  )
}

export function IdentifierBlock({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)

  async function copyValue() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="identifier-block">
      <div className="identifier-block__meta">
        <span>{label}</span>
        <button type="button" className="text-action" onClick={copyValue}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <code>{value}</code>
    </div>
  )
}

export function LoadingPanel({ label = 'Loading record...' }: { label?: string }) {
  return (
    <div className="state-panel" role="status" aria-live="polite">
      <span className="state-panel__pulse" aria-hidden="true" />
      <div>
        <strong>{label}</strong>
        <span>Retrieving the latest available network data.</span>
      </div>
    </div>
  )
}

export function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="state-panel state-panel--error" role="alert">
      <div>
        <strong>Record could not be retrieved</strong>
        <span>{message}</span>
      </div>
      <button type="button" className="secondary-button" onClick={() => window.location.reload()}>
        Retry
      </button>
    </div>
  )
}

export function KeyValue({ label, value, mono = false }: KeyValueProps) {
  return (
    <div className="key-value">
      <dt>{label}</dt>
      <dd className={mono ? 'mono-value' : undefined}>{value ?? 'Not available'}</dd>
    </div>
  )
}
