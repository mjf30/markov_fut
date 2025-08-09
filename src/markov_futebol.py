"""
markov_futebol.py — Um único arquivo com as funções principais do projeto.
Mantém tudo simples, com docstrings e passos claros.
"""
from __future__ import annotations
import json, os, glob
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

# ============== CONFIG E UTIL ==============

@dataclass
class Cfg:
    raw: Path
    interim: Path
    outputs: Path
    thirds_x: List[float]
    lanes_y: List[float]
    actions_include: List[str]
    action_other: str
    include_ball_receipt_in_edges: bool
    carry_zone_from_end_location: bool
    alpha_smoothing: float
    treat_shot_as_terminal: bool
    random_seed: int
    # NOVO — filtros
    filt_competitions: List[int]
    filt_seasons: List[int]
    filt_matches: List[int]
    filt_teams: List[str]

def load_cfg(path: str | Path) -> Cfg:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    paths = cfg["paths"]
    field = cfg["field"]
    acts = cfg["actions"]
    fil = cfg.get("filters", {})
    repo_dir = cfg.get("open_data_repo_dir", "./_open_data_repo/data")
    return Cfg(
        raw=Path(repo_dir),
        interim=Path(paths["interim"]),
        outputs=Path(paths["outputs"]),
        thirds_x=field["thirds_x"],
        lanes_y=field["lanes_y"],
        actions_include=list(acts["include"]),
        action_other=acts["map_other_to"],
        include_ball_receipt_in_edges=bool(acts.get("include_ball_receipt_in_edges", False)),
        carry_zone_from_end_location=bool(acts.get("carry_zone_from_end_location", True)),
        alpha_smoothing=float(cfg.get("alpha_smoothing", 0.3)),
        treat_shot_as_terminal=bool(cfg.get("treat_shot_as_terminal", True)),
        random_seed=int(cfg.get("random_seed", 42)),
        # filtros
        filt_competitions=list(fil.get("competitions", [])),
        filt_seasons=list(fil.get("seasons", [])),
        filt_matches=list(fil.get("matches", [])),
        filt_teams=list(fil.get("teams", [])),
    )

def ensure_dirs(cfg: Cfg) -> None:
    for p in [cfg.interim, cfg.outputs, cfg.outputs / "models", cfg.outputs / "figures", cfg.outputs / "tables"]:
        p.mkdir(parents=True, exist_ok=True)

# ============== FETCH ==============

def fetch_data(cfg: Cfg) -> None:
    """
    Verifica se o diretório de dados brutos (open_data_repo_dir) existe e contém dados.
    Não copia mais arquivos, apenas valida a fonte.
    """
    src_data = cfg.raw
    if not (src_data.exists() and any(src_data.glob("**/*.json"))):
        print(f"[fetch] Diretório de dados '{src_data}' não encontrado ou está vazio.")
        print("[fetch] Por favor, clone o repositório 'statsbomb/open-data' e configure 'open_data_repo_dir' no seu config.yaml.")
    else:
        print(f"[fetch] Usando dados diretamente de '{src_data}'. Nenhuma cópia é necessária.")

def _allowed_match_ids_from_filters(cfg: Cfg) -> set[int] | None:
    """
    Retorna um conjunto de match_id permitidos conforme os filtros do config.
    Se não houver filtro algum, retorna None (processa tudo).
    """
    # Sem filtros -> processa tudo
    if not (cfg.filt_competitions or cfg.filt_seasons or cfg.filt_matches or cfg.filt_teams):
        return None

    allowed = set()
    matches_root = cfg.raw / "matches"
    # Se não houver arquivos de matches, ainda assim respeite 'matches' explícitos
    if not matches_root.exists():
        return set(cfg.filt_matches) if cfg.filt_matches else set()

    for comp_dir in matches_root.iterdir():
        if not comp_dir.is_dir():
            continue
        comp_id = int(comp_dir.name)
        if cfg.filt_competitions and comp_id not in cfg.filt_competitions:
            continue
        for season_file in comp_dir.glob("*.json"):
            season_id = int(season_file.stem)
            if cfg.filt_seasons and season_id not in cfg.filt_seasons:
                continue
            ms = json.loads(season_file.read_text(encoding="utf-8"))
            for m in ms:
                mid = int(m["match_id"])
                # filtro por matches explícitos
                if cfg.filt_matches and mid not in cfg.filt_matches:
                    continue
                # filtro por times
                if cfg.filt_teams:
                    home = m["home_team"]["home_team_name"]
                    away = m["away_team"]["away_team_name"]
                    if not any(t in (home, away) for t in cfg.filt_teams):
                        continue
                allowed.add(mid)

    # Inclui os ids passados diretamente, mesmo se não aparecerem nos matches (robustez)
    allowed |= set(cfg.filt_matches)
    return allowed


