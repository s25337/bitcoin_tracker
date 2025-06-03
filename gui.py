import tkinter as tk
from tkinter import messagebox
import requests
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


def analyze_tx():
    txid = entry.get().strip()
    if not txid:
        messagebox.showwarning("Błąd", "Podaj ID transakcji!")
        return

    try:
        response = requests.get(f"http://127.0.0.1:5000/trace/{txid}")
        response.raise_for_status()
        data = response.json()

        G = nx.DiGraph()
        for tx, addresses in data.items():
            for addr in addresses:
                G.add_edge(tx, addr)

        # Wyczyść stare płótno, jeśli istnieje
        for widget in frame.winfo_children():
            widget.destroy()

        fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, with_labels=True, ax=ax,
                node_color='lightblue', edge_color='gray',
                font_size=8, node_size=800)
        ax.set_title(f"Graf transakcji: {txid}", fontsize=10)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Błąd", f"Połączenie z API:\n{e}")
    except Exception as e:
        messagebox.showerror("Błąd", f"Nieoczekiwany błąd:\n{e}")


# === GUI ===
root = tk.Tk()
root.title("Śledzenie transakcji Bitcoin")
root.geometry("900x700")

top_frame = tk.Frame(root)
top_frame.pack(pady=10)

tk.Label(top_frame, text="Podaj ID transakcji:").pack(side=tk.LEFT)
entry = tk.Entry(top_frame, width=60)
entry.pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Analizuj", command=analyze_tx).pack(side=tk.LEFT)

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

root.mainloop()
