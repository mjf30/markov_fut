
from __future__ import annotations
import math
from typing import Dict, Tuple, List, Optional
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from collections import defaultdict

# ---- Grid config (D/M/A columns, P/S rows) ----
COL_X = {"D": 0.0, "M": 1.0, "A": 2.0}
ROW_Y = {"P": 0.0, "S": -1.0}
ACTION_OFFSET = {"PAS": (-0.22, 0.0), "FIN": (0.0, 0.22), "PER": (0.22, 0.0), "REC": (0.0, -0.22)}

# Node fill colors by action
ACTION_COLOR = {"PAS":"#3b82f6","FIN":"#f59e0b","PER":"#ef4444","REC":"#8b5cf6"}
# Edge color by possession relation
EDGE_COLOR   = {"PP":"#1f3b73","SS":"#7b3f82","PS":"#d45087","SP":"#2ca02c"}

# ---------- helpers ----------
def _parse_state(s: str):
    try:
        p, z, a = s.split("_", 2); return p, z, a
    except Exception:
        return None, None, None

def _edge_color(a: str, b: str) -> str:
    pa,_,_ = _parse_state(a); pb,_,_ = _parse_state(b)
    return EDGE_COLOR.get((pa or "") + (pb or ""), "#444444")

def _layout_positions(states, mirror_s: bool):
    pos = {}
    for s in states:
        P, Z, A = _parse_state(s)
        if P is None: continue
        x = COL_X.get(Z, 1.0)
        if mirror_s and P == "S":
            x = 2.0 - x
        y = ROW_Y.get(P, -1.0)
        dx, dy = ACTION_OFFSET.get(A, (0.0, 0.0))
        pos[s] = (x + dx, y + dy)
    return pos

def _counts_out(counts: Dict[Tuple[str,str], int]) -> Dict[str, int]:
    tot = defaultdict(int)
    for (a,b),c in counts.items():
        tot[a] += c; tot[b] += 0
    return tot

def _percentile(values: List[float], q: float) -> float:
    if not values: return 1.0
    values = sorted(values)
    idx = int(round((len(values)-1) * min(max(q,0.0),1.0)))
    return values[idx]

def _draw_background_grid(ax):
    for x in [0.0, 1.0, 2.0]:
        ax.axvline(x, color="#e6e6e6", lw=1.1, zorder=0)
    ax.axhline(-0.5, color="#e6e6e6", lw=1.1, zorder=0)
    for x, label in [(0.0,"D"), (1.0,"M"), (2.0,"A")]:
        ax.text(x, 0.52, label, ha="center", va="center", fontsize=14, color="#444", zorder=2)
    ax.text(-0.38,  0.00, "P", ha="center", va="center", fontsize=14, color="#444", zorder=2)
    ax.text(-0.38, -1.00, "S", ha="center", va="center", fontsize=14, color="#444", zorder=2)

def _shorten_segment(p0, p1, r0, r1):
    (x0,y0),(x1,y1) = p0, p1
    dx, dy = x1-x0, y1-y0
    L = math.hypot(dx,dy)
    if L < 1e-6: return p0, p1
    ux, uy = dx/L, dy/L
    return (x0+ux*r0, y0+uy*r0), (x1-ux*r1, y1-uy*r1)

def _filter_edges(
    probs: Dict[Tuple[str,str], float],
    prob_threshold: float,
    topk_per_node: Optional[int],
    counts: Optional[Dict[Tuple[str,str], int]] = None,
    min_count: int = 0,
) -> Dict[Tuple[str,str], float]:
    counts = counts or {}
    tot_out = _counts_out(counts)
    cand = []
    for (a,b), p in probs.items():
        if a == b:  # ignora loops aqui
            continue
        ce = counts.get((a,b), 0)
        if p >= prob_threshold and ce >= min_count:
            score = p * max(1, tot_out.get(a,0))
            cand.append(((a,b), p, ce, score))
    keep: Dict[Tuple[str,str], float] = {}
    from collections import defaultdict
    by_src = defaultdict(list)
    for e, p, ce, sc in cand:
        by_src[e[0]].append((e,p,ce,sc))
    for a, lst in by_src.items():
        lst.sort(key=lambda t: (-t[3], -t[1], -t[2]))
        chosen = lst if topk_per_node is None else lst[:topk_per_node]
        for e,p,ce,sc in chosen:
            keep[e] = p
    return keep

