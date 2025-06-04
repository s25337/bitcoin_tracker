import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import qrcode
import requests
from io import BytesIO
import time
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

RPC_USER = "mojuser"
RPC_PASS = "mojehaslo"
RPC_PORT = 18332
RPC_URL = f"http://127.0.0.1:{RPC_PORT}/"

def rpc(method, params=[]):
    payload = {
        "jsonrpc": "1.0",
        "id": "btc",
        "method": method,
        "params": params
    }
    response = requests.post(RPC_URL, json=payload, auth=(RPC_USER, RPC_PASS))
    response.raise_for_status()
    return response.json()["result"]

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
            label.config(text=f"💰 Otrzymano: {amount:.8f} BTC")
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
root.title("Bitcoin Donation")
root.geometry("500x700")

wallet_frame = tk.Frame(root)
wallet_frame.pack(pady=20)

tk.Label(wallet_frame, text="Donations").pack()

btc_address = generate_wallet()
img = generate_qr(btc_address)

fig, ax = plt.subplots(figsize=(3, 3))
ax.imshow(img, cmap='gray')
ax.axis("off")
canvas = FigureCanvasTkAgg(fig, master=wallet_frame)
canvas.draw()
canvas.get_tk_widget().pack()

tk.Label(wallet_frame, text=btc_address, font=("Courier", 9)).pack(pady=5)

status_label = tk.Label(wallet_frame, text="Oczekiwanie na wpłatę...", fg="blue")
status_label.pack(pady=5)

tk.Label(wallet_frame, text="Historia transakcji").pack()
tx_listbox = tk.Listbox(wallet_frame, width=60)
tx_listbox.pack(pady=5)

tk.Button(wallet_frame, text="Odśwież historię", command=lambda: get_transaction_history(tx_listbox, status_label)).pack(pady=3)

track_and_display(btc_address, status_label, tx_listbox)

root.mainloop()
