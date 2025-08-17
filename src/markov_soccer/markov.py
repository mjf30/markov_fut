from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from collections import defaultdict

from .state_definitions import build_state


@dataclass
class Transitions:
    """Stores the raw counts and normalized probabilities of state transitions."""
    counts: Dict[tuple[str, str], int]
    probs: Dict[tuple[str, str], float]


def update_score(event: dict, goals_per_team: Dict[int, int]) -> None:
    """Updates the score based on 'Goal' outcomes in 'Shot' events."""
    if (event.get("type") or {}).get("name") != "Shot":
        return
    shot = event.get("shot") or {}
    outcome = (shot.get("outcome") or {}).get("name")
    if outcome == "Goal":
        team_id = (event.get("team") or {}).get("id")
        if team_id is not None:
            goals_per_team[team_id] = goals_per_team.get(team_id, 0) + 1
    # Note: Own goals are handled differently in the source data but are simplified here.


def get_relative_score(event: dict, goals_per_team: Dict[int, int]) -> tuple[int, int]:
    """Calculates the score relative to the team in the event."""
    team_id = (event.get("team") or {}).get("id")
    if team_id is None:
        return (0, 0)
    
    team_goals = goals_per_team.get(team_id, 0)
    
    # Simple heuristic to find the opponent's ID
    opponent_ids = [i for i in goals_per_team.keys() if i != team_id]
    opponent_goals = goals_per_team.get(opponent_ids[0], 0) if opponent_ids else 0
    
    return (team_goals, opponent_goals)


def build_transitions(
    events: List[dict], include_situation: bool = True
) -> Transitions:
    """Builds the transition counts and probabilities from a list of events."""
    counts: Dict[tuple[str, str], int] = defaultdict(int)
    goals_per_team: Dict[int, int] = {}

    # Build a single sequence of states for the entire game
    state_sequence: List[str] = []
    for ev in events:
        update_score(ev, goals_per_team)
        relative_score = get_relative_score(ev, goals_per_team)
        state = build_state(ev, relative_score, include_situation=include_situation)
        if state is not None:
            state_sequence.append(state.key())

    # Count successive transitions s_i -> s_{i+1}
    for i in range(len(state_sequence) - 1):
        from_state, to_state = state_sequence[i], state_sequence[i + 1]
        counts[(from_state, to_state)] += 1

    # Normalize counts to get probabilities
    totals: Dict[str, int] = defaultdict(int)
    for (from_state, _), count in counts.items():
        totals[from_state] += count

    probs: Dict[tuple[str, str], float] = {}
    for (from_state, to_state), count in counts.items():
        denominator = totals[from_state]
        if denominator > 0:
            probs[(from_state, to_state)] = count / denominator

    return Transitions(counts=dict(counts), probs=probs)