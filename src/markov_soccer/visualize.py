from __future__ import annotations
from typing import Dict, Tuple
import networkx as nx
import matplotlib.pyplot as plt


def plot_graph(
    probs: Dict[tuple[str, str], float], out_png: str, threshold: float = 0.05
) -> None:
    G = nx.DiGraph()
    for (a, b), p in probs.items():
        if p >= threshold:
            G.add_edge(a, b, weight=p, label=f"{p:.2f}")
    pos = nx.spring_layout(G, seed=42, k=1.5)
    plt.figure(figsize=(16, 12))
    nx.draw_networkx_nodes(G, pos, node_size=500)
    nx.draw_networkx_labels(G, pos, font_size=8)
    nx.draw_networkx_edges(G, pos, arrows=True)
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=nx.get_edge_attributes(G, "label"), font_size=7
    )
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()
