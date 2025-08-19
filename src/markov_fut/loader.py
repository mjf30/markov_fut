
from __future__ import annotations
from pathlib import Path
import json
from typing import List, Tuple

def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def path_competitions_file(data_root: Path) -> Path:
    return data_root / "data" / "competitions.json"

def path_matches_file(data_root: Path, competition_id: int, season_id: int) -> Path:
    return data_root / "data" / "matches" / str(competition_id) / f"{season_id}.json"

def path_events_file(data_root: Path, match_id: int) -> Path:
    return data_root / "data" / "events" / f"{match_id}.json"

def iter_events_for_match(data_root: Path, match_id: int) -> list[dict]:
    evs = load_json(path_events_file(data_root, match_id))
    # ordem robusta
    evs.sort(key=lambda e: (e.get("period", 1) or 1, e.get("minute", 0) or 0, e.get("second", 0) or 0, e.get("index", 0)))
    return evs

def list_match_ids(data_root: Path, competition_id: int, season_id: int) -> List[int]:
    return [m["match_id"] for m in load_json(path_matches_file(data_root, competition_id, season_id))]

def _norm(s: str) -> str:
    return (s or "").casefold().strip()

def resolve_ids_by_names(data_root: Path, competition_name: str, season_name: str) -> Tuple[int, int]:
    comps = load_json(path_competitions_file(data_root))
    cn, sn = _norm(competition_name), _norm(season_name)
    for row in comps:
        if _norm(row.get("competition_name","")) == cn and _norm(row.get("season_name","")) == sn:
            return int(row["competition_id"]), int(row["season_id"])
    for row in comps:
        if cn in _norm(row.get("competition_name","")) and sn in _norm(row.get("season_name","")):
            return int(row["competition_id"]), int(row["season_id"])
    raise ValueError(f"Não encontrei IDs para '{competition_name}' '{season_name}'.")

def list_match_ids_by_names(data_root: Path, competition_name: str, season_name: str) -> List[int]:
    comp_id, season_id = resolve_ids_by_names(data_root, competition_name, season_name)
    return list_match_ids(data_root, comp_id, season_id)

def resolve_team_id_from_events(data_root: Path, match_ids: list[int], team_name: str) -> int:
    tnorm = _norm(team_name)
    for mid in match_ids:
        for ev in iter_events_for_match(data_root, mid):
            team = (ev.get("team") or {})
            name = (team.get("name") or "")
            if _norm(str(name)) == tnorm:
                tid = team.get("id")
                if tid is not None:
                    return int(tid)
    raise ValueError(f"Não achei team_id para '{team_name}' em {len(match_ids)} jogos.")

def filter_match_ids_by_team_in_events(data_root: Path, match_ids: list[int], team_id: int) -> list[int]:
    """Retorna apenas match_ids onde o team_id aparece NOS EVENTOS (robusto a grafias no matches.json)."""
    keep = []
    for mid in match_ids:
        p = path_events_file(data_root, mid)
        try:
            evs = load_json(p)
        except FileNotFoundError:
            continue
        for ev in evs:
            tid = (ev.get("team") or {}).get("id")
            if tid == team_id:
                keep.append(mid)
                break
    return keep
