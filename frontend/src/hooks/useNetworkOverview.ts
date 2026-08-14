import { useEffect, useState } from 'react'

import { getNetworkOverview } from '../api/client'
import type { NetworkOverview } from '../api/types'

const fallbackOverview: NetworkOverview = {
  market_price_usd: 0,
  hash_rate: 0,
  total_fees_btc: 0,
  total_blocks: 0,
  blocks_mined: 0,
  minutes_between_blocks: 0,
  difficulty: 0,
  tx_count_24h: 0,
  mempool_size: 0,
  latest_block_height: 0,
  updated_at: new Date().toISOString(),
}

type NetworkStatus = 'loading' | 'ready' | 'offline'

interface NetworkState {
  data: NetworkOverview
  status: NetworkStatus
  error?: string
}

export function useNetworkOverview(): NetworkState {
  const [state, setState] = useState<NetworkState>({ data: fallbackOverview, status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()

    getNetworkOverview(controller.signal)
      .then((data) => setState({ data, status: 'ready' }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) {
          return
        }
        const message = error instanceof Error ? error.message : 'Unable to reach the data service.'
        setState({ data: fallbackOverview, status: 'offline', error: message })
      })

    return () => controller.abort()
  }, [])

  return state
}
