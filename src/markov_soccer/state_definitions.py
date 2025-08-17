from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

# Field thirds based on StatsBomb's X-axis (0-120)
DEF_THIRD, MID_THIRD, ATT_THIRD = "D", "M", "A"


def get_zone_by_x(x: float | int | None) -> Optional[str]:
    """Assigns a field third based on the x-coordinate."""
    if x is None:
        return None
    if x < 40:
        return DEF_THIRD
    if x < 80:
        return MID_THIRD
    return ATT_THIRD


# Discrete actions
PASS, SHOT, LOSS, RECOVERY = "PAS", "FIN", "PER", "REC"


def get_action(event: dict) -> Optional[str]:
    """Determines the discrete action for a given event."""
    etype = (event.get("type") or {}).get("name")
    if etype == "Pass":
        # StatsBomb convention: missing pass.outcome means a complete pass
        outcome = ((event.get("pass") or {}).get("outcome") or {}).get("name")
        return PASS if outcome is None else LOSS
    if etype == "Shot":
        return SHOT
    if etype in {"Dispossessed", "Miscontrol"}:
        return LOSS
    if etype == "Ball Recovery":
        return RECOVERY
    # Other actions are not part of this simple discretization
    return None


@dataclass(frozen=True)
class State:
    """Represents a single state in the Markov chain."""
    # P(ossession)/N(o possession), zone, action, situation (FAV/NEU/DES)
    possession: str
    zone: str
    action: str
    situation: Optional[str] = None  # FAV (Favorable), NEU (Neutral), DES (Unfavorable)

    def key(self) -> str:
        """Generates a unique string key for the state."""
        k = f"{self.possession}_{self.zone}_{self.action}"
        if self.situation:
            k += f"_{self.situation}"
        return k


def get_game_situation(team_goals: int, opponent_goals: int) -> str:
    """Determines the game situation based on the score."""
    if team_goals > opponent_goals:
        return "FAV"
    if team_goals < opponent_goals:
        return "DES"
    return "NEU"


def build_state(
    event: dict, relative_score: Tuple[int, int], include_situation: bool = True
) -> Optional[State]:
    """Constructs a State object from a given event and score."""
    team_id = (event.get("team") or {}).get("id")
    possession_team_id = (event.get("possession_team") or {}).get("id")
    if not team_id or not possession_team_id:
        return None

    possession_char = "P" if team_id == possession_team_id else "S"

    loc = event.get("location")
    x = loc[0] if isinstance(loc, list) and len(loc) >= 1 else None
    z = get_zone_by_x(x)
    a = get_action(event)
    if z is None or a is None:
        return None

    sit = None
    if include_situation:
        team_goals, opponent_goals = relative_score
        sit = get_game_situation(team_goals, opponent_goals)

    return State(possession=possession_char, zone=z, action=a, situation=sit)