
import requests

MEMPOOL_API = "https://mempool.space/api"

def get_block_by_height(height):
    url = f"{MEMPOOL_API}/block-height/{height}"
    response = requests.get(url)
    response.raise_for_status()
    return response.text  # zwraca hash bloku

def get_block_details(block_hash):
    url = f"{MEMPOOL_API}/block/{block_hash}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_block_txs(block_hash):
    url = f"{MEMPOOL_API}/block/{block_hash}/txids"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
