# === backend/app.py ===
import traceback
from flask import Flask, jsonify
import requests

app = Flask(__name__)

MEMPOOL_BASE_URL = "https://mempool.space/api"

def get_tx_details(txid):
    url = f"{MEMPOOL_BASE_URL}/tx/{txid}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

def get_address_txs(address):
    url = f"{MEMPOOL_BASE_URL}/address/{address}/txs"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

def trace_funds(txid, depth=1):  #  nie zmieniamy
    visited_tx = set()
    visited_addresses = set()
    graph = {}

    def recurse(current_txid, level):
        if level > 1:  #!!!
            return
        if current_txid in visited_tx:
            return

        visited_tx.add(current_txid)
        print(f"[DEPTH {level}] odwiedzam TX: {current_txid}")

        try:
            tx = get_tx_details(current_txid)
        except Exception as e:
            print(f"Błąd pobierania {current_txid}: {e}")
            return

        graph[current_txid] = []

        # --- WYJŚCIA ---
        for out in tx.get("vout", []):
            address = out.get("scriptpubkey_address")
            if not address:
                continue
            graph[current_txid].append(address)

            if address in visited_addresses:
                continue
            visited_addresses.add(address)

            if level < 1:
                try:
                    address_txs = get_address_txs(address)[:3]
                    for atx in address_txs:
                        next_txid = atx.get("txid")
                        if next_txid and next_txid != current_txid:
                            recurse(next_txid, level + 1)
                except Exception as e:
                    print(f"⚠️ Błąd przy adresie {address}: {e}")
                    continue

        # --- WEJŚCIA ---
        if level < 1:
            for vin in tx.get("vin", []):
                prev_txid = vin.get("txid")
                if not prev_txid:
                    continue
                if prev_txid not in graph:
                    graph[prev_txid] = []
                graph[prev_txid].append(current_txid)
                recurse(prev_txid, level + 1)

    recurse(txid, 0)
    print(f"Zbudowano graf z {len(graph)} węzłami (max depth 1)")
    return graph
def trace_inputs(txid):
    visited_tx = set()
    graph = {}

    def recurse(current_txid, level):
        if level > 1 or current_txid in visited_tx:
            return
        visited_tx.add(current_txid)

        try:
            tx = get_tx_details(current_txid)
        except Exception as e:
            print(f"Błąd pobierania TX {current_txid}: {e}")
            return

        graph[current_txid] = []

        if level < 1:
            for vin in tx.get("vin", []):
                prev_txid = vin.get("txid")
                vout_index = vin.get("vout")
                if not prev_txid or vout_index is None:
                    continue

                try:
                    prev_tx = get_tx_details(prev_txid)
                    prev_vout = prev_tx.get("vout", [])[vout_index]
                    value_btc = prev_vout.get("value", 0) / 100_000_000
                    label = f"{prev_txid}@{value_btc:.8f}"
                except Exception as e:
                    print(f"Nie udało się pobrać wartości dla {prev_txid}: {e}")
                    label = prev_txid

                graph.setdefault(label, []).append(current_txid)

    recurse(txid, 0)
    return graph


# Endpoint API
@app.route("/trace/<txid>", methods=["GET"])
def trace(txid):
    try:
        tx = get_tx_details(txid)

        if "vout" not in tx:
            return jsonify({"error": "Brak vout"}), 400

        graph = {txid: []}

        for out in tx["vout"]:
            address = out.get("scriptpubkey_address")
            value = out.get("value", 0) / 100_000_000  # satoshi -> BTC

            if address:
                label = f"{address}@{value:.8f}"
                graph[txid].append(label)

        return jsonify(graph)

    except Exception as e:
        print("=== ERROR in /trace ===")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/trace-inputs/<txid>", methods=["GET"])
def trace_inputs_endpoint(txid):
    try:
        graph = trace_inputs(txid)
        return jsonify(graph)
    except Exception as e:
        print("=== ERROR in /trace-inputs ===")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
