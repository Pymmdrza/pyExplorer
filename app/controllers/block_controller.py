import logging
from datetime import datetime
from typing import Optional, Dict, Any
from app.config.config_manager import config
from app.utils.api_client import make_request

logging.basicConfig(level=logging.INFO) # Add basic logging configuration


def get_block_details(block_height: str, page: int = 1, per_page: int = 10) -> Optional[Dict[str, Any]]:
    """Get detailed block information"""
    try:
        logging.info(f"Fetching block details for height: {block_height}")
        url = config.get_node_url('block') + str(block_height)
        block = make_request(url)

        if not block:
            logging.warning(f"No block data found for height: {block_height}")
            return None

        # Calculate total pages
        transactions = block.get('txs', []) or block.get('transactions', [])  # Try both keys
        if not isinstance(transactions, list):
            logging.warning(f"Invalid transactions data type: {type(transactions)}")
            transactions = []

        total_transactions = len(transactions)
        total_pages = (total_transactions + per_page - 1) // per_page if total_transactions > 0 else 1

        # Get a slice of transactions based on page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_transactions = transactions[start_idx:end_idx]

        logging.info(f"Successfully processed block data with {total_transactions} transactions")
        return {
            'hash': block.get('hash', ''),
            'height': int(block.get('height', 0)),
            'version': block.get('version', ''),
            'timestamp': datetime.fromtimestamp(int(block.get('time', 0))),
            'tx_count': total_transactions,
            'size': int(block.get('size', 0)),
            'merkle_root': block.get('merkleRoot', ''),
            'nonce': int(block.get('nonce', 0)),
            'bits': block.get('bits', ''),
            'difficulty': float(block.get('difficulty', 0)),
            'transactions': page_transactions,
            'current_page': page,
            'total_pages': total_pages
        }
    except Exception as e:
        logging.error(f"Error fetching block details: {str(e)}")
        return None

def get_blockchain_stats() -> Optional[Dict[str, Any]]:
    """Get general blockchain statistics"""
    try:
        logging.info("Fetching blockchain stats")
        response = make_request(config.get_stats_api())
        if not response:
            logging.warning("No blockchain stats data received")
            return None

        stats = {
            'market_price_usd': float(response.get('market_price_usd', 0)),
            'hash_rate': float(response.get('hash_rate', 0)),
            'total_fees_btc': float(response.get('total_fees_btc', 0)) / 1e8,
            'n_blocks_total': int(response.get('n_blocks_total', 0)),
            'n_blocks_mined': int(response.get('n_blocks_mined', 0)),
            'minutes_between_blocks': float(response.get('minutes_between_blocks', 0))
        }
        logging.info("Successfully retrieved blockchain stats")
        return stats
    except Exception as e:
        logging.error(f"Error fetching blockchain stats: {str(e)}")
        return None

def get_blockchain_metrics() -> Optional[Dict[str, Any]]:
    """Get blockchain metrics"""
    try:
        logging.info("Fetching blockchain metrics")
        metrics = {}

        # Get difficulty
        url = config.get_blockchain_api('difficulty')
        difficulty_response = make_request(url)
        if difficulty_response:
            try:
                metrics['difficulty'] = float(difficulty_response.get('text', 0))
            except ValueError as e:
                logging.error(f"Error parsing difficulty: {str(e)}")
                metrics['difficulty'] = 0

        # Get 24h transaction count
        url = config.get_blockchain_api('txCount24h')
        tx_count_response = make_request(url)
        if tx_count_response:
            try:
                metrics['tx_24h'] = int(float(tx_count_response.get('text', 0)))
            except ValueError as e:
                logging.error(f"Error parsing transaction count: {str(e)}")
                metrics['tx_24h'] = 0

        if any(metrics.values()):
            logging.info("Successfully retrieved blockchain metrics")
            return metrics

        logging.warning("No valid metrics data received")
        return None

    except Exception as e:
        logging.error(f"Error fetching blockchain metrics: {str(e)}")
        return None