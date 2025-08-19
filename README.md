# Markov-Fut

A simple CLI tool to build Markov chains from StatsBomb soccer data.

## Features

- **Team-centric analysis**: Build Markov chains for a specific team's matches.
- **Game-by-game segmentation**: States from different games are never connected.
- **Utility commands**: Easily find competition and team names for your analysis.

## States

The states are defined as `{P|S}_{D|M|A}_{PAS|SHO|LOS|REC}`:

-   **{P|S}**: Events from the **focus team** / **opponent** (defined in `scope.team` in `config.yaml`).
-   **Zones**: D (0–40), M (40–80), A (80–120). In StatsBomb, `x` is relative to the event's team, so no flipping is needed.
-   **Actions**:
    -   `PAS` — Successful `Pass` OR `Ball Receipt` OR `Carry`.
    -   `SHO` — `Shot`.
    -   `LOS` — Incomplete `Pass` OR `Dispossessed`/`Miscontrol` OR incomplete `Dribble`.
    -   `REC` — Recovery via: `Ball Recovery` OR `Interception` OR `Duel` (Tackle/Aerial/50/50) won.
    -   *(Goalkeeper events are not included in `REC` in this version.)*

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

1.  Create a `config.yaml` file (e.g., for Premier League 2015/2016, Arsenal):

```yaml
data_root: /path/to/open-data
out: ./output
scope:
  competition: Premier League
  season: 2015/2016
  team: Arsenal
prob_threshold: 0.08
```

2.  Run the tool:

```bash
markov-fut run config.yaml
```

### Utility Commands

-   List available competitions: `markov-fut comps`
-   List available teams in a competition: `markov-fut teams -c "Premier League" -s "2015/2016"`

## Outputs

-   `transition_counts.csv`: Raw counts of transitions between states.
-   `transition_matrix.csv`: Transition probabilities between states.
-   `states.csv`: List of all states and their total occurrences.
-   `graph.png`: A visualization of the Markov chain.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)