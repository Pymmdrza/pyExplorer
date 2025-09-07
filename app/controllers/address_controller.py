from datetime import datetime
from typing import Optional, Dict, Any
from app.config.config_manager import config
from app.config.node_reader import NodeReader
from app.utils.api_client import make_request

nr = NodeReader()
base_urls = nr.get_nodes() # Get base urls List
addr_query = nr.get_query('address')
tx_query = nr.get_query('tx')
block_query = nr.get_query('block')
block_index_query = nr.get_query('blockIndex')
params_basic = nr.get_addr_params('basic')
params_txs = nr.get_addr_params('txs')
params_txslight = nr.get_addr_params('txsLight')
node_url = base_urls[0] # atomic = 0 | guarda = 1 | trezor = 2


def get_address_details(address: str, page: int = 1, per_page: int = 10) -> Optional[Dict[str, Any]]:
    """Get address information with transaction details"""
    try:
        url = f"{node_url}{addr_query}{address}{params_basic}"
        addr = make_request(url)
        if not addr:
            return None

        # Process transactions
        all_transactions = addr.get('transactions', [])  # Changed from 'txs' to 'transactions'
        if not isinstance(all_transactions, list):
            all_transactions = []

        total_transactions = len(all_transactions)
        total_pages = (total_transactions + per_page - 1) // per_page if total_transactions > 0 else 1

        # Get transactions for the current page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_transactions = []

        for tx in all_transactions[start_idx:end_idx]:
            try:
                # Calculate balance change for this address
                balance_change = 0
                for vout in tx.get('vout', []):
                    if address in vout.get('addresses', []):
                        balance_change += float(vout.get('value', 0))
                for vin in tx.get('vin', []):
                    if address in vin.get('addresses', []):
                        balance_change -= float(vin.get('value', 0))

                page_transactions.append({
                    'hash': tx.get('txid', ''),
                    'time': int(tx.get('blockTime', 0)),
                    'result': balance_change / 1e8,
                    'balance_change': balance_change / 1e8
                })
            except Exception as e:
                print(f"Error processing transaction: {str(e)}")
                continue

        return {
            'address': address,
            'final_balance': float(addr.get('balance', 0)) / 1e8,
            'total_received': float(addr.get('totalReceived', 0)) / 1e8,
            'total_sent': float(addr.get('totalSent', 0)) / 1e8,
            'n_tx': total_transactions,
            'transactions': page_transactions,
            'current_page': page,
            'total_pages': total_pages
        }
    except Exception as e:
        print(f"Error fetching address details: {str(e)}")
        return None