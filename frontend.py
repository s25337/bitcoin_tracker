import streamlit as st
import requests
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Śledzenie transakcji Bitcoin")

txid = st.text_input("Podaj TXID", "")
mode = st.radio("Tryb analizy", ["Wyjścia", "Wejścia", "Całość"])

endpoint_map = {
    "Wyjścia": f"http://127.0.0.1:5000/trace/{txid}",
    "Wejścia": f"http://127.0.0.1:5000/trace-inputs/{txid}",
    "Całość": None
}

if txid and st.button("🔎 Analizuj"):
    try:
        if mode == "Całość":
            inputs = requests.get(f"http://127.0.0.1:5000/trace-inputs/{txid}").json()
            outputs = requests.get(f"http://127.0.0.1:5000/trace/{txid}").json()
            data = {**inputs}
            for k, v in outputs.items():
                data.setdefault(k, []).extend(v)
        else:
            endpoint = endpoint_map[mode]
            response = requests.get(endpoint)
            response.raise_for_status()
            data = response.json()

        G = nx.DiGraph()
        edge_labels = {}
        node_colors = {}

        for src, targets in data.items():
            src_clean, src_val = (src.split("@") + [""])[:2] if "@" in src else (src, "")
            for dst in targets:
                dst_clean, dst_val = (dst.split("@") + [""])[:2] if "@" in dst else (dst, "")

                G.add_edge(src_clean, dst_clean)
                value = dst_val or src_val
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

        fig, ax = plt.subplots(figsize=(10, 8))
        pos = nx.spring_layout(G, seed=42)
        colors = [node_colors.get(n, "gray") for n in G.nodes()]
        nx.draw(G, pos, with_labels=True, node_color=colors, edge_color="gray",
                node_size=900, font_size=8, arrows=True, ax=ax)
        if edge_labels:
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=7)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Błąd: {e}")
