import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { absoluteApiUrl, searchExplorer } from '../api/client'
import type { SearchResult } from '../api/types'

const examples = ['840000', 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', 'a'.repeat(64)]

export function SearchPanel() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<SearchResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setResult(null)

    if (!query.trim()) {
      setError('Enter a transaction hash, Bitcoin address, or block height.')
      return
    }

    setLoading(true)
    try {
      setResult(await searchExplorer(query.trim()))
    } catch (searchError) {
      const message = searchError instanceof Error ? searchError.message : 'Search failed.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section id="search" className="search-panel" aria-labelledby="search-title">
      <div>
        <p className="eyebrow">Explore Bitcoin</p>
        <h1 id="search-title">Search blocks, addresses, and transactions in seconds.</h1>
        <p className="hero-copy">
          pyExplorer combines async provider fallback, live mempool streaming, and clean data
          normalization into a fast local/demo blockchain explorer.
        </p>
      </div>

      <form className="search-form" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="global-search">
          Transaction hash, Bitcoin address, or block height
        </label>
        <input
          id="global-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Paste tx hash, address, or block height"
          autoComplete="off"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      <div className="example-row" aria-label="Example searches">
        {examples.map((example) => (
          <button key={example} type="button" onClick={() => setQuery(example)}>
            {example.length > 18 ? `${example.slice(0, 12)}…` : example}
          </button>
        ))}
      </div>

      {error ? <p className="form-message form-message--error">{error}</p> : null}
      {result ? (
        <div className="search-result" role="status">
          <span>{result.type}</span>
          <strong>{result.query}</strong>
          <div className="action-row">
            <Link to={result.frontend_path}>Open explorer page</Link>
            <a href={absoluteApiUrl(result.api_path)} target="_blank" rel="noreferrer">
              Open API result
            </a>
          </div>
        </div>
      ) : null}
    </section>
  )
}
