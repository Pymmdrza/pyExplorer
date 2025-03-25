import json
import os
import logging
from typing import Dict, List, Optional, Any


class ConfigException(Exception):
    pass


class ConfigManager:
    
    def __init__(self):
        """
        Initialize ConfigManager instance.

        This method will look for a config file named 'config.json' in the same
        directory as this file. If the file does not exist, a FileNotFoundError
        exception will be raised. The config file should contain a JSON object
        with the following structure:

        {
            "nodes": {
                <node_name>: {
                    "api": {
                        "base": <base_url>,
                        "addr": {
                            "prefix": <address_prefix>,
                            "suffix": {
                                "basic": <basic_suffix>,
                                "txs": <transactions_suffix>,
                                "txslight": <light_transactions_suffix>
                            }
                        },
                        "blockIndex": <block_index_suffix>,
                        "block": <block_suffix>,
                        "tx": <transaction_suffix>
                    }
                }
            }
        }

        The config file should contain at least one node definition. The
        current node is set to the first node in the config file.

        :raises FileNotFoundError: If the config file does not exist
        :raises Exception: If there is an error loading the config file
        """
        try:
            current = os.path.dirname(os.path.abspath(__file__))
            
            config_path = os.path.join(current, 'config.json')

            logging.info(f"Looking for config file at: {config_path}")

            if not os.path.exists(config_path):
                logging.error(f"Config file not found at: {config_path}")
                raise FileNotFoundError(f"Config file not found at: {config_path}")

            with open(config_path, 'r') as f:
                self.config = json.load(f)
                logging.info("Config file loaded successfully")

            self.current_node = 'atomic'
            self._initialize_api_nodes()
        except Exception as e:
            logging.error(f"Failed to initialize ConfigManager: {str(e)}")
            raise

    def _initialize_api_nodes(self):
        """
        Initialize API nodes from config.json and set default node to atomic
        
        Raises:
            KeyError: If required configuration key is missing
        """
        
        try:
            self.api_nodes = {
                'atomic': self.config['bitcoin']['node']['api']['atomic'],
                'guarda': self.config['bitcoin']['node']['api']['guarda'],
                'trezor': self.config['bitcoin']['node']['api']['trezor']
            }
            
            nodes = list(self.api_nodes.keys())
            self.current_node = nodes[0]
            logging.info(f"API nodes initialized, using {self.current_node} as default")
        except KeyError as e:
            logging.error(f"Missing required configuration key: {str(e)}")
            raise

    def get_node_url(self, endpoint_type: str) -> str:
        """
        Get the URL for a specific node and endpoint type.

        Args:
            endpoint_type: The type of endpoint to retrieve the URL for.
                One of 'address', 'block', 'blockIndex', or 'tx'.

        Returns:
            The constructed URL for the given endpoint type.

        Raises:
            ValueError: If the given endpoint_type is not recognized.
        """
        if not self.current_node:
            logging.error("No node selected")
            raise ValueError("No node selected")

        try:
            node = self.api_nodes[self.current_node]
            if endpoint_type == 'address':
                return node['base'] + node['addr']['prefix']
            elif endpoint_type in ['block', 'blockIndex', 'tx']:
                return node['base'] + node[endpoint_type]

            raise ValueError(f"Unknown endpoint type: {endpoint_type}")
        except KeyError as e:
            logging.error(f"Missing configuration for endpoint {endpoint_type}: {str(e)}")
            raise

    def get_node_suffix(self, endpoint_type: str, detail_level: str = 'basic') -> str:
        """Get suffix for address endpoints based on detail level"""
        if endpoint_type != 'address':
            return ''

        try:
            node = self.api_nodes[self.current_node]
            return node['addr']['suffix'].get(detail_level, '')
        except KeyError as e:
            logging.error(f"Error getting suffix for {endpoint_type}: {str(e)}")
            return ''

    def fallback_to_next_node(self) -> bool:
        """Switch to next available node if current one fails"""
        try:
            nodes = list(self.api_nodes.keys())
            current_index = nodes.index(self.current_node)
            next_index = (current_index + 1) % len(nodes)

            if nodes[next_index] == self.current_node:
                logging.warning("No more nodes available for fallback")
                return False

            self.current_node = nodes[next_index]
            logging.info(f"Switched to node: {self.current_node}")
            return True
        except Exception as e:
            logging.error(f"Error during node fallback: {str(e)}")
            return False

    def get_blockchain_api(self, endpoint: str) -> str:
        
        """
        Get a full URL for a blockchain API endpoint.

        Args:
            endpoint (str): The name of the endpoint, one of 'difficulty', 'blockcount', 'latestHash', 'bcPerBlock', 'totalBc', 'probability', 'hashesWin', 'nextReTarget', 'avgTxSize', 'avgTxValue', 'interval', 'eta', 'avgTxNum', 'addrToHash', 'hashToAddr', 'pubToAddr', 'addrToPub', 'txTotalBcOutput', 'txTotalBcInput', 'txFee', 'unconfirmedCount', 'price24h', 'marketcap', 'txCount24h', 'btcSent24h', 'hashRate', 'mempoolSize', 'difficulty24h', 'blockInterval'.

        Returns:
            str: The full URL of the API endpoint.

        Raises:
            ValueError: If the endpoint name is unknown.
            KeyError: If the configuration for the endpoint is missing.
        """
        try:
            base = self.config['bitcoin']['blockchain']['base']
            if endpoint in self.config['bitcoin']['blockchain']['main']:
                return base + self.config['bitcoin']['blockchain']['main'][endpoint]
            elif endpoint in self.config['bitcoin']['blockchain']['tools']:
                return base + self.config['bitcoin']['blockchain']['tools'][endpoint]
            elif endpoint in self.config['bitcoin']['blockchain']['lookups']:
                return base + self.config['bitcoin']['blockchain']['lookups'][endpoint]
            elif endpoint in self.config['bitcoin']['blockchain']['misc']:
                return base + self.config['bitcoin']['blockchain']['misc'][endpoint]

            raise ValueError(f"Unknown blockchain API endpoint: {endpoint}")
        except KeyError as e:
            logging.error(f"Missing blockchain API configuration: {str(e)}")
            raise

    def get_stats_api(self) -> str:
        """Get blockchain stats API endpoint"""
        try:
            return self.config['bitcoin']['blockchain']['state']
        except KeyError as e:
            logging.error(f"Missing stats API configuration: {str(e)}")
            raise

    def get_addr_api(self, level: str = 'basic'):
        """
        Get the API endpoint for the current node, with the given level of detail.

        Args:
            level (str): The level of detail to get, one of 'basic', 'txs', or 'txslight'.

        Returns:
            str: The API endpoint.

        Raises:
            ConfigException: If the configuration is missing or incorrect.
        """
        try:
            node = self.api_nodes[self.current_node]
            base_url = node['base'] + node['addr']['prefix']
            suffix = node['addr']['suffix'].get(level, '')
            return base_url + suffix
        except KeyError as e:
            logging.error("Missing configuration for address endpoint or suffix: %s, error: %s", level, str(e)) # Use custom logger
            raise ConfigException(f"Missing configuration for address endpoint or suffix: {str(e)}") from e
        except TypeError as e:
            logging.error("Configuration structure error for node: %s, error: %s", self.current_node, str(e)) # Use custom logger
            raise ConfigException(f"Configuration structure error for node {self.current_node}: {str(e)}")
        
 # Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)   
    
        

# Create global instance
config = ConfigManager()