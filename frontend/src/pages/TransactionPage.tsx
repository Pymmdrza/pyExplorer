import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getTransaction } from '../api/client'
import { DetailHeader, ErrorPanel, KeyValue, LoadingPanel } from '../components/DetailPrimitives'
import { useApiResource } from '../hooks/useApiResource'
import { formatBitcoin, formatInteger, formatIsoDate } from '../utils/format'

export function TransactionPage() {
  const { txHash = '' } = useParams()
  const loadTransaction = useCallback(
    (signal: AbortSignal) => getTransaction(txHash, signal),
    [txHash],
  )
  const transaction = useApiResource(loadTransaction)

  return (
    <div className="record-page">
      <DetailHeader
        eyebrow="Transaction"
        title="Transaction record"
        description="Canonical transaction data, settlement context, value flow, and endpoint details."
        identifier={txHash}
        identifierLabel="Transaction ID"
      />

      {transaction.loading ? <LoadingPanel label="Loading transaction" /> : null}
      {transaction.error ? <ErrorPanel message={transaction.error} /> : null}

      {transaction.data ? (
        <>
          <section className="record-summary" aria-label="Transaction summary">
            <div className="record-summary__primary">
              <span className="summary-label">Transferred value</span>
              <strong>{formatBitcoin(transaction.data.value_btc)}</strong>
              <span className="summary-note">Total output value represented by this transaction</span>
            </div>
            <dl className="record-facts">
              <KeyValue label="Fee" value={formatBitcoin(transaction.data.fee_btc)} />
              <KeyValue label="Confirmations" value={formatInteger(transaction.data.confirmations)} />
              <KeyValue label="Size" value={`${formatInteger(transaction.data.size)} bytes`} />
              <KeyValue label="Timestamp" value={formatIsoDate(transaction.data.time)} />
            </dl>
          </section>

          <section className="record-section">
            <div className="section-heading section-heading--compact">
              <div>
                <span className="eyebrow">Settlement</span>
                <h2>Block context</h2>
              </div>
              {transaction.data.block_height > 0 ? (
                <Link className="outlined-link" to={`/blocks/${transaction.data.block_height}`}>
                  Open block {formatInteger(transaction.data.block_height)}
                </Link>
              ) : (
                <span className="status-tag">Unconfirmed</span>
              )}
            </div>
            <dl className="fact-strip">
              <KeyValue label="Block height" value={transaction.data.block_height > 0 ? formatInteger(transaction.data.block_height) : 'Pending'} />
              <KeyValue label="Transaction ID" value={transaction.data.hash} mono />
            </dl>
          </section>

          <section className="flow-grid" aria-label="Transaction value flow">
            <EndpointList title="Inputs" endpoints={transaction.data.inputs} />
            <EndpointList title="Outputs" endpoints={transaction.data.outputs} />
          </section>
        </>
      ) : null}
    </div>
  )
}

interface EndpointListProps {
  title: string
  endpoints: Array<{ address: string; value_btc: number }>
}

function EndpointList({ title, endpoints }: EndpointListProps) {
  const total = endpoints.reduce((sum, endpoint) => sum + endpoint.value_btc, 0)

  return (
    <article className="record-section endpoint-panel">
      <div className="section-heading section-heading--compact">
        <div>
          <span className="eyebrow">Value flow</span>
          <h2>{title}</h2>
        </div>
        <div className="section-stat">
          <strong>{endpoints.length}</strong>
          <span>{formatBitcoin(total)}</span>
        </div>
      </div>

      {endpoints.length ? (
        <div className="endpoint-list">
          {endpoints.map((endpoint, index) => {
            const linkable = endpoint.address !== 'Unknown' && endpoint.address !== 'Coinbase'
            return (
              <div className="endpoint-row" key={`${endpoint.address}-${index}`}>
                <div className="endpoint-row__index">{String(index + 1).padStart(2, '0')}</div>
                <div className="endpoint-row__body">
                  <span className="endpoint-row__label">Address</span>
                  {linkable ? (
                    <Link className="full-identifier-link" to={`/addresses/${endpoint.address}`}>
                      {endpoint.address}
                    </Link>
                  ) : (
                    <code className="full-identifier">{endpoint.address}</code>
                  )}
                </div>
                <div className="endpoint-row__value">
                  <span>Value</span>
                  <strong>{formatBitcoin(endpoint.value_btc)}</strong>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="empty-state">
          <strong>No entries available</strong>
          <span>No {title.toLowerCase()} were returned for this transaction.</span>
        </div>
      )}
    </article>
  )
}
