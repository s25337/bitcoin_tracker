import tkinter as tk
from tkinter import messagebox
import requests
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def analyze_tx(mode):
    txid = entry.get().strip()
    if not txid:
        messagebox.showwarning("Błąd", "Podaj ID transakcji!")
        return

    endpoints = {
        "outputs": f"http://127.0.0.1:5000/trace/{txid}",
        "inputs": f"http://127.0.0.1:5000/trace-inputs/{txid}",
        "full": None  # całość zbudujemy lokalnie
    }

    if mode == "full":
        try:
            inputs = requests.get(endpoints["inputs"]).json()
            outputs = requests.get(endpoints["outputs"]).json()
            data = {**inputs}
            for k, v in outputs.items():
                data.setdefault(k, []).extend(v)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się pobrać danych: {e}")
            return
    else:
        url = endpoints.get(mode)
        if not url:
            messagebox.showerror("Błąd", "Nieznany tryb.")
            return

        try:
            response = requests.get(url)
            if response.status_code != 200:
                error = response.json().get("error", "Błąd backendu")
                messagebox.showerror("Błąd", f"{error}")
                return
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
                node_colors[dst_clean] = "pink"  # wyjścia
            elif len(dst_clean) == 64:
                node_colors[dst_clean] = "lightgreen"  # transakcje wejściowe

            if len(src_clean) == 64:
                node_colors[src_clean] = "lightgreen"

    if txid in node_colors:
        node_colors[txid] = "skyblue"

    # Czyszczenie wykresu
    for widget in frame.winfo_children():
        widget.destroy()

    fig = plt.Figure(figsize=(11, 9), dpi=100)
    ax = fig.add_subplot(111)

    # Specjalny układ: wejścia – centrum – wyjścia
    if mode == "full":
        shells = [[], [txid], []]  # left, center, right

        for node in G.nodes():
            if node == txid:
                continue
            elif (node, txid) in G.edges:  # wejście
                shells[0].append(node)
            elif (txid, node) in G.edges:  # wyjście
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

# === GUI ===
root = tk.Tk()
root.title("Śledzenie transakcji Bitcoin")
root.geometry("1100x850")

top_frame = tk.Frame(root)
top_frame.pack(pady=10)

tk.Label(top_frame, text="Podaj ID transakcji:").pack(side=tk.LEFT)
entry = tk.Entry(top_frame, width=64)
entry.pack(side=tk.LEFT, padx=5)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="🔽 Wyjścia", command=lambda: analyze_tx("outputs")).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="🔼 Wejścia", command=lambda: analyze_tx("inputs")).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="🔁 Całość", command=lambda: analyze_tx("full")).pack(side=tk.LEFT, padx=5)

frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

root.mainloop()
