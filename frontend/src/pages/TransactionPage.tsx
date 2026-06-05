import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getTransaction } from '../api/client'
import { DetailHeader, ErrorPanel, KeyValue, LoadingPanel } from '../components/DetailPrimitives'
import { useApiResource } from '../hooks/useApiResource'
import { formatBitcoin, formatHash, formatInteger, formatIsoDate } from '../utils/format'

export function TransactionPage() {
  const { txHash = '' } = useParams()
  const loadTransaction = useCallback(
    (signal: AbortSignal) => getTransaction(txHash, signal),
    [txHash],
  )
  const transaction = useApiResource(loadTransaction)

  return (
    <div className="detail-page">
      <DetailHeader
        eyebrow="Transaction detail"
        title={formatHash(txHash, 14, 14)}
        description="Review transaction timing, confirmations, inputs, outputs, fees, and related block information."
      />

      {transaction.loading ? <LoadingPanel label="Loading transaction…" /> : null}
      {transaction.error ? <ErrorPanel message={transaction.error} /> : null}

      {transaction.data ? (
        <>
          <section className="detail-grid">
            <article className="section-card data-card">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Summary</p>
                  <h2>Transaction facts</h2>
                </div>
              </div>
              <dl className="key-value-grid">
                <KeyValue label="Hash" value={transaction.data.hash} />
                <KeyValue label="Time" value={formatIsoDate(transaction.data.time)} />
                <KeyValue label="Confirmations" value={formatInteger(transaction.data.confirmations)} />
                <KeyValue label="Size" value={`${formatInteger(transaction.data.size)} bytes`} />
                <KeyValue label="Value" value={formatBitcoin(transaction.data.value_btc)} />
                <KeyValue label="Fee" value={formatBitcoin(transaction.data.fee_btc)} />
              </dl>
            </article>

            <article className="section-card data-card">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Block context</p>
                  <h2>Confirmed in block</h2>
                </div>
              </div>
              <Link className="large-link" to={`/blocks/${transaction.data.block_height}`}>
                #{formatInteger(transaction.data.block_height)}
              </Link>
              <p className="muted">
                Open the containing block to inspect peer transactions and block metadata.
              </p>
            </article>
          </section>

          <section className="detail-grid">
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
  return (
    <article className="section-card table-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{title}</p>
          <h2>{endpoints.length} entries</h2>
        </div>
      </div>
      {endpoints.length ? (
        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>Address</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map((endpoint, index) => (
                <tr key={`${endpoint.address}-${index}`}>
                  <td className="hash-cell">
                    {endpoint.address === 'Unknown' || endpoint.address === 'Coinbase' ? (
                      endpoint.address
                    ) : (
                      <Link to={`/addresses/${endpoint.address}`}>{endpoint.address}</Link>
                    )}
                  </td>
                  <td>{formatBitcoin(endpoint.value_btc)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <strong>No {title.toLowerCase()} found.</strong>
          <span>The selected data source did not return entries for this transaction.</span>
        </div>
      )}
    </article>
  )
}
