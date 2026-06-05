import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { searchExplorer } from '../api/client'

const examples = [
  { label: 'Block height', value: '840000' },
  { label: 'Bitcoin address', value: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa' },
  { label: 'Transaction hash', value: 'a0db149ace545beabbd87a8d6b20ffd6aa3b5a50e58add49a3d435f898c272cf' },
]

export function SearchPanel() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    const trimmedQuery = query.trim()
    if (!trimmedQuery) {
      setError('Enter a transaction hash, Bitcoin address, or block height.')
      return
    }

    setLoading(true)
    try {
      const result = await searchExplorer(trimmedQuery)
      navigate(result.frontend_path)
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
        <p className="eyebrow">Blockchain explorer</p>
        <h1 id="search-title">Search Bitcoin blocks, addresses, and transactions.</h1>
        <p className="hero-copy">
          Enter an identifier to open the complete record with balances, confirmations, block
          context, and recent activity in one place.
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
          <button key={example.label} type="button" onClick={() => setQuery(example.value)}>
            {example.label}
          </button>
        ))}
      </div>

      {error ? <p className="form-message form-message--error">{error}</p> : null}
    </section>
  )
}
