export function formatCompactNumber(value: number, maximumFractionDigits = 2): string {
  if (!Number.isFinite(value) || value === 0) {
    return '—'
  }
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits,
  }).format(value)
}

export function formatInteger(value: number): string {
  if (!Number.isFinite(value) || value === 0) {
    return '—'
  }
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
}

export function formatCurrency(value: number): string {
  if (!Number.isFinite(value) || value === 0) {
    return '—'
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatBitcoin(value: number, maximumFractionDigits = 8): string {
  if (!Number.isFinite(value) || value === 0) {
    return '—'
  }
  return `${new Intl.NumberFormat('en-US', {
    maximumFractionDigits,
  }).format(value)} BTC`
}

export function formatHash(value: string, head = 8, tail = 8): string {
  if (value.length <= head + tail + 3) {
    return value
  }
  return `${value.slice(0, head)}…${value.slice(-tail)}`
}

export function formatIsoDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'Just now'
  }
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function formatUnixTime(value?: number | null): string {
  if (!value) {
    return 'Pending'
  }
  const date = new Date(value * 1000)
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date)
}