# ============== CLEAN (ORIENTAÇÃO, ZONAS, AÇÕES) ==============

def _flip_to_possession_perspective(row: pd.Series) -> tuple[float, float]:
    x, y = row.get("location_x"), row.get("location_y")
    if pd.isna(x) or pd.isna(y): return np.nan, np.nan
    same_team = (row.get("team") == row.get("possession_team"))
    return (float(x), float(y)) if same_team else (float(120 - x), float(80 - y))

def _zone_bucket(x: float, y: float, cfg: Cfg) -> tuple[int, str]:
    if any(pd.isna(v) for v in [x, y]): return -1, "NA"
    tx1, tx2 = cfg.thirds_x; ly1, ly2 = cfg.lanes_y
    xi = 0 if x < tx1 else (1 if x < tx2 else 2)
    yi = 0 if y < ly1 else (1 if y < ly2 else 2)
    zone_id = yi * 3 + xi
    names = ["D-ESQ","D-CEN","D-DIR","M-ESQ","M-CEN","M-DIR","A-ESQ","A-CEN","A-DIR"]
    return int(zone_id), names[zone_id]

def _map_action(etype: str) -> str:
    if not etype: return "other"
    t = etype.lower()
    if "pass" in t: return "pass"
    if "carry" in t: return "carry"
    if "dribble" in t: return "dribble"
    if "shot" in t: return "shot"
    if "clearance" in t: return "clearance"
    return "other"

def clean_events(cfg: Cfg) -> None:
    allowed = _allowed_match_ids_from_filters(cfg)
    files = sorted(glob.glob(str(cfg.raw / "events" / "*.json")))
    if not files:
        print("[clean] Nenhum JSON em data/raw/events. Copie do repo clonado ou rode --fetch após configurar 'open_data_repo_dir'.")
        return

    rows = []
    for path in tqdm(files, desc="[clean] lendo events/*.json"):
        mid = int(Path(path).stem)
        if allowed is not None and mid not in allowed:
            continue  # pula jogos fora do filtro
        with open(path, "r", encoding="utf-8") as f:
            evs = json.load(f)
        match_id = int(Path(path).stem)
        for ev in evs:
            period = ev.get("period")
            if period is None or int(period) > 4: continue
            
            etype = (ev.get("type") or {}).get("name")
            pass_outcome = (ev.get("pass", {}).get("outcome") or {}).get("name")
            
            row = {
                "event_id": ev["id"],
                "match_id": match_id, 
                "period": int(period), 
                "index": int(ev.get("index", -1)),
                "timestamp": ev.get("timestamp"), 
                "team": (ev.get("team") or {}).get("name"), 
                "possession_team": (ev.get("possession_team") or {}).get("name"), 
                "type": etype,
                "location_x": (ev.get("location") or [None, None])[0], 
                "location_y": (ev.get("location") or [None, None])[1],
                "under_pressure": bool(ev.get("under_pressure", False)),
                "related_events": ev.get("related_events") or [],
                "is_ball_receipt": (etype or "").lower() == "ball receipt",
                "out": bool(ev.get("out", False)),
                # Pass
                "pass_type": (ev.get("pass", {}).get("type") or {}).get("name"),
                "pass_outcome": pass_outcome,
                # Duel
                "duel_type": (ev.get("duel", {}).get("type") or {}).get("name"),
                "duel_outcome": (ev.get("duel", {}).get("outcome") or {}).get("name"),
                # 50/50
                "fifty_fifty_outcome": (ev.get("50_50", {}).get("outcome") or {}).get("name"),
                # Flags
                "is_interception": etype == "Interception",
                "is_ball_recovery": etype == "Ball Recovery",
                "is_clearance": etype == "Clearance",
                "is_offside": etype == "Offside" or pass_outcome == "Offside",
                # Goalkeeper
                "gk_type": (ev.get("goalkeeper", {}).get("type") or {}).get("name"),
                # Shot
                "shot_outcome": (ev.get("shot", {}).get("outcome") or {}).get("name"),
            }
            
            sx, sy = _flip_to_possession_perspective(pd.Series(row)); row["sx"], row["sy"] = sx, sy
            zid, zname = _zone_bucket(sx, sy, cfg); row["zone_id"], row["zone_name"] = zid, zname
            row["action"] = _map_action(etype)
            rows.append(row)

    df = pd.DataFrame(rows).sort_values(["match_id","period","index"]).reset_index(drop=True)
    df.loc[df["zone_id"] < 0, "zone_name"] = "NA"
    outp = cfg.interim / "events_clean.parquet"
    df.to_parquet(outp, index=False)
    print(f"[clean] salvo {outp} ({len(df)} linhas)")

