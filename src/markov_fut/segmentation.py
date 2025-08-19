
from __future__ import annotations
from typing import Dict, Tuple, Iterable, Optional
from collections import defaultdict

STOP_EVENTS = {
    "Foul Committed", "Out", "Offside", "Half End", "Period End",
    "Injury Stoppage", "Referee Ball-Drop", "Substitution"
}
RESTART_PASS_TYPES = {"Free Kick","Corner","Throw-in","Goal Kick","Kick Off"}

def _map_zone(loc):
    x = (loc or [60, 40])[0]
    if x < 40: return "D"
    if x < 70: return "M"
    return "A"

def _base_action(ev: dict) -> str:
    et = ev.get("type",{}).get("name")
    if et == "Shot": return "FIN"
    if et == "Ball Recovery": return "REC"
    if et in {"Dispossessed","Miscontrol"}: return "PER"
    if et == "Pass": return "PAS"
    return "PAS"

def _is_stop(ev: dict) -> bool:
    return ev.get("type", {}).get("name") in STOP_EVENTS

def _is_restart(ev: dict) -> bool:
    if ev.get("type", {}).get("name") != "Pass":
        return False
    ptype = ev.get("pass", {}).get("type", {}).get("name")
    return ptype in RESTART_PASS_TYPES

def _prefix_for(ev: dict, my_team_id: Optional[int]) -> str:
    team_id = ev.get("team", {}).get("id")
    if my_team_id is None: return "P"
    return "P" if team_id == my_team_id else "S"

def _iter_states(events, my_team_id: Optional[int]):
    for ev in events:
        act = _base_action(ev)
        z = _map_zone(ev.get("location"))
        pref = _prefix_for(ev, my_team_id)
        yield f"{pref}_{z}_{act}", ev

def build_transitions_for_match(
    events: Iterable[dict],
    my_team_id: Optional[int] = None,
    cut_on_stop: bool = True,
    coerce_turnovers: bool = True,
    collapse_set_piece: bool = True,
) -> Dict[Tuple[str,str], int]:
    """
    - cut_on_stop=True: encerra cadeia em STOP e no reinício subsequente.
    - cut_on_stop=False: não zera prev_state nem no STOP nem no RESTART; "cola" 1->reinício.
    - coerce_turnovers: força PER/REC em troca de posse viva.
    """
    transitions: Dict[Tuple[str,str], int] = defaultdict(int)

    events = list(events)
    events.sort(key=lambda e: (
        e.get("period", 0),
        e.get("minute", 0),
        e.get("second", 0),
        e.get("index", 0),
    ))

    prev_state = None
    prev_poss_team = None
    live = False

    for state, ev in _iter_states(events, my_team_id=my_team_id):
        if _is_stop(ev):
            # Quando corta em STOP, encerramos o segmento.
            # Quando NÃO corta, mantemos prev_state para colar com o próximo evento.
            if cut_on_stop:
                prev_state = None
                live = False
            prev_poss_team = ev.get("possession_team", {}).get("id")
            continue

        restart = _is_restart(ev)
        if restart:
            if cut_on_stop:
                # Reinício inicia novo segmento e não liga com anterior
                prev_state = None
                live = True
            else:
                # Não cortar: mantém prev_state para colar 1 -> reinício
                live = True
        elif not live:
            live = True
            # só zeramos prev_state aqui se a política for "cortar" (começo de jogo depois de um stop)
            if cut_on_stop:
                prev_state = None

        poss_team = ev.get("possession_team", {}).get("id")
        curr_state = state

        # turnover vivo (sem parada entre os eventos)
        if prev_state is not None and coerce_turnovers:
            if prev_poss_team is not None and poss_team != prev_poss_team:
                pp, pz, pa = prev_state.split("_", 2)
                if pa not in {"PER","FIN"}:
                    prev_state = f"{pp}_{pz}_PER"
                cp, cz, ca = curr_state.split("_", 2)
                if ca != "FIN":
                    curr_state = f"{cp}_{cz}_REC"

        if prev_state is not None:
            transitions[(prev_state, curr_state)] += 1

        prev_state = curr_state
        prev_poss_team = poss_team

    return dict(transitions)
