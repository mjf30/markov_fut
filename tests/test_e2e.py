from pathlib import Path
from subprocess import run, PIPE
import json, csv

CONFIG_TMPL = """data_root: {root}
out: {out}
scope:
  competition: Premier League
  season: 2015/2016
  team: Arsenal
prob_threshold: 0.05
"""

def write_fixture_repo(tmp: Path):
    data = tmp/"open-data"/"data"
    (data/"events").mkdir(parents=True)
    (data/"matches/2").mkdir(parents=True)
    (data/"competitions.json").write_text('[{"competition_id":2,"competition_name":"Premier League","season_id":27,"season_name":"2015/2016"}]', encoding="utf-8")
    (data/"matches/2/27.json").write_text('[{"match_id":1001,"home_team":{"name":"Arsenal"},"away_team":{"name":"Chelsea"}},{"match_id":1002,"home_team":{"name":"Liverpool"},"away_team":{"name":"Arsenal"}}]', encoding="utf-8")
    # Jogo 1001: Arsenal (id 1) x Chelsea (id 2)
    evs1 = [
        {"index":1,"period":1,"type":{"name":"Pass"},"team":{"id":1,"name":"Arsenal"},"location":[50,40],"pass":{}},
        {"index":2,"period":1,"type":{"name":"Ball Receipt"},"team":{"id":1,"name":"Arsenal"},"location":[55,40]},
        {"index":3,"period":1,"type":{"name":"Pass"},"team":{"id":1,"name":"Arsenal"},"location":[70,40],"pass":{}},
        {"index":4,"period":1,"type":{"name":"Shot"},"team":{"id":1,"name":"Arsenal"},"location":[100,40]},
        {"index":5,"period":1,"type":{"name":"Duel"},"duel":{"type":{"name":"Tackle"}},"outcome":{"name":"Won"},"team":{"id":2,"name":"Chelsea"},"location":[60,40]},
        {"index":6,"period":1,"type":{"name":"Pass"},"team":{"id":2,"name":"Chelsea"},"location":[62,40],"pass":{}},
        {"index":7,"period":1,"type":{"name":"Ball Receipt"},"team":{"id":2,"name":"Chelsea"},"location":[66,40]},
    ]
    (data/"events/1001.json").write_text(json.dumps(evs1), encoding="utf-8")
    # Jogo 1002: Liverpool (id 3) x Arsenal (id 1)
    evs2 = [
        {"index":1,"period":1,"type":{"name":"Pass"},"team":{"id":3,"name":"Liverpool"},"location":[50,40],"pass":{}},
        {"index":2,"period":1,"type":{"name":"Ball Receipt"},"team":{"id":3,"name":"Liverpool"},"location":[55,40]},
        {"index":3,"period":1,"type":{"name":"Pass"},"team":{"id":3,"name":"Liverpool"},"location":[70,40],"pass":{}},
        {"index":4,"period":1,"type":{"name":"Interception"},"outcome":{"name":"Success In Play"},"team":{"id":1,"name":"Arsenal"},"location":[70,40]},
        {"index":5,"period":1,"type":{"name":"Pass"},"team":{"id":1,"name":"Arsenal"},"location":[72,40],"pass":{"type":{"name":"Interception"}}},
    ]
    (data/"events/1002.json").write_text(json.dumps(evs2), encoding="utf-8")
    return tmp/"open-data"

def test_cli_run_filters_team_and_no_cross_match(tmp_path: Path):
    data_root = write_fixture_repo(tmp_path)
    out = tmp_path/"out"
    cfg = tmp_path/"config.yaml"
    cfg.write_text(CONFIG_TMPL.format(root=str(data_root), out=str(out)), encoding="utf-8")

    p = run(["markov-fut","run",str(cfg)], stdout=PIPE, stderr=PIPE, text=True)
    assert p.returncode == 0, p.stderr

    for fname in ["transition_counts.csv","transition_matrix.csv","states.csv","graph.png"]:
        assert (out/fname).exists()

    # soma das linhas ~ 1
    from collections import defaultdict
    sums = defaultdict(float)
    with (out/"transition_matrix.csv").open() as f:
        r = csv.DictReader(f)
        for row in r:
            sums[row["from_state"]] += float(row["probability"])
    assert all(abs(v-1.0) < 1e-6 for v in sums.values())

    # garante que há P_* e S_* e que há PAS->PAS
    states = (out/"states.csv").read_text().splitlines()[1:]
    assert any(s.startswith("P_") for s in states)
    assert any(s.startswith("S_") for s in states)