# ---------- API ----------
def plot_graph(
    probs: Dict[Tuple[str,str], float],
    out_png: str,
    prob_threshold: float = 0.08,
    threshold: Optional[float] = None,   # alias compatível
    topk_per_node: Optional[int] = 5,
    mirror_s: bool = True,
    title: Optional[str] = None,
    counts: Optional[Dict[Tuple[str,str], int]] = None,
    min_count: int = 0,
    node_radius_min: float = 0.050,
    node_radius_max: float = 0.090,
    loop_label_gap: float = 0.14,        # distância do rótulo de self-loop para fora do nó
    arrowsize_scale: float = 16.0,
) -> None:
    if threshold is not None:
        prob_threshold = float(threshold)

    states = sorted({a for (a,_b) in probs} | {b for (_a,b) in probs})
    pos = _layout_positions(states, mirror_s=mirror_s)

    # raios por volume (se counts fornecido)
    tot_out = _counts_out(counts or {})
    vols = [math.sqrt(max(1, tot_out.get(s, 0))) for s in states]
    p95 = max(_percentile(vols, 0.95), 1.0) if vols else 1.0
    radii = {}
    for s in states:
        t = min(math.sqrt(max(1, tot_out.get(s, 0))) / p95, 1.0)
        radii[s] = node_radius_min + t * (node_radius_max - node_radius_min)

    edges = _filter_edges(probs, prob_threshold, topk_per_node, counts=counts, min_count=min_count)

    fig = plt.figure(figsize=(20, 12))
    ax = plt.gca()
    _draw_background_grid(ax)

    # desenha nós
    for s in states:
        P, Z, A = _parse_state(s)
        x,y = pos[s]; r = radii[s]
        circ = Circle((x,y), r, facecolor=ACTION_COLOR.get(A,"#bbb"),
                      edgecolor="black", linewidth=0.7, alpha=0.97, zorder=2)
        ax.add_patch(circ)
        ax.text(x, y, s, ha="center", va="center", fontsize=9.5,
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.6), zorder=3)

    # self-loop labels (SEM desenhar aresta)
    def _loop_angle(zone: str, prefix: str) -> float:
        if zone == "D": return math.pi
        if zone == "A": return 0.0
        return math.pi/2 if prefix == "P" else -math.pi/2

    for s in states:
        p_loop = probs.get((s,s))
        if p_loop is None: 
            continue
        P, Z, _ = _parse_state(s)
        ang = _loop_angle(Z or "M", P or "P")
        x0,y0 = pos[s]; r = radii[s]
        lx = x0 + (r + loop_label_gap) * math.cos(ang)
        ly = y0 + (r + loop_label_gap) * math.sin(ang)
        ax.text(lx, ly, f"{p_loop:.2f}", ha="center", va="center", fontsize=8.5,
                bbox=dict(boxstyle="round,pad=0.16", facecolor="white", edgecolor="none", alpha=0.85), zorder=3.4)

    # arestas normais
    for (a,b), w in edges.items():
        start, end = _shorten_segment(pos[a], pos[b], radii[a], radii[b])
        col = _edge_color(a,b)
        patch = FancyArrowPatch(start, end,
                                connectionstyle="arc3,rad=0.05",
                                arrowstyle='-|>',
                                mutation_scale=arrowsize_scale,
                                linewidth=1.0 + 1.2*w,
                                color=col, alpha=0.86, zorder=1.6)
        ax.add_patch(patch)
        mx = (start[0]+end[0])/2.0; my = (start[1]+end[1])/2.0 + 0.026
        ax.text(mx, my, f"{w:.2f}", fontsize=8, color="#333", ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.10", facecolor="white", edgecolor="none", alpha=0.6), zorder=2.6)

    ax.set_xlim(-0.7, 2.7); ax.set_ylim(-1.6, 0.6); ax.axis("off")
    if title: plt.title(title, fontsize=16)
    plt.tight_layout(); plt.savefig(out_png, dpi=300); plt.close()
