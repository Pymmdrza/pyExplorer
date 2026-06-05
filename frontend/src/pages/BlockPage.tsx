import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getBlock } from '../api/client'
import { DetailHeader, ErrorPanel, KeyValue, LoadingPanel } from '../components/DetailPrimitives'
import { MetricCard } from '../components/MetricCard'
import { useApiResource } from '../hooks/useApiResource'
import { formatBitcoin, formatCompactNumber, formatHash, formatInteger, formatIsoDate } from '../utils/format'

export function BlockPage() {
  const { height = '' } = useParams()
  const loadBlock = useCallback((signal: AbortSignal) => getBlock(height, 1, 25, signal), [height])
  const block = useApiResource(loadBlock)

  return (
    <div className="detail-page">
      <DetailHeader
        eyebrow="Block detail"
        title={`Block #${height}`}
        description="Inspect block metadata, mining context, and transaction summaries."
      />

      {block.loading ? <LoadingPanel label="Loading block…" /> : null}
      {block.error ? <ErrorPanel message={block.error} /> : null}

      {block.data ? (
        <>
          <section className="section-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Block overview</p>
                <h2>Mining metrics</h2>
              </div>
            </div>
            <div className="metrics-grid">
              <MetricCard
                label="Height"
                value={formatInteger(block.data.height)}
                detail="Position in the chain"
                tone="amber"
              />
              <MetricCard
                label="Transactions"
                value={formatInteger(block.data.tx_count)}
                detail="Recorded in this block"
                tone="blue"
              />
              <MetricCard
                label="Size"
                value={`${formatInteger(block.data.size)} bytes`}
                detail="Serialized block size"
                tone="green"
              />
              <MetricCard
                label="Difficulty"
                value={formatCompactNumber(block.data.difficulty)}
                detail="Mining target difficulty"
                tone="violet"
              />
            </div>
          </section>

          <section className="detail-grid">
            <article className="section-card data-card">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Identifiers</p>
                  <h2>Block facts</h2>
                </div>
              </div>
              <dl className="key-value-grid">
                <KeyValue label="Hash" value={block.data.hash} />
                <KeyValue label="Timestamp" value={formatIsoDate(block.data.timestamp)} />
                <KeyValue label="Merkle root" value={block.data.merkle_root} />
                <KeyValue label="Nonce" value={formatInteger(block.data.nonce)} />
                <KeyValue label="Bits" value={block.data.bits ?? '—'} />
                <KeyValue label="Version" value={block.data.version ?? '—'} />
              </dl>
            </article>
          </section>

          <section className="section-card table-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Transactions</p>
                <h2>Block transaction sample</h2>
              </div>
              <span className="muted">
                Page {block.data.pagination.current_page} of {block.data.pagination.total_pages}
              </span>
            </div>
            {block.data.transactions.length ? (
              <div className="responsive-table">
                <table>
                  <thead>
                    <tr>
                      <th>Transaction</th>
                      <th>Time</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {block.data.transactions.map((transaction) => (
                      <tr key={transaction.hash}>
                        <td className="hash-cell">
                          <Link to={`/transactions/${transaction.hash}`}>
                            {formatHash(transaction.hash)}
                          </Link>
                        </td>
                        <td>{transaction.time ? formatIsoDate(transaction.time) : 'Pending'}</td>
                        <td>{formatBitcoin(transaction.value_btc)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <strong>No transactions returned.</strong>
                <span>Block metadata is available, but transaction rows were not returned.</span>
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  )
}
