import tkinter as tk
from tkinter import messagebox
import qrcode
from PIL import Image, ImageTk
import requests
import time
import threading

#rpc
RPC_URL = "http://127.0.0.1:18332/"  # testnet port
RPC_USER = "mojuser"
RPC_PASS = "mojehaslo"


import requests  # ← ten import musi być

def rpc(method, params=[]):
    payload = {
        "jsonrpc": "1.0",
        "id": "wallet",
        "method": method,
        "params": params
    }
    response = requests.post(RPC_URL, json=payload, auth=(RPC_USER, RPC_PASS))
    response.raise_for_status()
    return response.json()["result"]

def generate_qr(address):
    qr = qrcode.make(f"bitcoin:{address}")
    qr.save("qr.png")

def fetch_transactions(address, label):
    try:
        amount = rpc("getreceivedbyaddress", [address, 0])
        label.config(text=f"Otrzymano: {amount:.8f} BTC")
    except Exception as e:
        label.config(text=f"Błąd: {e}")

def periodic_check(address, label, interval=10):
    def loop():
        while True:
            fetch_transactions(address, label)
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()

#gui
root = tk.Tk()
root.title("Donation")
root.geometry("400x500")

title = tk.Label(root, text="Twój adres BTC:", font=("Helvetica", 14))
title.pack(pady=10)

try:
    address = rpc("getnewaddress")
except Exception as e:
    messagebox.showerror("Błąd RPC", str(e))
    root.destroy()
    exit()

addr_label = tk.Label(root, text=address, font=("Courier", 10), wraplength=350)
addr_label.pack(pady=5)

generate_qr(address)
qr_img = Image.open("qr.png").resize((200, 200))
qr_photo = ImageTk.PhotoImage(qr_img)

img_label = tk.Label(root, image=qr_photo)
img_label.image = qr_photo
img_label.pack(pady=10)

status_label = tk.Label(root, text="Oczekiwanie na transakcję...", font=("Helvetica", 12))
status_label.pack(pady=15)

periodic_check(address, status_label, interval=15)

root.mainloop()
