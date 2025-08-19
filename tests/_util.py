
import importlib
from collections import defaultdict

def resolve_pkg_name():
    for name in ("markov_futebol","markov_fut"):
        try:
            importlib.import_module(name)
            return name
        except Exception:
            continue
    raise RuntimeError("Pacote não encontrado. Instale com `pip install -e .`")

def get_modules():
    pkg = resolve_pkg_name()
    seg = importlib.import_module(f"{pkg}.segmentation")
    viz = importlib.import_module(f"{pkg}.visualize")
    return pkg, seg, viz

def ev(idx, team, poss, etype, x=60, ptype=None):
    e = {
        "index": idx, "period": 1, "minute": 0, "second": idx,
        "team": {"id": team}, "possession_team": {"id": poss},
        "type": {"name": etype}, "location": [x, 40],
    }
    if etype == "Pass" and ptype:
        e["pass"] = {"type": {"name": ptype}}
    return e

def normalize_probs(counts):
    out_tot = defaultdict(int)
    for (a,b), c in counts.items():
        out_tot[a] += c
    probs = {(a,b): c / max(1, out_tot[a]) for (a,b), c in counts.items()}
    return probs, out_tot
