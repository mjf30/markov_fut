from __future__ import annotations
from pathlib import Path
import csv
import typer
import yaml
from rich import print

from .loader import list_match_ids, iter_events_for_match, list_match_ids_by_names
from .markov import construir_transicoes
from .visualize import plot_graph

app = typer.Typer(help="Cadeias de Markov simples com StatsBomb Open Data.")


def _run_pipeline(
    match_ids: list[int],
    data_root: Path,
    out_dir: Path,
    prob_threshold: float,
    incluir_situacao: bool,
):
    """Executa o pipeline de carga, construção e salvamento."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Carrega eventos e agrega
    eventos = []
    for mid in match_ids:
        try:
            evs = iter_events_for_match(data_root, mid)
            eventos.extend(evs)
        except FileNotFoundError:
            print(
                f"[yellow]Aviso:[/yellow] eventos do jogo {mid} não encontrados, pulando."
            )

    print(f"[bold]Eventos carregados:[/bold] {len(eventos)}")

    trans = construir_transicoes(eventos, incluir_situacao=incluir_situacao)

    # Salva contagens
    counts_csv = out_dir / "transition_counts.csv"
    with counts_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from_state", "to_state", "count"])
        for (a, b), c in sorted(trans.counts.items(), key=lambda x: (-x[1], x[0])):
            w.writerow([a, b, c])

    # Salva probabilidades
    probs_csv = out_dir / "transition_matrix.csv"
    with probs_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from_state", "to_state", "probability"])
        for (a, b), p in sorted(trans.probs.items(), key=lambda x: (-x[1], x[0])):
            w.writerow([a, b, f"{p:.6f}"])

    # Exporta dicionário de estados observados
    states = sorted({a for (a, _b) in trans.probs} | {b for (_a, b) in trans.probs})
    with (out_dir / "states.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state"])
        for s in states:
            w.writerow([s])

    # Grafo
    plot_graph(trans.probs, str(out_dir / "graph.png"), threshold=prob_threshold)

    print(f"[green]OK![/green] Arquivos salvos em {out_dir}")


@app.command()
def build(
    out: Path = typer.Option(
        ..., "--out", "-o", help="Pasta de saída", file_okay=False
    ),
    data_root: Path = typer.Option(
        "./_open_data_repo",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Raiz do repo open-data (contendo pasta data/)",
    ),
    sem_situacao: bool = typer.Option(
        False, "--sem-situacao", help="Remove a situação do jogo (placar) da análise."
    ),
    competition: int = typer.Option(None, "--competition", "-c"),
    season: int = typer.Option(None, "--season", "-s"),
    match_id: int = typer.Option(None, "--match-id", "-m"),
    prob_threshold: float = typer.Option(
        0.05, help="Arestas com probabilidade mínima para o grafo"
    ),
):
    """Constrói o modelo a partir de IDs numéricos."""
    if match_id is None:
        if competition is None or season is None:
            raise typer.BadParameter(
                "Informe --match-id OU (--competition e --season)."
            )
        match_ids = list_match_ids(data_root, competition, season)
        print(f"[bold]Total de jogos na temporada:[/bold] {len(match_ids)}")
    else:
        match_ids = [match_id]

    _run_pipeline(
        match_ids,
        data_root,
        out,
        prob_threshold,
        incluir_situacao=not sem_situacao,
    )


@app.command()
def run(
    config_file: Path = typer.Argument(
        ..., exists=True, dir_okay=False, help="Arquivo de configuração YAML."
    )
):
    """Executa a análise a partir de um arquivo de configuração."""
    cfg = yaml.safe_load(config_file.read_text(encoding="utf-8"))

    data_root_str = cfg.get("data_root", "./_open_data_repo")
    data_root = Path(data_root_str).expanduser()
    out_dir = Path(cfg.get("out", "./saida")).expanduser()
    scope = cfg["scope"]
    competition_name = scope["competition"]
    season_name = scope["season"]
    team_name = scope.get("team")  # opcional
    prob_threshold = float(cfg.get("prob_threshold", 0.05))
    incluir_situacao = bool(cfg.get("incluir_situacao", True))

    # Resolver match_ids
    match_ids = list_match_ids_by_names(
        data_root, competition_name, season_name, team_name=team_name
    )
    print(f"[bold]Jogos selecionados:[/bold] {len(match_ids)}")

    _run_pipeline(match_ids, data_root, out_dir, prob_threshold, incluir_situacao)


if __name__ == "__main__":
    app()
