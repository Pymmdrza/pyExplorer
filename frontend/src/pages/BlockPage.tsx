import { useCallback } from 'react'
import { useParams } from 'react-router-dom'

import { getBlock } from '../api/client'
import {
  DetailHeader,
  ErrorPanel,
  IdentifierValue,
  KeyValue,
  LoadingPanel,
} from '../components/DetailPrimitives'
import { MetricCard } from '../components/MetricCard'
import { useApiResource } from '../hooks/useApiResource'
import { formatBitcoin, formatCompactNumber, formatInteger, formatIsoDate } from '../utils/format'

export function BlockPage() {
  const { height = '' } = useParams()
  const loadBlock = useCallback((signal: AbortSignal) => getBlock(height, 1, 25, signal), [height])
  const block = useApiResource(loadBlock)

  return (
    <div className="record-page">
      <DetailHeader
        eyebrow="Block"
        title={`Block #${height}`}
        description="Block metadata, mining context, and the transactions returned for this block."
        identifier={block.data?.hash}
        identifierLabel="Block hash"
      />

      {block.loading ? <LoadingPanel label="Loading block" /> : null}
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

          <section className="record-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Identifiers</p>
                <h2>Block facts</h2>
              </div>
            </div>
            <dl className="record-facts">
              <KeyValue label="Hash" value={block.data.hash} mono />
              <KeyValue label="Timestamp" value={formatIsoDate(block.data.timestamp)} />
              <KeyValue label="Merkle root" value={block.data.merkle_root} mono />
              <KeyValue label="Nonce" value={formatInteger(block.data.nonce)} />
              <KeyValue label="Bits" value={block.data.bits ?? 'Not available'} />
              <KeyValue label="Version" value={block.data.version ?? 'Not available'} />
            </dl>
          </section>

          <section className="record-section">
            <div className="section-heading section-heading--compact">
              <div>
                <p className="eyebrow">Transactions</p>
                <h2>Block transaction sample</h2>
              </div>
              <span className="muted">
                Page {block.data.pagination.current_page} of {block.data.pagination.total_pages}
              </span>
            </div>
            {block.data.transactions.length ? (
              <div className="activity-list activity-list--compact">
                {block.data.transactions.map((transaction) => (
                  <article className="activity-row activity-row--compact" key={transaction.hash}>
                    <div className="activity-row__direction" data-direction="in">
                      <span>Transaction</span>
                    </div>
                    <div className="activity-row__main">
                      <span className="activity-row__label">Transaction hash</span>
                      <IdentifierValue
                        value={transaction.hash}
                        to={`/transactions/${transaction.hash}`}
                        copyValue={transaction.hash}
                      />
                      <span className="activity-row__time">
                        {transaction.time ? formatIsoDate(transaction.time) : 'Pending'}
                      </span>
                    </div>
                    <div className="activity-row__amount">
                      <span>Value</span>
                      <strong>{formatBitcoin(transaction.value_btc)}</strong>
                    </div>
                  </article>
                ))}
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
