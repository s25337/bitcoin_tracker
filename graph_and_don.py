
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext

import matplotlib.pyplot as plt
import networkx as nx
import qrcode
import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from block_explorer import get_block_by_height, get_block_details, get_block_txs

# === RPC KONFIGURACJA ===
RPC_USER = "mojuser"
RPC_PASS = "mojehaslo"
RPC_PORT = 18332
RPC_URL = f"http://127.0.0.1:{RPC_PORT}/"

def rpc(method, params=[]):
    payload = {"jsonrpc": "1.0", "id": "btc", "method": method, "params": params}
    response = requests.post(RPC_URL, json=payload, auth=(RPC_USER, RPC_PASS))
    response.raise_for_status()
    return response.json()["result"]

# === ANALIZA TRANSAKCJI ===
def analyze_tx(mode, entry, frame):
    txid = entry.get().strip()
    if not txid:
        messagebox.showwarning("Błąd", "Podaj ID transakcji!")
        return

    endpoints = {
        "outputs": f"http://127.0.0.1:5000/trace/{txid}",
        "inputs": f"http://127.0.0.1:5000/trace-inputs/{txid}",
    }

    try:
        if mode == "full":
            inputs = requests.get(endpoints["inputs"]).json()
            outputs = requests.get(endpoints["outputs"]).json()
            data = {**inputs}
            for k, v in outputs.items():
                data.setdefault(k, []).extend(v)
        else:
            url = endpoints.get(mode)
            if not url:
                messagebox.showerror("Błąd", "Nieznany tryb.")
                return
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        messagebox.showerror("Błąd", f"Błąd pobierania danych:\n{e}")
        return

    G = nx.DiGraph()
    node_colors = {}
    edge_labels = {}

    for src, targets in data.items():
        src_clean, src_value = (src.split("@") + [""])[:2] if "@" in src else (src, "")
        for dst in targets:
            dst_clean, dst_value = (dst.split("@") + [""])[:2] if "@" in dst else (dst, "")
            G.add_edge(src_clean, dst_clean)

            value = dst_value or src_value
            if value:
                edge_labels[(src_clean, dst_clean)] = f"{value} BTC"

            if dst_clean.startswith(("1", "3", "bc1", "tb1")):
                node_colors[dst_clean] = "pink"
            elif len(dst_clean) == 64:
                node_colors[dst_clean] = "lightgreen"

            if len(src_clean) == 64:
                node_colors[src_clean] = "lightgreen"

    if txid in node_colors:
        node_colors[txid] = "skyblue"

    for widget in frame.winfo_children():
        widget.destroy()

    fig = plt.Figure(figsize=(11, 9), dpi=100)
    ax = fig.add_subplot(111)

    if mode == "full":
        shells = [[], [txid], []]
        for node in G.nodes():
            if node == txid:
                continue
            elif (node, txid) in G.edges:
                shells[0].append(node)
            elif (txid, node) in G.edges:
                shells[2].append(node)
            else:
                shells[1].append(node)
        pos = nx.shell_layout(G, shells)
    else:
        pos = nx.spring_layout(G, seed=42)

    color_list = [node_colors.get(n, "gray") for n in G.nodes()]
    nx.draw(G, pos, with_labels=True, ax=ax,
            node_color=color_list, edge_color='gray',
            node_size=1000, font_size=8, arrows=True)

    if edge_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=7)

    ax.set_title(f"Transakcja BTC: {txid} ({mode})")
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
# ===Fishy===
def show_suspicion():
    txid = entry_suspicion.get().strip()
    if not txid:
        messagebox.showwarning("Błąd", "Podaj ID transakcji!")
        return

    try:
        response = requests.get(f"http://127.0.0.1:5000/suspicion/{txid}")
        response.raise_for_status()
        result = response.json()
        score = result["score"]
        reasons = result["reasons"]

        suspicion_var.set(f"{score}% podejrzana")
        reasons_text.delete("1.0", tk.END)
        for r in reasons:
            reasons_text.insert(tk.END, f"- {r}\n")

    except Exception as e:
        messagebox.showerror("Błąd", str(e))
# == BLOK ===
def create_block_explorer_tab(notebook):
    tab4 = tk.Frame(notebook)
    notebook.add(tab4, text="Eksplorator bloków")

    top_frame = tk.Frame(tab4)
    top_frame.pack(pady=10)

    tk.Label(top_frame, text="Wysokość bloku:").pack(side=tk.LEFT)
    height_entry = tk.Entry(top_frame, width=20)
    height_entry.pack(side=tk.LEFT, padx=5)

    result_text = scrolledtext.ScrolledText(tab4, width=100, height=30)
    result_text.pack(pady=10, padx=10)

    def fetch_block_data():
        height_str = height_entry.get().strip()
        if not height_str.isdigit():
            messagebox.showerror("Błąd", "Wpisz prawidłową wysokość bloku (liczbę).")
            return
        try:
            block_hash = get_block_by_height(int(height_str))
            block_data = get_block_details(block_hash)
            txs = get_block_txs(block_hash)

            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, f"Hash: {block_data.get('id')}\n")
            result_text.insert(tk.END, f"Czas: {block_data.get('timestamp')}\n")
            result_text.insert(tk.END, f"Ilość transakcji: {block_data.get('tx_count')}\n")
            result_text.insert(tk.END, f"Rozmiar: {block_data.get('size')} B\n")
            result_text.insert(tk.END, f"Wysokość: {block_data.get('height')}\n")
            result_text.insert(tk.END, "-" * 60 + "\n")
            result_text.insert(tk.END, "Transakcje:\n")
            for txid in txs[:100]:
                result_text.insert(tk.END, f"{txid}\n")

        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    tk.Button(top_frame, text="Pobierz", command=fetch_block_data).pack(side=tk.LEFT, padx=5)

