from datetime import datetime
from typing import Optional, Dict, Any
from app.config.config_manager import config
from app.utils.api_client import make_request

def get_transaction_details(tx_hash: str) -> Optional[Dict[str, Any]]:
    """Get detailed transaction information"""
    try:
        url = config.get_node_url('tx') + tx_hash
        tx = make_request(url)

        if not tx:
            return None

        # Process inputs
        inputs = []
        for vin in tx.get('vin', []):
            inputs.append({
                'prev_out': {
                    'addr': vin.get('addresses', ['Unknown'])[0],
                    'value': float(vin.get('value', 0)) / 1e8
                }
            })

        # Process outputs
        outputs = []
        for vout in tx.get('vout', []):
            outputs.append({
                'addr': vout.get('addresses', ['Unknown'])[0] if vout.get('addresses') else 'Unknown',
                'value': float(vout.get('value', 0)) / 1e8
            })

        # Calculate total input and output values
        total_input = sum(float(vin.get('value', 0)) for vin in tx.get('vin', []))
        total_output = sum(float(vout.get('value', 0)) for vout in tx.get('vout', []))

        return {
            'hash': tx.get('txid', ''),
            'time': datetime.fromtimestamp(int(tx.get('blockTime', 0))),
            'block_height': int(tx.get('blockHeight', 0)),
            'confirmations': int(tx.get('confirmations', 0)),
            'size': int(tx.get('size', 0)),
            'value': total_output / 1e8,
            'fee': (total_input - total_output) / 1e8,
            'inputs': inputs,
            'out': outputs
        }
    except Exception as e:
        print(f"Error fetching transaction details: {str(e)}")
        return None
