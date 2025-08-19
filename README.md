# markov-fut (v0.5.0)

Estados (sem placar, 3 partes):
```
{P|S}_{D|M|A}_{PAS|FIN|PER|REC}
```
- **P/S** = eventos da **equipe foco** / **adversário** (defina `scope.team` no `config.yaml`).
- **Zonas** = D (0–40), M (40–80), A (80–120). **No StatsBomb, x já é relativo ao time do evento** — não faça flip.
- **Ações**:
  - `PAS` — `Pass` **completo** (sem `pass.outcome`) **OU** `Ball Receipt` **OU** `Carry`.
  - `FIN` — `Shot`.
  - `PER` — `Pass` **incompleto** (`pass.outcome`) **OU** `Dispossessed`/`Miscontrol` **OU** `Dribble` **incompleto**.
  - `REC` — retoma via: `Ball Recovery` **ou** `Interception` (evento, sucesso/sem outcome) **ou**
    `Pass(type="Interception")` (gera **REC→PAS** no mesmo evento) **ou**
    `Duel` (`Tackle`/`Aerial`/`50/50`) **vencido**.
  - *(`Goal Keeper` não entra em `REC` nesta versão.)*

## Robusteza adicionada
- **Filtro por jogos do time foco usando os *eventos*** (não depende da grafia do nome em `matches.json`).
- **Reset por jogo**: nunca conecta estados de jogos diferentes.
- **Comandos utilitários**: `markov-fut comps` e `markov-fut teams -c "Premier League" -s "2015/2016"`.

## Instalação
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Execução
Crie `config.yaml` (ex.: Premier League 2015/2016, Arsenal):
```yaml
data_root: /caminho/para/open-data
out: ./saida
scope:
  competition: Premier League
  season: 2015/2016
  team: Arsenal
prob_threshold: 0.08
```
Rode:
```bash
markov-fut run config.yaml
```

Saídas: `transition_counts.csv`, `transition_matrix.csv`, `states.csv`, `graph.png`.
