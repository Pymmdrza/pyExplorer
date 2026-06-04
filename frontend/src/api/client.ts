import type {
  AddressResponse,
  ApiErrorBody,
  BlockResponse,
  NetworkOverview,
  SearchResult,
  TransactionResponse,
} from './types'

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/$/, '')

export class ApiError extends Error {
  code: string
  details?: unknown
  status: number

  constructor(body: ApiErrorBody, status: number) {
    super(body.message)
    this.name = 'ApiError'
    this.code = body.code
    this.details = body.details
    this.status = status
  }
}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: 'application/json' },
    signal,
  })

  if (!response.ok) {
    let body: ApiErrorBody = {
      code: 'HTTP_ERROR',
      message: `Request failed with status ${response.status}`,
    }
    try {
      body = (await response.json()) as ApiErrorBody
    } catch {
      // Keep the generic body when the upstream response is not JSON.
    }
    throw new ApiError(body, response.status)
  }

  return (await response.json()) as T
}

export function getNetworkOverview(signal?: AbortSignal): Promise<NetworkOverview> {
  return request<NetworkOverview>('/network/overview', signal)
}

export function searchExplorer(query: string, signal?: AbortSignal): Promise<SearchResult> {
  return request<SearchResult>(`/search?q=${encodeURIComponent(query)}`, signal)
}

export function getTransaction(
  txHash: string,
  signal?: AbortSignal,
): Promise<TransactionResponse> {
  return request<TransactionResponse>(`/transactions/${encodeURIComponent(txHash)}`, signal)
}

export function getAddress(
  address: string,
  page = 1,
  perPage = 10,
  signal?: AbortSignal,
): Promise<AddressResponse> {
  const query = new URLSearchParams({ page: String(page), per_page: String(perPage) })
  return request<AddressResponse>(`/addresses/${encodeURIComponent(address)}?${query}`, signal)
}

export function getBlock(
  height: string | number,
  page = 1,
  perPage = 10,
  signal?: AbortSignal,
): Promise<BlockResponse> {
  const query = new URLSearchParams({ page: String(page), per_page: String(perPage) })
  return request<BlockResponse>(`/blocks/${encodeURIComponent(String(height))}?${query}`, signal)
}

export function transactionStreamUrl(): string {
  return `${API_BASE_URL}/stream/transactions`
}

export function absoluteApiUrl(apiPath: string): string {
  const normalizedPath = apiPath.startsWith('/') ? apiPath : `/${apiPath}`
  if (/^https?:\/\//i.test(API_BASE_URL)) {
    return `${API_BASE_URL}${normalizedPath}`
  }
  return `${window.location.origin}${API_BASE_URL}${normalizedPath}`
}
