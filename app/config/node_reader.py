import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class Node:
    nodes: List[str]
    query: Dict[str, Any]
    params: Dict[str, Any]

class NodeReader:
    def __init__(self) -> None:
        current = os.getcwd()
        self.path = os.path.join(current, "nodes.json")
        self.nodes: List[Node] = []

    @property
    def data(self) -> List[Node]:
        return self.nodes

    @data.setter
    def data(self, value: List[Node]) -> None:
        self.nodes = value

    @staticmethod
    def reader():
        try:
            current = os.path.dirname(os.path.abspath(__file__))
            node_path = os.path.join(current, 'nodes.json')
            if not os.path.exists(node_path):
                raise FileNotFoundError(f"Config file not found at: {node_path}")

            with open(node_path, 'r') as f:
                content = json.load(f)
            return content
        except Exception as e:
            print(f"Failed to NodeReader: {str(e)}")
            raise

    @classmethod
    def get_nodes(cls) -> List[Node]:
        reader = cls.reader()
        nodes = reader.get('nodes')
        if not nodes:
            raise ValueError("No nodes found in config file")
        return nodes

    @classmethod
    def get_query(cls, _Query: str) -> Optional[str]:
        """
        Standard queries:
        - address
        - tx
        - block
        - blockIndex
        """
        query_standard = ["address", "tx", "block", "blockIndex"]
        if _Query not in query_standard:
            raise ValueError(f"Invalid query type: {_Query}")
        reader = cls.reader()
        _query = reader.get('query')
        if not _query:
            raise ValueError("No nodes found in config file")
        return _query.get(_Query)

    @classmethod
    def get_params(cls) -> Dict[str, Any]:
        reader = cls.reader()
        params = reader.get('params')
        if not params:
            raise ValueError("No nodes found in config file")
        return params

    @classmethod
    def get_addr_params(cls, method: str) -> Optional[str]:
        """params for address endpoint
        Standard methods:
        - basic # return address details without txs details
        - txs # return address details with txs all details
        - txsLight # return address details with txid and vin and vout
        - txLight # return address details with txid only
        """
        params = cls.get_params()
        addr = params.get('addr')
        if not addr:
            raise ValueError("No address params found in config file")
        return addr.get(method)

# Example Usage:
# nodereader = NodeReader()
# nodes = nodereader.get_nodes()
# print(nodes)
# addr_query = nodereader.get_query('address')
# tx_query = nodereader.get_query('tx')
# block_query = nodereader.get_query('block')
# block_index_query = nodereader.get_query('blockIndex')
# addr_params = nodereader.get_addr_params('basic')
# tx_params = nodereader.get_addr_params('txs')
# tx_light_params = nodereader.get_addr_params('txsLight')