import { useEffect, useState } from 'react'

import { getRecentTransactions, transactionStreamUrl } from '../api/client'
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

function mergeTransactions(
  incoming: LiveTransaction[],
  current: LiveTransaction[],
  limit: number,
): LiveTransaction[] {
  const byHash = new Map<string, LiveTransaction>()
  for (const transaction of [...incoming, ...current]) {
    if (transaction.hash && !byHash.has(transaction.hash)) {
      byHash.set(transaction.hash, transaction)
    }
  }
  return [...byHash.values()].slice(0, limit)
}

export function useTransactionStream(limit = 8): StreamState {
  const [transactions, setTransactions] = useState<LiveTransaction[]>([])
  const [status, setStatus] = useState<StreamStatus>(() =>
    supportsEventSource() ? 'connecting' : 'unavailable',
  )

  useEffect(() => {
    const controller = new AbortController()
    const pollId = window.setInterval(() => void loadRecent(), 30_000)

    async function loadRecent() {
      try {
        const recent = await getRecentTransactions(limit, controller.signal)
        setTransactions((current) => mergeTransactions(recent, current, limit))
      } catch {
        if (!controller.signal.aborted && !supportsEventSource()) {
          setStatus('unavailable')
        }
      }
    }

    void loadRecent()

    if (!supportsEventSource()) {
      return () => {
        controller.abort()
        window.clearInterval(pollId)
      }
    }

    const source = new EventSource(transactionStreamUrl())

    source.onopen = () => setStatus('connected')
    source.onerror = () => setStatus('reconnecting')
    source.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as LiveTransaction
        setTransactions((current) => mergeTransactions([payload], current, limit))
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

    return () => {
      controller.abort()
      window.clearInterval(pollId)
      source.close()
    }
  }, [limit])

  return { transactions, status }
}
