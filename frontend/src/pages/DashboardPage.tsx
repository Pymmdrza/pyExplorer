import { Link } from 'react-router-dom'

import { MetricCard } from '../components/MetricCard'
import { SearchPanel } from '../components/SearchPanel'
import { useNetworkOverview } from '../hooks/useNetworkOverview'
import { useTransactionStream } from '../hooks/useTransactionStream'
import {
  formatBitcoin,
  formatCompactNumber,
  formatCurrency,
  formatHash,
  formatInteger,
  formatIsoDate,
  formatUnixTime,
} from '../utils/format'

export function DashboardPage() {
  const network = useNetworkOverview()
  const live = useTransactionStream()
  const overview = network.data
  const recentHeights = Array.from(
    { length: 5 },
    (_, index) => overview.latest_block_height - index,
  ).filter((height) => height > 0)

  return (
    <>
      <section className="hero-grid">
        <SearchPanel />
        <aside className="status-card" aria-labelledby="status-title">
          <div className="status-card__header">
            <p className="eyebrow">System status</p>
            <span className={`status-pill status-pill--${network.status}`} role="status">
              {network.status}
            </span>
          </div>
          <h2 id="status-title">Explorer service is ready for live Bitcoin data.</h2>
          <p>
            Network records are retrieved on demand and cached briefly for a fast, consistent experience.
          </p>
          <dl className="status-list">
            <div>
              <dt>Updated</dt>
              <dd>{formatIsoDate(overview.updated_at)}</dd>
            </div>
            <div>
              <dt>Live feed</dt>
              <dd>{live.status}</dd>
            </div>
          </dl>
          {network.error ? <p className="inline-alert">{network.error}</p> : null}
        </aside>
      </section>

      <section id="network" className="section-card" aria-labelledby="metrics-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Network overview</p>
            <h2 id="metrics-title">Key Bitcoin metrics</h2>
          </div>
          <span className="muted">Current network snapshot</span>
        </div>
        <div className="metrics-grid">
          <MetricCard
            label="BTC price"
            value={formatCurrency(overview.market_price_usd)}
            detail="Current market price"
            tone="amber"
          />
          <MetricCard
            label="Latest block"
            value={formatInteger(overview.latest_block_height)}
            detail="Best known chain height"
            tone="blue"
          />
          <MetricCard
            label="24h transactions"
            value={formatCompactNumber(overview.tx_count_24h)}
            detail="Confirmed transaction volume"
            tone="green"
          />
          <MetricCard
            label="Difficulty"
            value={formatCompactNumber(overview.difficulty)}
            detail="Mining difficulty target"
            tone="violet"
          />
          <MetricCard
            label="Mempool"
            value={formatCompactNumber(overview.mempool_size)}
            detail="Unconfirmed transactions"
            tone="blue"
          />
          <MetricCard
            label="Hash rate"
            value={formatCompactNumber(overview.hash_rate)}
            detail="Estimated network hash rate"
            tone="green"
          />
          <MetricCard
            label="Block interval"
            value={`${overview.minutes_between_blocks.toFixed(1)} min`}
            detail="Average minutes between blocks"
            tone="amber"
          />
          <MetricCard
            label="Daily fees"
            value={formatBitcoin(overview.total_fees_btc)}
            detail="Fees recorded in the latest stats window"
            tone="violet"
          />
        </div>
      </section>

      <section className="content-grid">
        <article id="live" className="section-card" aria-labelledby="live-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Realtime mempool</p>
              <h2 id="live-title">Live transactions</h2>
            </div>
            <span className={`status-pill status-pill--${live.status}`}>{live.status}</span>
          </div>
          <div className="transaction-list">
            {live.transactions.length ? (
              live.transactions.map((transaction) => (
                <Link
                  className="transaction-row"
                  key={transaction.hash}
                  to={`/transactions/${transaction.hash}`}
                >
                  <div>
                    <strong>{formatHash(transaction.hash)}</strong>
                    <small>{formatUnixTime(transaction.time)}</small>
                  </div>
                  <span>{formatBitcoin(transaction.amount_btc, 5)}</span>
                </Link>
              ))
            ) : (
              <div className="empty-state">
                <strong>Waiting for the first mempool event...</strong>
                <span>Start the local data service to show unconfirmed transactions here.</span>
              </div>
            )}
          </div>
        </article>

        <article className="section-card" aria-labelledby="blocks-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Explorer shortcuts</p>
              <h2 id="blocks-title">Latest block trail</h2>
            </div>
          </div>
          <div className="block-list">
            {recentHeights.length ? (
              recentHeights.map((height) => (
                <Link key={height} to={`/blocks/${height}`}>
                  <span>Block #{formatInteger(height)}</span>
                  <small>Open explorer page</small>
                </Link>
              ))
            ) : (
              <div className="empty-state">
                <strong>No block height yet.</strong>
                <span>Network overview will populate this once the data service is reachable.</span>
              </div>
            )}
          </div>
        </article>
      </section>

    </>
  )
}
