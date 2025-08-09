#!/usr/bin/env python3
"""
Orquestrador simples do pipeline.
Uso:
  python run.py --all --config config.yaml
  python run.py --fetch --clean --states --edges --estimate --evaluate --figures --config config.yaml
"""
import argparse, sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))
from markov_futebol import (
    load_cfg, ensure_dirs,
    fetch_data, clean_events,
    build_states_and_edges, estimate_P,
    evaluate_and_plot
)

def parse_args():
    p = argparse.ArgumentParser(description="Pipeline simples de Markov (StatsBomb Open Data)")
    p.add_argument("--config", type=str, default="config.yaml", help="Caminho do YAML de config")
    p.add_argument("--all", action="store_true", help="Roda todas as etapas")
    p.add_argument("--fetch", action="store_true", help="Baixa ou carrega dados brutos")
    p.add_argument("--clean", action="store_true", help="Limpa e enriquece eventos")
    p.add_argument("--states", action="store_true", help="Constrói estados")
    p.add_argument("--edges", action="store_true", help="Gera arestas intra/flip")
    p.add_argument("--estimate", action="store_true", help="Estima P e blocos")
    p.add_argument("--evaluate", action="store_true", help="Métricas")
    p.add_argument("--figures", action="store_true", help="Figuras")
    return p.parse_args()

def main():
    args = parse_args()
    cfg = load_cfg(args.config)
    ensure_dirs(cfg)

    if args.all or args.fetch:
        fetch_data(cfg)
    if args.all or args.clean:
        clean_events(cfg)
    if args.all or args.states or args.edges:
        build_states_and_edges(cfg)
    if args.all or args.estimate:
        estimate_P(cfg)
    if args.all or args.evaluate or args.figures:
        evaluate_and_plot(cfg, do_figures=(args.all or args.figures))

if __name__ == "__main__":
    main()
