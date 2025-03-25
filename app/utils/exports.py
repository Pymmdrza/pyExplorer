import json
import csv
from io import StringIO
from typing import Dict, Any, List

def format_transaction_data(tx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format transaction data for export"""
    return {
        'hash': tx_data.get('hash', ''),
        'time': tx_data.get('time', '').strftime('%Y-%m-%d %H:%M:%S'),
        'block_height': tx_data.get('block_height', 0),
        'confirmations': tx_data.get('confirmations', 0),
        'size': tx_data.get('size', 0),
        'value': tx_data.get('value', 0),
        'fee': tx_data.get('fee', 0)
    }

def format_address_data(addr_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format address data for export"""
    return {
        'address': addr_data.get('address', ''),
        'final_balance': addr_data.get('final_balance', 0),
        'total_received': addr_data.get('total_received', 0),
        'total_sent': addr_data.get('total_sent', 0),
        'n_tx': addr_data.get('n_tx', 0)
    }

def export_to_json(data: Dict[str, Any]) -> str:
    """Export data to JSON format"""
    return json.dumps(data, indent=2)

def export_to_csv(data: Dict[str, Any], data_type: str) -> str:
    """Export data to CSV format"""
    output = StringIO()
    writer = csv.writer(output)
    
    if data_type == 'transaction':
        writer.writerow(['Hash', 'Time', 'Block Height', 'Confirmations', 'Size', 'Value (BTC)', 'Fee (BTC)'])
        writer.writerow([
            data['hash'],
            data['time'],
            data['block_height'],
            data['confirmations'],
            data['size'],
            data['value'],
            data['fee']
        ])
    elif data_type == 'address':
        writer.writerow(['Address', 'Final Balance (BTC)', 'Total Received (BTC)', 'Total Sent (BTC)', 'Number of Transactions'])
        writer.writerow([
            data['address'],
            data['final_balance'],
            data['total_received'],
            data['total_sent'],
            data['n_tx']
        ])
    
    return output.getvalue()
