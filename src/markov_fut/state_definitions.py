from __future__ import annotations
from typing import Optional, List

# zonas por X (0-120) — já relativo ao time do evento no StatsBomb
def zona_por_x(x: float | int | None) -> Optional[str]:
    if x is None: return None
    if x < 40: return "D"
    if x < 80: return "M"
    return "A"

def _outcome_name(d: dict | None, key: str="outcome") -> Optional[str]:
    if not d: return None
    o = d.get(key) or {}
    if isinstance(o, dict):
        return o.get("name")
    return None

def _has_success(text: Optional[str]) -> bool:
    if not text: return False
    t = text.casefold()
    return ("success" in t) or ("won" in t) or ("wins" in t) or ("successful" in t)

def actions_for_event(ev: dict) -> List[str]:
    """Retorna lista de ações ['PAS'|'FIN'|'PER'|'REC'].
    Especial: Pass com pass.type Interception -> ['REC','PAS'] (one-touch). GK não incluído em REC por escolha.
    """
    et = (ev.get("type") or {}).get("name")
    if et == "Pass":
        p = ev.get("pass") or {}
        ptype = (p.get("type") or {}).get("name")
        out = _outcome_name(p)
        if ptype == "Interception":
            return ["REC","PAS"]
        return ["PAS"] if out is None else ["PER"]
    if et == "Ball Receipt":
        out = _outcome_name(ev)
        return ["PAS"] if not out else ["PER"]  # Incomplete => PER
    if et == "Carry":
        return ["PAS"]
    if et == "Shot":
        return ["FIN"]
    if et in {"Dispossessed","Miscontrol"}:
        return ["PER"]
    if et == "Dribble":
        out = _outcome_name(ev)
        if out and "incomplete" in out.casefold():
            return ["PER"]
        return []
    if et == "Interception":
        out = _outcome_name(ev)
        return ["REC"] if _has_success(out) or out is None else []
    if et == "Duel":
        duel = ev.get("duel") or {}
        dtype = (duel.get("type") or {}).get("name")
        out = _outcome_name(ev)
        if dtype in {"Tackle","Aerial","50/50"} and _has_success(out):
            return ["REC"]
        return []
    if et == "Ball Recovery":
        return ["REC"]
    return []  # GK não entra aqui

def prefixo_por_equipe(ev: dict, team_id_foco: int) -> Optional[str]:
    tid = (ev.get("team") or {}).get("id")
    if tid is None: return None
    return "P" if tid == team_id_foco else "S"

def construir_estados_do_evento(ev: dict, team_id_foco: int) -> list[str]:
    pref = prefixo_por_equipe(ev, team_id_foco)
    if pref is None:
        return []
    loc = ev.get("location")
    x = loc[0] if isinstance(loc, list) and len(loc)>=1 else None
    z = zona_por_x(x)
    if z is None:
        return []
    acts = actions_for_event(ev)
    return [f"{pref}_{z}_{a}" for a in acts]

# -------- Aliases de compatibilidade (para testes/uso antigo) --------
def acao(event: dict):
    acts = actions_for_event(event)
    return acts[0] if acts else None

def construir_estado(event: dict, team_id_foco: int):
    sts = construir_estados_do_evento(event, team_id_foco)
    return sts[0] if sts else None
