import { useCallback } from 'react'
import { useParams } from 'react-router-dom'

import { getAddress } from '../api/client'
import {
  DetailHeader,
  ErrorPanel,
  IdentifierValue,
  LoadingPanel,
} from '../components/DetailPrimitives'
import { useApiResource } from '../hooks/useApiResource'
import { formatBitcoin, formatInteger, formatIsoDate } from '../utils/format'

export function AddressPage() {
  const { address = '' } = useParams()
  const loadAddress = useCallback((signal: AbortSignal) => getAddress(address, 1, 25, signal), [address])
  const addressState = useApiResource(loadAddress)

  return (
    <div className="record-page">
      <DetailHeader
        eyebrow="Address"
        title="Address"
        description="Current balance, lifetime transfer volume, and the most recent address activity."
        identifier={address}
        identifierLabel="Bitcoin address"
      />

      {addressState.loading ? <LoadingPanel label="Loading address" /> : null}
      {addressState.error ? <ErrorPanel message={addressState.error} /> : null}

      {addressState.data ? (
        <>
          <section className="balance-panel" aria-label="Address balance">
            <div className="balance-panel__lead">
              <span className="summary-label">Current balance</span>
              <strong>{formatBitcoin(addressState.data.final_balance_btc)}</strong>
              <span className="summary-note">Live balance for the currently viewed address.</span>
              <IdentifierValue value={addressState.data.address} copyValue={addressState.data.address} className="balance-panel__identifier" />
            </div>
            <dl className="balance-panel__metrics">
              <div>
                <dt>Total received</dt>
                <dd>{formatBitcoin(addressState.data.total_received_btc)}</dd>
              </div>
              <div>
                <dt>Total sent</dt>
                <dd>{formatBitcoin(addressState.data.total_sent_btc)}</dd>
              </div>
              <div>
                <dt>Transactions</dt>
                <dd>{formatInteger(addressState.data.tx_count)}</dd>
              </div>
            </dl>
          </section>

          <section className="record-section activity-section">
            <div className="section-heading section-heading--compact">
              <div>
                <span className="eyebrow">Activity</span>
                <h2>Transaction history</h2>
              </div>
              <span className="pagination-note">
                Page {addressState.data.pagination.current_page} of {addressState.data.pagination.total_pages}
              </span>
            </div>

            {addressState.data.transactions.length ? (
              <div className="activity-list">
                {addressState.data.transactions.map((transaction) => {
                  const incoming = transaction.balance_change_btc >= 0
                  return (
                    <article className="activity-row" key={transaction.hash}>
                      <div className="activity-row__direction" data-direction={incoming ? 'in' : 'out'}>
                        <span>{incoming ? 'Received' : 'Sent'}</span>
                      </div>
                      <div className="activity-row__main">
                        <span className="activity-row__label">Transaction hash</span>
                        <IdentifierValue
                          value={transaction.hash}
                          to={`/transactions/${transaction.hash}`}
                          copyValue={transaction.hash}
                        />
                        <span className="activity-row__time">
                          {transaction.time ? formatIsoDate(transaction.time) : 'Pending confirmation'}
                        </span>
                      </div>
                      <div className="activity-row__amount">
                        <span>Balance change</span>
                        <strong>{formatBitcoin(transaction.balance_change_btc)}</strong>
                        <small>Absolute value {formatBitcoin(transaction.value_btc)}</small>
                      </div>
                    </article>
                  )
                })}
              </div>
            ) : (
              <div className="empty-state">
                <strong>No transaction activity</strong>
                <span>No transaction history is currently available for this address.</span>
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  )
}
