# === backend/app.py ===
import traceback
from pickle import GET

from flask import Flask, jsonify
import requests

app = Flask(__name__)

MEMPOOL_BASE_URL = "https://mempool.space/api"

def get_tx_details(txid):
    url = f"{MEMPOOL_BASE_URL}/tx/{txid}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_address_txs(address):
    url = f"{MEMPOOL_BASE_URL}/address/{address}/txs"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def trace_funds(txid, depth=2):
    visited = set()
    graph = {}

    def recurse(txid, level):
        if level > depth or txid in visited:
            return
        visited.add(txid)
        tx = get_tx_details(txid)
        outputs = tx.get("vout", [])
        graph[txid] = []
        for out in outputs:
            address = out.get("scriptpubkey_address")
            if address:
                graph[txid].append(address)
                # Get txs for this address
                address_txs = get_address_txs(address)
                for atx in address_txs:
                    if atx["txid"] != txid:
                        recurse(atx["txid"], level + 1)

    recurse(txid, 0)
    return graph


@app.route("/trace/<txid>", methods=["GET"])
def trace(txid):
    try:
        url = f"https://mempool.space/api/tx/{txid}"
        response = requests.get(url)
        if response.status_code != 200:
            print("Response content:", response.text)
            return jsonify({"error": f"Upstream API returned {response.status_code}"}), 502
        tx_data = response.json()

        if "vin" not in tx_data or "vout" not in tx_data:
            return jsonify({"error": "Invalid transaction format"}), 400

        graph = {}

        # Dodaj główny tx
        graph[txid] = []

        for out in tx_data["vout"]:
            addr = out.get("scriptpubkey_address", "unknown")
            graph[txid].append(addr)

        return jsonify(graph)

    except Exception as e:
        print("=== ERROR in /trace ===")
        traceback.print_exc()  # wypisuje pełny stack trace w konsoli
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)