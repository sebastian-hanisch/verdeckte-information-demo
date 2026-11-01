"""Läufe der Regret-Verfahren mit Prüfpunkten: Lücke der Durchschnittsstrategie und der letzten Iteration, Aufwand in besuchten Knoten, Steigungen.

Die Lücke ist die größere der beiden Lücken (Bestantwort gegen den Spielwert, vdi_strategy.max_gap). Prüfpunkte liegen geometrisch (Faktor 1,3) und auf 10^k und 3 · 10^k;
zwischen ihnen wird nicht gemessen. Wer eine Reihe liest, sollte nie „T größer ⇒ Lücke kleiner“ an einem einzelnen Paar von Prüfpunkten erwarten: das Mittel fällt nicht monoton."""

import math

import numpy as np

import vdi_cfr as C
import vdi_strategy as S
from vdi_rng import SplitMix64


def checkpoints(max_t: int) -> list[int]:
    """Prüfpunkte: 10 · 1,3^k (gerundet) bis max_t, dazu 10^k und 3 · 10^k (10 bis 300 000) und max_t selbst (sortiert, ohne Wiederholung)."""
    pts = {int(round(10 * 1.3 ** k)) for k in range(0, 80) if 10 * 1.3 ** k <= max_t}
    pts |= {m * 10 ** k for k in range(1, 6) for m in (1, 3) if m * 10 ** k <= max_t}
    pts.add(max_t)
    return sorted(p for p in pts if 1 <= p <= max_t)


def stream(seed: int, cell: int) -> SplitMix64:
    """Eigener Zufallsstrom je (Zufalls-Seed, Zelle): reine Ganzzahl-Arithmetik, auf jeder Plattform gleich (kein Python-hash)."""
    return SplitMix64(int(seed) * 1_000_003 + int(cell))


def run_variant(T, variant: str, steps: int, v0: float, marks=None, init_regrets=None) -> dict:
    """Ein Verfahren `variant` (vdi_cfr.VARIANTS) über `steps` Schritte. Rückgabe: Prüfpunkte `t`, `avg` (größere Lücke der Durchschnittsstrategie), `avg_sum` (Summe der beiden Lücken),
    `last` (größere Lücke der letzten Iteration), `nodes` (besuchte Knoten bis dahin)."""
    marks = checkpoints(steps) if marks is None else sorted(set(marks))
    solver = C.CFRSolver(T, variant, init_regrets=init_regrets)
    out = {"t": [], "avg": [], "avg_sum": [], "last": [], "nodes": []}
    pending = iter(marks)
    nxt = next(pending, None)
    for t in range(1, steps + 1):
        solver.step()
        if t == nxt:
            g0, g1, total = S.exploitability(T, solver.average(), v0)
            h0, h1, _ = S.exploitability(T, solver.current(), v0)
            out["t"].append(t)
            out["avg"].append(max(g0, g1))
            out["avg_sum"].append(total)
            out["last"].append(max(h0, h1))
            out["nodes"].append(solver.nodes)
            nxt = next(pending, None)
    return out


def run_sampling(T, rng, steps: int, v0: float, marks) -> dict:
    """Externes Sampling (MCCFR) mit dem Zufallsstrom `rng`. Rückgabe wie run_variant (ohne letzte Iteration)."""
    solver = C.SamplingSolver(T, rng)
    marks = sorted(set(marks))
    out = {"t": [], "avg": [], "avg_sum": [], "nodes": []}
    pending = iter(marks)
    nxt = next(pending, None)
    for t in range(1, steps + 1):
        solver.step()
        if t == nxt:
            g0, g1, total = S.exploitability(T, solver.average(), v0)
            out["t"].append(t)
            out["avg"].append(max(g0, g1))
            out["avg_sum"].append(total)
            out["nodes"].append(solver.nodes)
            nxt = next(pending, None)
    return out


def slope(ts, vals) -> float:
    """Steigung der Ausgleichsgeraden im doppelt logarithmischen Maßstab (Lücke gegen Schritte): −1 heißt Lücke ~ 1/T, −0,5 heißt Lücke ~ 1/√T."""
    x = np.log(np.asarray(ts, float))
    y = np.log(np.maximum(np.asarray(vals, float), 1e-300))
    return float(np.polyfit(x, y, 1)[0])


def slope_between(run: dict, t_lo: int, t_hi: int, key: str = "avg") -> float:
    """Steigung über die Prüfpunkte mit t_lo ≤ t ≤ t_hi."""
    pts = [(t, v) for t, v in zip(run["t"], run[key]) if t_lo <= t <= t_hi]
    return slope([p[0] for p in pts], [p[1] for p in pts])


def first_below(run: dict, eps: float, key: str = "avg"):
    """Erster Prüfpunkt, an dem die Lücke höchstens eps ist: (t, besuchte Knoten) oder None."""
    for t, v, n in zip(run["t"], run[key], run["nodes"]):
        if v <= eps:
            return t, n
    return None


def value_at(run: dict, t: int, key: str = "avg") -> float:
    """Wert an einem Prüfpunkt (der Punkt muss in der Reihe liegen)."""
    return run[key][run["t"].index(t)]


def count_increases(run: dict, key: str = "avg") -> int:
    """Wie oft ist die Lücke von einem Prüfpunkt zum nächsten gestiegen?"""
    v = run[key]
    return sum(1 for a, b in zip(v, v[1:]) if b > a)


def mean_sd(values) -> dict:
    """Mittel und Standardabweichung (ddof = 1) über die Zufalls-Seeds."""
    v = [float(x) for x in values]
    mean = math.fsum(v) / len(v)
    sd = math.sqrt(math.fsum((x - mean) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return {"mean": mean, "sd": sd, "values": v}
