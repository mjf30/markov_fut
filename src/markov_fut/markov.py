from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Tuple
from .state_definitions import construir_estados_do_evento

def construir_transicoes(events: List[dict], team_id_foco: int):
    counts: Dict[tuple[str,str], int] = defaultdict(int)
    seq: List[str] = []
    for ev in events:
        states = construir_estados_do_evento(ev, team_id_foco)
        for st in states:
            if seq:
                counts[(seq[-1], st)] += 1
            seq.append(st)

    totals = defaultdict(int)
    for (a,b), c in counts.items():
        totals[a] += c
    probs = {}
    for (a,b), c in counts.items():
        denom = totals[a]
        if denom>0: probs[(a,b)] = c/denom
    return dict(counts), probs

def agregar_e_normalizar(lista_counts: List[Dict[tuple[str,str], int]]):
    total_counts = defaultdict(int)
    for cnt in lista_counts:
        for k,v in cnt.items():
            total_counts[k] += v
    totals = defaultdict(int)
    for (a,b), c in total_counts.items():
        totals[a] += c
    probs = {}
    for (a,b), c in total_counts.items():
        denom = totals[a]
        if denom>0:
            probs[(a,b)] = c/denom
    return dict(total_counts), probs