# ============== ESTADOS E ARESTAS ==============

def _cause_of_flip(prev_row: pd.Series, next_row: pd.Series, id2row: dict) -> tuple[str, bool]:
    """Árvore de decisão para encontrar a causa da troca de posse."""
    # A) Reinícios
    if next_row["type"] == "Pass" and next_row["pass_type"]:
        ptype = next_row["pass_type"].lower()
        if "throw-in" in ptype: return "restart_throw_in", True
        if "goal kick" in ptype: return "restart_goal_kick", True
        if "corner" in ptype: return "restart_corner", True
        if "free kick" in ptype: return "restart_free_kick", True
        if "kick off" in ptype: return "restart_kickoff", True

    # B) Ações defensivas (time novo)
    if next_row["is_interception"]: return "interception", False
    if next_row["is_ball_recovery"]: return "ball_recovery", False
    if next_row["duel_type"] == "Tackle" and "Success" in (next_row["duel_outcome"] or ""): return "tackle", False
    if next_row["type"] == "Foul Won": return "foul_won", False
    if next_row["fifty_fifty_outcome"] == "Success": return "fifty_fifty", False
    if next_row["gk_type"] in ["Save", "Claim", "Punch", "Smother"]: return "gk_action", False
    
    # Checar related_events para ações defensivas
    for rid in next_row.get("related_events", []):
        rel = id2row.get(rid)
        if not rel: continue
        if rel.get("is_interception"): return "interception", False
        if rel.get("duel_type") == "Tackle" and "Success" in (rel.get("duel_outcome") or ""): return "tackle", False

    # C) Erros do time antigo
    if prev_row["is_offside"]: return "offside", False
    if prev_row["type"] == "Miscontrol": return "miscontrol", False
    if prev_row["type"] == "Dispossessed": return "dispossessed", False
    if prev_row["type"] == "Pass" and prev_row["pass_outcome"] in ["Incomplete", "Out"]:
        return ("out" if prev_row["out"] else "bad_pass"), False
    if prev_row["is_clearance"]: return "clearance_conceded", False

    # D) Pressão
    if prev_row["under_pressure"]: return "pressure_loss", False

    # E) Fallback
    return "other", False

