import tkinter as tk
from tkinter import messagebox

import matplotlib
import networkx as nx
import matplotlib.pyplot as plt
import json
import os
matplotlib.use("TkAgg")
MOCK_DIR = "mock_data"

def load_mock_tx(txid):
    path = os.path.join(MOCK_DIR, f"{txid}.json")
    with open(path, "r") as f:
        return json.load(f)

def load_mock_address(address):
    path = os.path.join(MOCK_DIR, f"{address}.json")
    with open(path, "r") as f:
        return json.load(f)

def trace_funds(txid, depth=1):
    visited = set()
    graph = {}

    def recurse(txid, level):
        if level > depth or txid in visited:
            return
        visited.add(txid)
        try:
            tx = load_mock_tx(txid)
        except FileNotFoundError:
            return
        outputs = tx.get("vout", [])
        graph[txid] = []
        for out in outputs:
            addr = out.get("scriptpubkey_address")
            if addr:
                graph[txid].append(addr)
                try:
                    addr_txs = load_mock_address(addr)
                    for atx in addr_txs:
                        if atx["txid"] != txid:
                            recurse(atx["txid"], level + 1)
                except FileNotFoundError:
                    continue

    recurse(txid, 0)
    return graph

def draw_graph(graph_data):
    G = nx.DiGraph()
    for txid, targets in graph_data.items():
        for addr in targets:
            G.add_edge(txid, addr)

    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, k=0.5)
    nx.draw(G, pos, with_labels=True, node_size=1500, node_color="lightblue", font_size=8, arrows=True)
    plt.title("Mock: Bitcoin Transaction Graph")
    plt.show()

def on_submit():
    txid = entry.get().strip()
    if not txid:
        messagebox.showerror("Błąd", "Podaj ID transakcji.")
        return
    try:
        graph_data = trace_funds(txid, depth=1)
        if not graph_data:
            messagebox.showinfo("Info", "Nie znaleziono transakcji.")
            return
        draw_graph(graph_data)
    except Exception as e:
        messagebox.showerror("Błąd", str(e))

# === GUI ===
root = tk.Tk()
root.title("Śledzenie transakcji Bitcoin (Offline)")

tk.Label(root, text="Podaj ID transakcji:").pack(padx=10, pady=5)
entry = tk.Entry(root, width=50)
entry.pack(padx=10, pady=5)

submit_btn = tk.Button(root, text="Analizuj", command=on_submit)
submit_btn.pack(pady=10)

root.mainloop()
