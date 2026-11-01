"""Szenario: die Einstellungen der Seitenleiste als unveränderlicher Wert und die daraus gebauten Spiele (Bäume werden je Prozess einmal gebaut)."""

from dataclasses import dataclass
from fractions import Fraction as Fr
from functools import lru_cache

import vdi_constants as C
import vdi_games as G
import vdi_seqform as SQ
import vdi_tree as TR


@dataclass(frozen=True)
class Settings:
    jbet: int = C.STRAT_DEFAULT["jbet"]         # erster Spieler: Setzen mit dem Buben (Zwölftel)
    kbet: int = C.STRAT_DEFAULT["kbet"]         # erster Spieler: Setzen mit dem König im ersten Zug (Zwölftel)
    qcall: int = C.STRAT_DEFAULT["qcall"]       # erster Spieler: Mitgehen mit der Dame nach Pass–Setzen (Zwölftel)
    bluff: int = C.STRAT_DEFAULT["bluff"]       # zweiter Spieler: Setzen mit dem Buben nach einem Pass (Zwölftel)
    call: int = C.STRAT_DEFAULT["call"]         # zweiter Spieler: Mitgehen mit der Dame gegen Setzen (Zwölftel)
    n: int = C.DEFAULT_N
    n3: int = C.DEFAULT_N3
    steps: int = C.DEFAULT_STEPS
    start: str = C.DEFAULT_START
    lsteps: int = C.DEFAULT_LEDUC
    mc: int = C.DEFAULT_MC
    b: int = C.DEFAULT_A_B
    c: int = C.DEFAULT_A_C
    g: int = C.DEFAULT_A_G
    s: int = C.DEFAULT_A_S
    r: int = C.DEFAULT_A_R
    p: int = C.DEFAULT_A_P
    seed: int = C.DEFAULT_SEED


def twelfth(k: int) -> Fr:
    """Ein Reglerwert in Zwölfteln als Bruch."""
    return Fr(int(k), C.TWELFTHS)


def strategy_parameters(s: Settings) -> dict:
    """Die fünf frei wählbaren Entscheidungen als Brüche (alle übrigen sind in der Gleichgewichtsfamilie fest)."""
    return {"alpha": twelfth(s.jbet), "king": twelfth(s.kbet), "queen_call": twelfth(s.qcall), "bluff": twelfth(s.bluff), "call": twelfth(s.call)}


@lru_cache(maxsize=None)
def kuhn_instance(n: int):
    """(Baum, Sequenzform) des Kuhn-Spiels mit n Karten (einmal je Prozess)."""
    T = TR.build(G.Kuhn(n))
    return T, SQ.SeqForm(T)


@lru_cache(maxsize=None)
def leduc_instance():
    T = TR.build(G.Leduc())
    return T, SQ.SeqForm(T)


def anmeldung_game(s: Settings) -> G.Anmeldung:
    """Das Anmeldungsspiel zu den Reglern (Anteil riskanter Sendungen in Prozent, Gebühr fest)."""
    return G.Anmeldung(b=s.b, c=s.c, f=C.A_FEE, g=s.g, s=s.s, r=s.r, p=Fr(s.p, 100))
