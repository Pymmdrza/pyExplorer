export interface NetworkOverview {
  market_price_usd: number
  hash_rate: number
  total_fees_btc: number
  total_blocks: number
  blocks_mined: number
  minutes_between_blocks: number
  difficulty: number
  tx_count_24h: number
  mempool_size: number
  latest_block_height: number
  updated_at: string
}

export interface SearchResult {
  query: string
  type: 'transaction' | 'address' | 'block'
  api_path: string
  frontend_path: string
}

export interface LiveTransaction {
  hash: string
  time?: number | null
  amount_btc: number
  from_addresses: string[]
  to_addresses: string[]
}

export interface PaginationMeta {
  current_page: number
  per_page: number
  total_items: number
  total_pages: number
}

export interface TransactionEndpoint {
  address: string
  value_btc: number
}

export interface TransactionResponse {
  hash: string
  time: string
  block_height: number
  confirmations: number
  size: number
  value_btc: number
  fee_btc: number
  inputs: TransactionEndpoint[]
  outputs: TransactionEndpoint[]
}

export interface AddressTransaction {
  hash: string
  time?: string | null
  value_btc: number
  balance_change_btc: number
}

export interface AddressResponse {
  address: string
  final_balance_btc: number
  total_received_btc: number
  total_sent_btc: number
  tx_count: number
  transactions: AddressTransaction[]
  pagination: PaginationMeta
}

export interface BlockTransaction {
  hash: string
  time?: string | null
  value_btc: number
}

export interface BlockResponse {
  hash: string
  height: number
  version?: string | number | null
  timestamp: string
  tx_count: number
  size: number
  merkle_root: string
  nonce: number
  bits?: string | number | null
  difficulty: number
  transactions: BlockTransaction[]
  pagination: PaginationMeta
}

export interface ApiErrorBody {
  code: string
  message: string
  details?: unknown
}
