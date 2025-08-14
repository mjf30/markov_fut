from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, List, Iterable
from collections import defaultdict

from .state_definitions import construir_estado


@dataclass
class Transicoes:
    # contagens brutas e probabilidades normalizadas
    counts: Dict[tuple[str, str], int]
    probs: Dict[tuple[str, str], float]


def atualizar_placar(event: dict, gols_por_time: Dict[int, int]) -> None:
    # Marca gols quando "Shot" tem outcome "Goal" (ou own_goal)
    if (event.get("type") or {}).get("name") != "Shot":
        return
    shot = event.get("shot") or {}
    outcome = (shot.get("outcome") or {}).get("name")
    if outcome == "Goal":
        team_id = (event.get("team") or {}).get("id")
        if team_id is not None:
            gols_por_time[team_id] = gols_por_time.get(team_id, 0) + 1
    # Own goals no Open Data aparecem como "Own Goal For"/"Own Goal Against" em outros eventos,
    # mas para simplicidade consideramos acima apenas Shot->Goal.


def placar_relativo(event: dict, gols_por_time: Dict[int, int]) -> tuple[int, int]:
    team_id = (event.get("team") or {}).get("id")
    if team_id is None:
        return (0, 0)
    gols_time = gols_por_time.get(team_id, 0)
    # adversário: heurística simples pegando possession_team ou 'team' diferente
    poss_team = (event.get("possession_team") or {}).get("id")
    # Em geral, times em campo são apenas 2; pegamos qualquer id diferente que já apareceu
    ids = list(gols_por_time.keys())
    adv_ids = [i for i in ids if i != team_id]
    gols_adv = gols_por_time.get(adv_ids[0], 0) if adv_ids else 0
    return (gols_time, gols_adv)


def construir_transicoes(events: List[dict]) -> Transicoes:
    counts: Dict[tuple[str, str], int] = defaultdict(int)
    gols_por_time: Dict[int, int] = {}
    
    # Constrói uma única sequência de estados para todo o jogo
    estados_seq: List[str] = []
    for ev in events:
        atualizar_placar(ev, gols_por_time)
        rel = placar_relativo(ev, gols_por_time)
        est = construir_estado(ev, rel)
        if est is not None:
            estados_seq.append(est.key())

    # Conta transições sucessivas s_i -> s_{i+1}
    for i in range(len(estados_seq) - 1):
        a, b = estados_seq[i], estados_seq[i + 1]
        counts[(a, b)] += 1

    # Normalização por origem
    totals: Dict[str, int] = defaultdict(int)
    for (a, b), c in counts.items():
        totals[a] += c

    probs: Dict[tuple[str, str], float] = {}
    for (a, b), c in counts.items():
        denom = totals[a]
        if denom > 0:
            probs[(a, b)] = c / denom

    return Transicoes(counts=dict(counts), probs=probs)
