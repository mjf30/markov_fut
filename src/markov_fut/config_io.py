from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class RunConfig:
    data_root: Path
    out: Path
    competition: str
    season: str
    team: str | None
    prob_threshold: float

def load_config(path: Path) -> RunConfig:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    scope = cfg.get("scope") or {}
    data_root = Path(cfg.get("data_root", "./_open_data_repo")).expanduser()
    out = Path(cfg.get("out", "./saida")).expanduser()
    comp = scope.get("competition")
    season = scope.get("season")
    team = scope.get("team")
    if not comp or not season:
        raise ValueError("scope.competition e scope.season são obrigatórios")
    prob = float(cfg.get("prob_threshold", 0.08))
    return RunConfig(data_root, out, comp, season, team, prob)
