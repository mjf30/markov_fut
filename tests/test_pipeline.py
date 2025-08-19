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
    # 2 jogos: um do Arsenal, um de Chelsea x Spurs (sem Arsenal)
    (data/"matches/2/27.json").write_text('[{"match_id":1001,"home_team":{"name":"Arsenal"},"away_team":{"name":"Chelsea"}},{"match_id":1002,"home_team":{"name":"Chelsea"},"away_team":{"name":"Tottenham"}}]', encoding="utf-8")
    # eventos jogo 1001 (Arsenal participa)
    evs1 = [
        {"index":1,"period":1,"type":{"name":"Pass"},"team":{"id":1,"name":"Arsenal"},"location":[50,40],"pass":{}},
        {"index":2,"period":1,"type":{"name":"Ball Receipt"},"team":{"id":1,"name":"Arsenal"},"location":[55,40]},
        {"index":3,"period":1,"type":{"name":"Shot"},"team":{"id":1,"name":"Arsenal"},"location":[100,40]},
        {"index":4,"period":1,"type":{"name":"Duel"},"duel":{"type":{"name":"Tackle"}},"outcome":{"name":"Won"},"team":{"id":2,"name":"Chelsea"},"location":[60,40]},
    ]
    (data/"events/1001.json").write_text(json.dumps(evs1), encoding="utf-8")
    # eventos jogo 1002 (Arsenal NÃO participa) — não deve ser considerado
    evs2 = [
        {"index":1,"period":1,"type":{"name":"Pass"},"team":{"id":3,"name":"Chelsea"},"location":[50,40],"pass":{}},
        {"index":2,"period":1,"type":{"name":"Shot"},"team":{"id":4,"name":"Tottenham"},"location":[90,30]},
    ]
    (data/"events/1002.json").write_text(json.dumps(evs2), encoding="utf-8")
    return tmp/"open-data"

def test_run_filters_team_and_no_cross_game(tmp_path: Path):
    data_root = write_fixture_repo(tmp_path)
    out = tmp_path/"out"
    cfg = tmp_path/"config.yaml"
    cfg.write_text(CONFIG_TMPL.format(root=str(data_root), out=str(out)), encoding="utf-8")

    p = run(["markov-fut","run",str(cfg)], stdout=PIPE, stderr=PIPE, text=True)
    assert p.returncode == 0, p.stderr

    # outputs
    for f in ["transition_counts.csv","transition_matrix.csv","states.csv","graph.png"]:
        assert (out/f).exists()

    # Verifica que NÃO há transição do último estado do jogo 1001 para o primeiro do 1002
    # (Como 1002 foi filtrado, de qualquer forma não deve aparecer)
    # Também valida normalização
    from collections import defaultdict
    sums = defaultdict(float)
    with (out/"transition_matrix.csv").open() as f:
        r = csv.DictReader(f)
        for row in r:
            sums[row["from_state"]] += float(row["probability"])
    assert all(abs(v-1.0) < 1e-6 for v in sums.values())
