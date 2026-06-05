import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getAddress } from '../api/client'
import { DetailHeader, ErrorPanel, KeyValue, LoadingPanel } from '../components/DetailPrimitives'
import { MetricCard } from '../components/MetricCard'
import { useApiResource } from '../hooks/useApiResource'
import { formatBitcoin, formatHash, formatInteger, formatIsoDate } from '../utils/format'

export function AddressPage() {
  const { address = '' } = useParams()
  const loadAddress = useCallback((signal: AbortSignal) => getAddress(address, 1, 25, signal), [address])
  const addressState = useApiResource(loadAddress)

  return (
    <div className="detail-page">
      <DetailHeader
        eyebrow="Address detail"
        title={formatHash(address, 16, 16)}
        description="Review balances, aggregate flow, and the latest activity for this address."
      />

      {addressState.loading ? <LoadingPanel label="Loading address…" /> : null}
      {addressState.error ? <ErrorPanel message={addressState.error} /> : null}

      {addressState.data ? (
        <>
          <section className="section-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Balance overview</p>
                <h2>Address metrics</h2>
              </div>
            </div>
            <div className="metrics-grid">
              <MetricCard
                label="Final balance"
                value={formatBitcoin(addressState.data.final_balance_btc)}
                detail="Current known balance"
                tone="amber"
              />
              <MetricCard
                label="Total received"
                value={formatBitcoin(addressState.data.total_received_btc)}
                detail="Lifetime inbound value"
                tone="green"
              />
              <MetricCard
                label="Total sent"
                value={formatBitcoin(addressState.data.total_sent_btc)}
                detail="Lifetime outbound value"
                tone="violet"
              />
              <MetricCard
                label="Transactions"
                value={formatInteger(addressState.data.tx_count)}
                detail="Observed activity count"
                tone="blue"
              />
            </div>
          </section>

          <section className="section-card table-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Recent activity</p>
                <h2>Latest transactions</h2>
              </div>
              <span className="muted">
                Page {addressState.data.pagination.current_page} of{' '}
                {addressState.data.pagination.total_pages}
              </span>
            </div>
            {addressState.data.transactions.length ? (
              <div className="responsive-table">
                <table>
                  <thead>
                    <tr>
                      <th>Transaction</th>
                      <th>Time</th>
                      <th>Value</th>
                      <th>Balance change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {addressState.data.transactions.map((transaction) => (
                      <tr key={transaction.hash}>
                        <td className="hash-cell">
                          <Link to={`/transactions/${transaction.hash}`}>
                            {formatHash(transaction.hash)}
                          </Link>
                        </td>
                        <td>{transaction.time ? formatIsoDate(transaction.time) : 'Pending'}</td>
                        <td>{formatBitcoin(transaction.value_btc)}</td>
                        <td>{formatBitcoin(transaction.balance_change_btc)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <strong>No transactions returned.</strong>
                <span>Transaction history is not currently available for this address.</span>
              </div>
            )}
          </section>

          <section className="section-card data-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Raw identifier</p>
                <h2>Address</h2>
              </div>
            </div>
            <dl className="key-value-grid">
              <KeyValue label="Address" value={addressState.data.address} />
            </dl>
          </section>
        </>
      ) : null}
    </div>
  )
}