def build_states_and_edges(cfg: Cfg) -> None:
    path = cfg.interim / "events_clean.parquet"
    if not path.exists():
        print("[states/edges] events_clean.parquet não encontrado. Rode --clean primeiro.")
        return
    df = pd.read_parquet(path)

    # Criar índice id -> linha para lookups rápidos em related_events
    id2row = {row["event_id"]: row for row in df.to_dict("records")}

    if not cfg.include_ball_receipt_in_edges:
        df = df[~df["is_ball_receipt"].fillna(False)].copy()

    def mk_state(row: pd.Series):
        role = "atk" if row["team"] == row["possession_team"] else "def"
        return (role, int(row["zone_id"]), row["action"])

    df["state"] = df.apply(mk_state, axis=1)
    states = sorted(df["state"].dropna().unique().tolist())
    state_to_id = {s:i for i,s in enumerate(states)}

    # salvar índice de estados
    idx_path = cfg.outputs / "models" / "state_index.json"
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    import json as _json
    idx_path.write_text(_json.dumps({
        "n_states": len(states),
        "states": [{"state_id": state_to_id[s], "role": s[0], "zone_id": s[1], "action": s[2]} for s in states],
        "meta": {"thirds_x": cfg.thirds_x, "lanes_y": cfg.lanes_y, "treat_shot_as_terminal": cfg.treat_shot_as_terminal}
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # arestas
    edges = []
    for (mid, per), g in tqdm(df.groupby(["match_id","period"], sort=False), desc="[edges] construindo arestas"):
        g = g.sort_values("index").reset_index(drop=True)
        for i in range(len(g)-1):
            a = g.iloc[i]; b = g.iloc[i+1]
            if cfg.treat_shot_as_terminal and a["action"] == "shot": continue
            a_id = state_to_id.get(a["state"]); b_id = state_to_id.get(b["state"])
            if a_id is None or b_id is None: continue
            
            kind = "intra" if a["team"] == b["team"] else "flip"
            cause, is_restart = "", False
            if kind == "flip":
                cause, is_restart = _cause_of_flip(a, b, id2row)
            
            edges.append((a_id, b_id, kind, cause, is_restart))

    if not edges:
        print("[edges] nenhuma aresta gerada.")
        return
    
    edf = (pd.DataFrame(edges, columns=["from_id","to_id","kind","cause","is_restart"])
           .value_counts()
           .reset_index(name="count"))
    out_edges = cfg.outputs / "tables" / "edges.csv"
    out_edges.parent.mkdir(parents=True, exist_ok=True)
    edf.to_csv(out_edges, index=False)
    print(f"[edges] salvo {out_edges} ({len(edf)} linhas)")

# ============== ESTIMAÇÃO P ==============

def estimate_P(cfg: Cfg) -> None:
    idx_path = cfg.outputs / "models" / "state_index.json"
    edges_path = cfg.outputs / "tables" / "edges.csv"
    if not (idx_path.exists() and edges_path.exists()):
        print("[estimate] faltam state_index.json e/ou edges.csv. Rode --states/--edges primeiro.")
        return

    import json as _json
    idx = _json.loads(idx_path.read_text(encoding="utf-8"))
    n_states = int(idx["n_states"]); states = idx["states"]
    role = np.array([s["role"] for s in states])

    edf = pd.read_csv(edges_path)
    C = np.zeros((n_states, n_states), dtype=np.float64)
    for r in edf.itertuples(index=False):
        C[int(r.from_id), int(r.to_id)] += float(r.count)

    alpha = cfg.alpha_smoothing
    P = (C + alpha) / (C.sum(axis=1, keepdims=True) + alpha * n_states)
    np.savez(cfg.outputs / "models" / "P_full.npz", P=P)

    atk_idx = np.where(role == "atk")[0]; def_idx = np.where(role == "def")[0]
    A = P[np.ix_(atk_idx, atk_idx)]; B = P[np.ix_(atk_idx, def_idx)]
    Cb = P[np.ix_(def_idx, atk_idx)]; D = P[np.ix_(def_idx, def_idx)]
    np.savez(cfg.outputs / "models" / "P_blocks.npz", A=A, B=B, C=Cb, D=D, atk_idx=atk_idx, def_idx=def_idx)
    print(f"[estimate] salvo P_full.npz e P_blocks.npz (N={n_states})")

# ============== AVALIAÇÃO E FIGURAS ==============

def evaluate_and_plot(cfg: Cfg, do_figures: bool = True) -> None:
    import numpy as np
    import pandas as pd
    import json as _json

    events_path = cfg.interim / "events_clean.parquet"
    edges_path = cfg.outputs / "tables" / "edges.csv"
    pfull_path = cfg.outputs / "models" / "P_full.npz"
    sidx_path = cfg.outputs / "models" / "state_index.json"

    if not all(p.exists() for p in [events_path, edges_path, pfull_path, sidx_path]):
        print("[evaluate] faltam arquivos. Rode as etapas anteriores.")
        return

    df = pd.read_parquet(events_path)
    edf = pd.read_csv(edges_path)
    P = np.load(pfull_path)["P"]
    state_index = _json.loads(sidx_path.read_text(encoding="utf-8"))

    total = edf["count"].sum()
    # Evitar erro de indexação se a matriz P for menor que os IDs em edf
    valid_from = edf["from_id"] < P.shape[0]
    valid_to = edf["to_id"] < P.shape[1]
    valid_indices = valid_from & valid_to
    
    edf_valid = edf[valid_indices].copy()
    
    log_probs = np.log(np.clip(P[edf_valid["from_id"], edf_valid["to_id"]], 1e-12, 1.0))
    ll = float((edf_valid["count"] * log_probs).sum())
    ppl = float(np.exp(-ll / max(edf_valid["count"].sum(), 1)))

    metrics = pd.DataFrame([{"log_likelihood": ll, "perplexity": ppl, "total_edges": total}])
    metrics_path = cfg.outputs / "tables" / "metrics.csv"
    metrics.to_csv(metrics_path, index=False)
    print(f"[evaluate] métricas salvas em {metrics_path}")

    if do_figures:
        try:
            from plotting import plot_recovery_heatmap, plot_transition_graph, plot_flip_kernel_heatmap
            
            plot_recovery_heatmap(df, outpath=cfg.outputs / "figures" / "heatmap_recovery.png")
            
            plot_transition_graph(
                P, state_index, 
                threshold=0.08, 
                outpath=cfg.outputs / "figures" / "graph_threshold.png"
            )
            
            # Filtra reinícios para a análise de kernel
            flips_for_kernel = edf.query("kind == 'flip' and is_restart == False")
            plot_flip_kernel_heatmap(
                flips_for_kernel, 
                state_index, 
                outpath=cfg.outputs / "figures" / "heatmap_flip_kernel.png"
            )
            print("[evaluate] figuras salvas.")
        except Exception as e:
            print("[evaluate] erro ao gerar figuras:", e)

# FIM
