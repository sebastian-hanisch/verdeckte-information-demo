"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b). Alle Erwartungswerte sind von Hand gerechnet (Rechnung im Docstring)."""

import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import vdi_games as G  # noqa: E402
import vdi_seqform as SQ  # noqa: E402
import vdi_tree as TR  # noqa: E402


@lru_cache(maxsize=None)
def kuhn_instance(n: int):
    """(Baum, Sequenzform) des Kuhn-Spiels mit n Karten, einmal je Prozess gebaut."""
    T = TR.build(G.Kuhn(n))
    return T, SQ.SeqForm(T)


@lru_cache(maxsize=None)
def leduc_instance():
    T = TR.build(G.Leduc())
    return T, SQ.SeqForm(T)


@pytest.fixture
def kuhn2():
    """Kuhn-Poker mit zwei Karten (Bube, König), von Hand gezählt.

    Zwei Austeilungen (Bube, König) und (König, Bube), je Wahrscheinlichkeit 1/2. Unter jeder Austeilung der Teilbaum: Anfang, nach Pass, Pass–Pass, Pass–Setzen, Pass–Setzen–Aufgeben,
    Pass–Setzen–Mitgehen, Setzen, Setzen–Aufgeben, Setzen–Mitgehen = 9 Knoten, davon 5 Endknoten. Gesamt 1 + 2·9 = 19 Knoten, 2·5 = 10 Endknoten. Je Spieler vier Informationsmengen
    (zwei Karten, zwei Verläufe) und 1 + 4·2 = 9 Sequenzen; reduzierte reine Strategien: erster Spieler 3 je Karte (Setzen; Passen und Aufgeben; Passen und Mitgehen) = 3² = 9,
    zweiter Spieler 4 je Karte = 4² = 16.

    Spielwert 0. Reines Gleichgewicht: erster Spieler mit dem Buben passen und aufgeben, mit dem König setzen; zweiter Spieler mit dem Buben aufgeben bzw. passen, mit dem König mitgehen bzw. setzen.
    Austeilung (Bube, König): Pass, König setzt, Bube gibt auf: −1. Austeilung (König, Bube): König setzt, Bube gibt auf: +1. Mittel 0."""
    T, SF = kuhn_instance(2)
    return {"T": T, "SF": SF, "nodes": 19, "terminals": 10, "infosets": 4, "sequences": 9, "reduced": (9, 16), "value": 0, "uniform_value": "1/8"}


@pytest.fixture
def kuhn3():
    """Kuhn-Poker mit drei Karten: 6 Austeilungen × 9 Knoten + Wurzel = 55 Knoten, 30 Endknoten; je Spieler 6 Informationsmengen, 13 Sequenzen, 27 bzw. 64 reduzierte Strategien (3³, 4³).

    Spielwert −1/18 an den ersten Spieler (Kuhn 1950, hier auf drei Wegen nachgerechnet)."""
    T, SF = kuhn_instance(3)
    return {"T": T, "SF": SF, "nodes": 55, "terminals": 30, "infosets": 6, "sequences": 13, "reduced": (27, 64)}


@pytest.fixture
def leduc():
    T, SF = leduc_instance()
    return {"T": T, "SF": SF}
