from __future__ import annotations
from pathlib import Path
import csv
import typer
import yaml
from rich import print

from .loader import list_match_ids, iter_events_for_match, list_match_ids_by_names
from .markov import build_transitions
from .visualize import plot_graph

app = typer.Typer(help="A simple Markov Chain model for soccer matches using StatsBomb Open Data.")


def _run_pipeline(
    match_ids: list[int],
    data_root: Path,
    out_dir: Path,
    prob_threshold: float,
    include_situation: bool,
):
    """Loads data, builds the model, and saves the output files."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load and aggregate events
    events = []
    for mid in match_ids:
        try:
            match_events = iter_events_for_match(data_root, mid)
            events.extend(match_events)
        except FileNotFoundError:
            print(f"[yellow]Warning:[/yellow] Event data for match {mid} not found, skipping.")

    if not events:
        print("[red]No events found for the provided match IDs.[/red]")
        raise typer.Exit(1)

    print(f"[bold]Events loaded:[/bold] {len(events)}")

    transitions = build_transitions(events, include_situation=include_situation)

    # Save transition counts
    counts_csv = out_dir / "transition_counts.csv"
    with counts_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["from_state", "to_state", "count"])
        for (a, b), c in sorted(transitions.counts.items(), key=lambda x: (-x[1], x[0])):
            writer.writerow([a, b, c])

    # Save transition probabilities
    probs_csv = out_dir / "transition_matrix.csv"
    with probs_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["from_state", "to_state", "probability"])
        for (a, b), p in sorted(transitions.probs.items(), key=lambda x: (-x[1], x[0])):
            writer.writerow([a, b, f"{p:.6f}"])

    # Export a dictionary of observed states
    states = sorted({a for (a, _b) in transitions.probs} | {b for (_a, b) in transitions.probs})
    with (out_dir / "states.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["state"])
        for s in states:
            writer.writerow([s])

    # Save the graph visualization
    plot_graph(transitions.probs, str(out_dir / "graph.png"), threshold=prob_threshold)

    print(f"[green]Success![/green] Output files saved in {out_dir}")


@app.command()
def run(
    config_file: Path = typer.Argument(
        ..., exists=True, dir_okay=False, help="Path to the YAML configuration file."
    )
):
    """Runs the analysis based on a configuration file."""
    cfg = yaml.safe_load(config_file.read_text(encoding="utf-8"))

    data_root_str = cfg.get("data_root", "./statsbomb_data")
    data_root = Path(data_root_str).expanduser()
    out_dir = Path(cfg.get("out", "./output")).expanduser()

    # Load analysis parameters
    params = cfg.get("params", {})
    prob_threshold = float(params.get("prob_threshold", 0.05))
    include_situation = bool(params.get("include_situation", True))

    # Determine match_ids (IDs take precedence over names)
    ids_cfg = cfg.get("ids")
    scope_cfg = cfg.get("scope")
    match_ids = []

    if ids_cfg:
        match_id = ids_cfg.get("match_id")
        if match_id:
            match_ids = [match_id]
            print(f"[bold]Selected match (by ID):[/bold] {match_id}")
        else:
            comp_id = ids_cfg.get("competition_id")
            season_id = ids_cfg.get("season_id")
            if comp_id and season_id:
                match_ids = list_match_ids(data_root, comp_id, season_id)
                print(f"[bold]Matches in season (by ID):[/bold] {len(match_ids)}")
            
    if not match_ids and scope_cfg:
        competition_name = scope_cfg.get("competition")
        season_name = scope_cfg.get("season")
        team_name = scope_cfg.get("team")
        if competition_name and season_name:
            match_ids = list_match_ids_by_names(
                data_root, competition_name, season_name, team_name=team_name
            )
            print(f"[bold]Selected matches (by name):[/bold] {len(match_ids)}")

    if not match_ids:
        print("[red]Error:[/red] No valid match configuration found in 'ids' or 'scope'.")
        raise typer.Exit(1)

    _run_pipeline(match_ids, data_root, out_dir, prob_threshold, include_situation)


if __name__ == "__main__":
    app()
