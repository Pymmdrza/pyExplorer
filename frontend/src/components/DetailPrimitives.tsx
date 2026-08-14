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

interface IdentifierValueProps {
  value: string
  to?: string
  copyValue?: string
  className?: string
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
  return (
    <div className="identifier-block">
      <span className="identifier-block__label">{label}</span>
      <IdentifierValue value={value} copyValue={value} className="identifier-value--hero" />
    </div>
  )
}

export function IdentifierValue({ value, to, copyValue, className }: IdentifierValueProps) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    if (!copyValue) {
      return
    }
    try {
      await navigator.clipboard.writeText(copyValue)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className={`identifier-value ${className ?? ''}`.trim()}>
      {to ? (
        <Link className="identifier-link" to={to} title={value}>
          {value}
        </Link>
      ) : (
        <code className="identifier-text" title={value}>{value}</code>
      )}
      {copyValue ? (
        <button type="button" className="identifier-copy" onClick={handleCopy}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      ) : null}
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
