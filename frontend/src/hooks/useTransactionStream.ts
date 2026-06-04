import { useEffect, useState } from 'react'

import { transactionStreamUrl } from '../api/client'
import type { LiveTransaction } from '../api/types'

type StreamStatus = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'unavailable'

interface StreamState {
  transactions: LiveTransaction[]
  status: StreamStatus
}

function parseStreamStatus(value: unknown): StreamStatus {
  if (value === 'connected' || value === 'connecting' || value === 'reconnecting' || value === 'idle') {
    return value
  }
  return 'reconnecting'
}

function supportsEventSource(): boolean {
  return typeof window !== 'undefined' && 'EventSource' in window
}

export function useTransactionStream(limit = 8): StreamState {
  const [transactions, setTransactions] = useState<LiveTransaction[]>([])
  const [status, setStatus] = useState<StreamStatus>(() =>
    supportsEventSource() ? 'connecting' : 'unavailable',
  )

  useEffect(() => {
    if (!supportsEventSource()) {
      return undefined
    }

    const source = new EventSource(transactionStreamUrl())

    source.onopen = () => setStatus('connected')
    source.onerror = () => setStatus('reconnecting')
    source.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as LiveTransaction
        setTransactions((current) => [payload, ...current].slice(0, limit))
        setStatus('connected')
      } catch {
        setStatus('reconnecting')
      }
    }
    source.addEventListener('ping', (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent<string>).data) as { status?: string }
        setStatus(parseStreamStatus(payload.status))
      } catch {
        setStatus('reconnecting')
      }
    })

    return () => source.close()
  }, [limit])

  return { transactions, status }
}
