
from __future__ import annotations
from pathlib import Path
import csv
import typer
from rich import print

from .config_io import load_config
from .loader import (
    list_match_ids_by_names,
    iter_events_for_match,
    resolve_team_id_from_events,
    filter_match_ids_by_team_in_events,
)
from .markov import construir_transicoes

app = typer.Typer(help="Markov StatsBomb (filtra apenas jogos do time foco).")

@app.command()
def run(config: Path):
    cfg = load_config(config)
    out = cfg.out; out.mkdir(parents=True, exist_ok=True)

    # 1) todos os jogos da competição/temporada
    match_ids_all = list_match_ids_by_names(cfg.data_root, cfg.competition, cfg.season)

    # 2) resolve team_id PELOS EVENTOS (robusto)
    if cfg.team is None:
        raise typer.BadParameter("Config sem 'team'. Informe scope.team para P/S por equipe foco.")
    team_id = resolve_team_id_from_events(cfg.data_root, match_ids_all, cfg.team)

    # 3) mantém só partidas onde o time aparece nos eventos
    match_ids = filter_match_ids_by_team_in_events(cfg.data_root, match_ids_all, team_id)
    if not match_ids:
        raise typer.BadParameter(
            f"Nenhum jogo do time '{cfg.team}' encontrado em {cfg.competition} {cfg.season}."
        )

    # 4) debug info (para você conferir)
    dbg = out / "debug_run_info.txt"
    dbg.write_text(
        f"competition={cfg.competition}\nseason={cfg.season}\nteam={cfg.team}\nteam_id={team_id}\n"
        f"season_matches={len(match_ids_all)}\nselected_matches={len(match_ids)}\nmatch_ids={match_ids}\n",
        encoding="utf-8",
    )

    # 5) transições por JOGO e agregação final
    from collections import defaultdict
    all_counts = defaultdict(int)
    for mid in match_ids:
        try:
            evs = iter_events_for_match(cfg.data_root, mid)
        except FileNotFoundError:
            print(f"[yellow]Aviso:[/yellow] eventos do jogo {mid} não encontrados, pulando.")
            continue
        cnt, _ = construir_transicoes(evs, team_id)
        for k, v in cnt.items():
            all_counts[k] += v

    # 6) normalização -> probabilidades
    totals = {}
    for (a,b), c in all_counts.items():
        totals[a] = totals.get(a, 0) + c
    probs = { (a,b): c / totals[a] for (a,b), c in all_counts.items() if totals.get(a,0) > 0 }
    counts = dict(all_counts)

    # 7) CSVs
    with (out/"transition_counts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["from_state","to_state","count"])
        for (a,b),c in sorted(counts.items(), key=lambda x:(-x[1], x[0])): w.writerow([a,b,c])
    with (out/"transition_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["from_state","to_state","probability"])
        for (a,b),p in sorted(probs.items(), key=lambda x:(-x[1], x[0])): w.writerow([a,b,f"{p:.6f}"])
    states = sorted({a for (a,_b) in probs} | {b for (_a,b) in probs})
    with (out/"states.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["state"])
        for s in states: w.writerow([s])

    # 8) visualização — detecta assinatura para manter compatibilidade com sua versão do visualize.py
    try:
        from .visualize import plot_graph as _plot
        import inspect
        sig = inspect.signature(_plot)
        if "counts" in sig.parameters:
            _plot(
                counts=counts, probs=probs, out_png=str(out/"graph.png"),
                prob_threshold=cfg.prob_threshold, min_count=10, topk_per_node=5,
                mirror_s=True, title=f"{cfg.competition} {cfg.season} – {cfg.team}"
            )
        else:
            # assinatura antiga (probs, out_png, threshold,...)
            _plot(probs, str(out/"graph.png"), threshold=cfg.prob_threshold, topk_per_node=None)
    except Exception as e:
        print(f"[yellow]Aviso:[/yellow] plot falhou: {e!r}")

    print(f"[green]OK[/green] → {out}")
