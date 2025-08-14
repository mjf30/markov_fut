from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

# Divisão simples do campo: 0-120 no eixo X (StatsBomb)
TERCO_DEF, TERCO_MEI, TERCO_ATA = "D", "M", "A"


def zona_por_x(x: float | int | None) -> Optional[str]:
    if x is None:
        return None
    if x < 40:
        return TERCO_DEF
    if x < 80:
        return TERCO_MEI
    return TERCO_ATA


# Ações discretas
PAS, FIN, PER, REC = "PAS", "FIN", "PER", "REC"


def acao(event: dict) -> Optional[str]:
    etype = (event.get("type") or {}).get("name")
    if etype == "Pass":
        # Convenção StatsBomb: pass.outcome ausente => passe completo
        outcome = ((event.get("pass") or {}).get("outcome") or {}).get("name")
        return PAS if outcome is None else PER
    if etype == "Shot":
        return FIN
    if etype in {"Dispossessed", "Miscontrol"}:
        return PER
    if etype == "Ball Recovery":
        return REC
    # Outras ações não entram na discretização simples
    return None


def posse_valida(event: dict) -> bool:
    team = (event.get("team") or {}).get("id")
    possession_team = (event.get("possession_team") or {}).get("id")
    return team is not None and team == possession_team


@dataclass(frozen=True)
class Estado:
    # P(ossuidor)/S(em posse), zona, ação, situação (FAV/NEU/DES)
    posse: str
    zona: str
    acao: str
    situacao: str  # FAV, NEU, DES

    def key(self) -> str:
        return f"{self.posse}_{self.zona}_{self.acao}_{self.situacao}"


def situacao_jogo(gols_time: int, gols_adv: int) -> str:
    if gols_time > gols_adv:
        return "FAV"
    if gols_time < gols_adv:
        return "DES"
    return "NEU"


def construir_estado(event: dict, placar_rel: Tuple[int, int]) -> Optional[Estado]:
    if not posse_valida(event):
        return None
    loc = event.get("location")
    x = loc[0] if isinstance(loc, list) and len(loc) >= 1 else None
    z = zona_por_x(x)
    a = acao(event)
    if z is None or a is None:
        return None
    gols_time, gols_adv = placar_rel
    sit = situacao_jogo(gols_time, gols_adv)
    return Estado(posse="P", zona=z, acao=a, situacao=sit)
