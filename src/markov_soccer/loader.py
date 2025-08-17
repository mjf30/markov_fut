from __future__ import annotations
from pathlib import Path
import json
from typing import Iterable, Dict, List, Tuple, Optional


def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def path_competitions_file(data_root: Path) -> Path:
    return data_root / "data" / "competitions.json"


def path_matches_file(data_root: Path, competition_id: int, season_id: int) -> Path:
    return data_root / "data" / "matches" / str(competition_id) / f"{season_id}.json"


def path_lineups_file(data_root: Path, match_id: int) -> Path:
    return data_root / "data" / "lineups" / f"{match_id}.json"


def path_events_file(data_root: Path, match_id: int) -> Path:
    return data_root / "data" / "events" / f"{match_id}.json"


def list_match_ids(data_root: Path, competition_id: int, season_id: int) -> List[int]:
    matches = load_json(path_matches_file(data_root, competition_id, season_id))
    return [m["match_id"] for m in matches]


def iter_events_for_match(data_root: Path, match_id: int) -> List[dict]:
    events = load_json(path_events_file(data_root, match_id))
    # Ordenar por "index" se existir, senão na ordem do arquivo
    events.sort(key=lambda e: e.get("index", 0))
    return events


# ---------- Name-based helpers ----------


def _norm(s: str) -> str:
    return s.casefold().strip()


def resolve_ids_by_names(
    data_root: Path, competition_name: str, season_name: str
) -> Tuple[int, int]:
    """Busca em competitions.json a linha cujo competition_name e season_name casam (case-insensitive)
    e retorna (competition_id, season_id)."""
    comps = load_json(path_competitions_file(data_root))
    cn, sn = _norm(competition_name), _norm(season_name)
    for row in comps:
        if (
            _norm(row.get("competition_name", "")) == cn
            and _norm(row.get("season_name", "")) == sn
        ):
            return int(row["competition_id"]), int(row["season_id"])
    # fallback: tentar contains
    for row in comps:
        if cn in _norm(row.get("competition_name", "")) and sn in _norm(
            row.get("season_name", "")
        ):
            return int(row["competition_id"]), int(row["season_id"])
    raise ValueError(
        f"Nao encontrei IDs para competição='{competition_name}' temporada='{season_name}'."
    )


def _extract_team_names(m: dict) -> List[str]:
    names = []
    # Patterns comuns no Open Data
    ht = m.get("home_team") or {}
    at = m.get("away_team") or {}
    # dict aninhado
    for k in ("home_team_name", "name"):
        v = ht.get(k)
        if isinstance(v, str):
            names.append(v)
    for k in ("away_team_name", "name"):
        v = at.get(k)
        if isinstance(v, str):
            names.append(v)
    # top-level alternativas (algumas versões trazem como chaves diretas)
    for k in ("home_team_name", "away_team_name", "home_team", "away_team"):
        v = m.get(k)
        if isinstance(v, str):
            names.append(v)
        elif isinstance(v, dict):
            vv = v.get("name") or v.get("home_team_name") or v.get("away_team_name")
            if isinstance(vv, str):
                names.append(vv)
    # dedup simples
    out = []
    seen = set()
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def list_match_ids_by_names(
    data_root: Path,
    competition_name: str,
    season_name: str,
    team_name: Optional[str] = None,
) -> List[int]:
    comp_id, season_id = resolve_ids_by_names(data_root, competition_name, season_name)
    matches = load_json(path_matches_file(data_root, comp_id, season_id))
    if team_name is None:
        return [m["match_id"] for m in matches]
    tnorm = _norm(team_name)
    mids = []
    for m in matches:
        names = _extract_team_names(m)
        if any(_norm(n) == tnorm for n in names):
            mids.append(m["match_id"])
    if not mids:
        raise ValueError(
            f"Time '{team_name}' não encontrado em {competition_name} {season_name}."
        )
    return mids