# === PORTFEL ===
def generate_wallet():
    return rpc("getnewaddress")

def generate_qr(address):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(address)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def fetch_received(address):
    try:
        return rpc("getreceivedbyaddress", [address])
    except:
        return 0

def track_and_display(address, label, listbox):
    def update():
        while True:
            amount = fetch_received(address)
            label.config(text=f"Otrzymano: {amount:.8f} BTC")
            if amount > 0:
                get_transaction_history(listbox, label)
            time.sleep(10)
    threading.Thread(target=update, daemon=True).start()

def get_transaction_history(listbox, label):
    try:
        txs = rpc("listtransactions", ["*", 10, 0, True])
        listbox.delete(0, tk.END)
        for tx in reversed(txs):
            if tx.get("category") == "receive":
                line = f"{tx['amount']:.8f} BTC | {tx['confirmations']} konf | {tx['txid'][:8]}..."
                listbox.insert(tk.END, line)
        label.config(text="✅ Historia załadowana")
    except Exception as e:
        label.config(text=f"❌ Błąd historii: {e}")

# === GUI ===
root = tk.Tk()
root.title("Bitcoin: Transakcje i Portfel")
root.geometry("1150x850")

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# === Zakładka 1: Transakcje ===
tab1 = tk.Frame(notebook)
notebook.add(tab1, text="Analiza transakcji")

top_frame = tk.Frame(tab1)
top_frame.pack(pady=10)

tk.Label(top_frame, text="Podaj ID transakcji:").pack(side=tk.LEFT)
entry = tk.Entry(top_frame, width=64)
entry.pack(side=tk.LEFT, padx=5)

btn_frame = tk.Frame(tab1)
btn_frame.pack(pady=5)

frame1 = tk.Frame(tab1)
frame1.pack(fill=tk.BOTH, expand=True)

tk.Button(btn_frame, text="Wyjścia", command=lambda: analyze_tx("outputs", entry, frame1)).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Wejścia", command=lambda: analyze_tx("inputs", entry, frame1)).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="Całość", command=lambda: analyze_tx("full", entry, frame1)).pack(side=tk.LEFT, padx=5)

# === Zakładka 2: Portfel i QR ===
tab2 = tk.Frame(notebook)
notebook.add(tab2, text="Odbieranie wpłat")

wallet_frame = tk.Frame(tab2)
wallet_frame.pack(pady=20)

tk.Label(wallet_frame, text="Donations").pack()

btc_address = generate_wallet()
img = generate_qr(btc_address)

fig2, ax2 = plt.subplots(figsize=(3, 3))
ax2.imshow(img, cmap='gray')
ax2.axis("off")
canvas2 = FigureCanvasTkAgg(fig2, master=wallet_frame)
canvas2.draw()
canvas2.get_tk_widget().pack()

tk.Label(wallet_frame, text=btc_address, font=("Courier", 9)).pack(pady=5)

status_label = tk.Label(wallet_frame, text="Oczekiwanie na wpłatę...", fg="blue")
status_label.pack(pady=5)

tk.Label(wallet_frame, text="Historia transakcji").pack()
tx_listbox = tk.Listbox(wallet_frame, width=60)
tx_listbox.pack(pady=5)
tk.Button(wallet_frame, text="Odśwież historię", command=lambda: get_transaction_history(tx_listbox, status_label)).pack(pady=3)

track_and_display(btc_address, status_label, tx_listbox)
 # == TAB 3
tab3 = tk.Frame(notebook)
notebook.add(tab3, text="Podejrzaność")

suspicion_top = tk.Frame(tab3)
suspicion_top.pack(pady=10)

tk.Label(suspicion_top, text="ID transakcji:").pack(side=tk.LEFT)
entry_suspicion = tk.Entry(suspicion_top, width=60)
entry_suspicion.pack(side=tk.LEFT, padx=5)
tk.Button(suspicion_top, text="Oblicz", command=show_suspicion).pack(side=tk.LEFT)

suspicion_var = tk.StringVar()
tk.Label(tab3, textvariable=suspicion_var, font=("Arial", 16)).pack(pady=10)

reasons_text = tk.Text(tab3, height=15, width=100)
reasons_text.pack(pady=10)

create_block_explorer_tab(notebook)

root.mainloop()
