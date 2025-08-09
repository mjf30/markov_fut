"""
plotting.py — Funções de visualização aprimoradas.
Usa matplotlib, mplsoccer e networkx para criar visualizações ricas em informações.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import seaborn as sns

def plot_recovery_heatmap(df: pd.DataFrame, outpath: str | Path) -> None:
    """Gera um heatmap de onde as recuperações de bola ('Ball Recovery') ocorrem."""
    recoveries = df[df["type"] == "Ball Recovery"].copy()
    if recoveries.empty:
        print("[plot] Nenhum evento 'Ball Recovery' encontrado para o heatmap.")
        return

    pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(10, 7))
    
    kde = pitch.kdeplot(
        x=recoveries['sx'], y=recoveries['sy'], ax=ax,
        fill=True, levels=100, thresh=0.0,
        cut=4, cmap='viridis'
    )
    
    ax.set_title("Heatmap de Recuperação de Posse (Ball Recovery)", color="white", fontsize=18)
    plt.savefig(outpath, dpi=300, bbox_inches='tight', facecolor='#22312b')
    plt.close(fig)
    print(f"[plot] Salvo heatmap de recuperação em {outpath}")

def plot_transition_graph(P: np.ndarray, state_index: dict, threshold: float, outpath: str | Path) -> None:
    """Plota um grafo de transições, com nós coloridos por 'role' e 'action'."""
    try:
        import networkx as nx
    except ImportError:
        print("[plot] networkx não instalado. `pip install networkx`. Pulando grafo.")
        return

    states = state_index["states"]
    state_map = {s["state_id"]: s for s in states}
    
    G = nx.from_numpy_array(P, create_using=nx.DiGraph)
    
    edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) if d['weight'] < threshold]
    G.remove_edges_from(edges_to_remove)
    G.remove_nodes_from(list(nx.isolates(G)))

    if not G.nodes:
        print(f"[plot] Nenhum nó no grafo com threshold={threshold}. Pulando.")
        return

    # Mapeamento de cores
    role_colors = {"atk": "skyblue", "def": "salmon"}
    action_palette = sns.color_palette("viridis", n_colors=len(set(s["action"] for s in states)))
    action_map = {action: color for action, color in zip(sorted(set(s["action"] for s in states)), action_palette)}

    node_colors = [role_colors.get(state_map[node]["role"], "lightgray") for node in G.nodes()]
    labels = {node: f'{state_map[node]["role"][:1]}:{state_map[node]["zone_id"]}:{state_map[node]["action"][:4]}' for node in G.nodes()}
    edge_weights = [d['weight'] for _, _, d in G.edges(data=True)]

    fig, ax = plt.subplots(figsize=(16, 16))
    pos = nx.spring_layout(G, seed=42, k=1.1)
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800, ax=ax, alpha=0.8)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_color="black", ax=ax)
    nx.draw_networkx_edges(
        G, pos, width=[w * 10 for w in edge_weights],
        edge_color='gray', alpha=0.6,
        arrows=True, arrowstyle='->', arrowsize=20, ax=ax
    )
    
    ax.set_title(f"Grafo de Transições (P >= {threshold})", fontsize=20)
    plt.axis('off')
    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"[plot] Salvo grafo de transições em {outpath}")

def plot_flip_kernel_heatmap(flips_df: pd.DataFrame, state_index: dict, outpath: str | Path) -> None:
    """Plota um heatmap do kernel de flip: da zona de perda (atk) para a de recuperação (def)."""
    if flips_df.empty:
        print("[plot] Nenhum 'flip' encontrado para o kernel heatmap.")
        return

    states = state_index["states"]
    state_map = {s["state_id"]: s for s in states}
    
    df = flips_df.copy()
    df['from_zone'] = df['from_id'].map(lambda i: state_map.get(i, {}).get('zone_id'))
    df['to_zone'] = df['to_id'].map(lambda i: state_map.get(i, {}).get('zone_id'))
    
    # Apenas flips de ataque para defesa
    df = df.dropna(subset=['from_zone', 'to_zone'])
    df = df[df['from_id'].map(lambda i: state_map.get(i, {}).get('role')) == 'atk']
    df = df[df['to_id'].map(lambda i: state_map.get(i, {}).get('role')) == 'def']

    if df.empty:
        print("[plot] Nenhum flip 'atk' -> 'def' encontrado para o kernel.")
        return

    kernel = df.groupby(['from_zone', 'to_zone'])['count'].sum().unstack(fill_value=0)
    
    # Normalizar por linha (de onde a bola foi perdida)
    kernel_norm = kernel.div(kernel.sum(axis=1), axis=0).fillna(0)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(kernel_norm, annot=True, fmt=".2f", cmap="viridis", ax=ax, linewidths=.5)
    
    ax.set_title("Kernel de Flip Normalizado (Zona de Perda -> Zona de Recuperação)", fontsize=16)
    ax.set_xlabel("Zona de Recuperação (Time Defensor)", fontsize=12)
    ax.set_ylabel("Zona de Perda (Time Atacante)", fontsize=12)
    plt.tight_layout()
    
    plt.savefig(outpath, dpi=300)
    plt.close(fig)
    print(f"[plot] Salvo heatmap do kernel de flip em {outpath}")

# FIM
