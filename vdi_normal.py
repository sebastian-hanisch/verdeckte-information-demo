"""Normalform eines Baumspiels: reduzierte reine Strategien, ihre Zahl und die Auszahlungsmatrix; dazu Regret Matching auf der Matrix (Vergleich zu CFR auf dem Baum).

Eine reduzierte reine Strategie legt für jede Informationsmenge, die sie selbst erreichen kann, eine Aktion fest (Entscheidungen hinter einer selbst verworfenen Aktion zählen nicht).
Ihre Zahl wächst mit der Karten- und Zugzahl exponentiell; die Sequenzform (vdi_seqform) umgeht die Matrix."""

import itertools

import numpy as np


def _children_of_sequence(T, SF, p):
    kinder = {}
    for i in range(T.ninfo[p]):
        kinder.setdefault(SF.ipar[p][i], []).append(i)
    return kinder


def reduced_count(T, SF, p: int) -> int:
    """Zahl der reduzierten reinen Strategien von Spieler p: R(I) = Summe über die Aktionen a von Produkt R(J) über die Informationsmengen J direkt hinter (I, a); gesamt das Produkt der obersten."""
    kinder = _children_of_sequence(T, SF, p)
    memo = {}

    def R(i):
        if i not in memo:
            tot = 0
            for a in range(T.nact[p][i]):
                pr = 1
                for j in kinder.get(SF.seqid[p][(i, a)], []):
                    pr *= R(j)
                tot += pr
            memo[i] = tot
        return memo[i]

    res = 1
    for i in kinder.get(0, []):
        res *= R(i)
    return res


def reduced_plans(T, SF, p: int) -> list[dict]:
    """Alle reduzierten reinen Strategien von Spieler p als Wörterbücher {Informationsmenge: Aktion}."""
    kinder = _children_of_sequence(T, SF, p)

    def plans_info(i):
        out = []
        for a in range(T.nact[p][i]):
            subs = [plans_info(j) for j in kinder.get(SF.seqid[p][(i, a)], [])]
            for combo in itertools.product(*subs):
                d = {i: a}
                for cmb in combo:
                    d.update(cmb)
                out.append(d)
        return out

    tops = [plans_info(i) for i in kinder.get(0, [])]
    res = []
    for combo in itertools.product(*tops):
        d = {}
        for cmb in combo:
            d.update(cmb)
        res.append(d)
    return res


def plan_realization(SF, plan: dict, p: int) -> np.ndarray:
    """Realisierungsplan einer reinen Strategie: 1 für jede Sequenz (I, a), bei der der Plan in I die Aktion a wählt, sonst 0 (leere Sequenz: 1)."""
    x = np.zeros(SF.n[p])
    x[0] = 1.0
    for i, a in plan.items():
        x[SF.seqid[p][(i, a)]] = 1.0
    return x


def normal_matrix(T, SF):
    """Normalform-Auszahlungsmatrix M = X·A·Yᵀ (Zeilen: reduzierte Strategien von Spieler 0, Spalten: von Spieler 1) und die beiden Planlisten. Über Realisierungspläne gerechnet."""
    P0, P1 = reduced_plans(T, SF, 0), reduced_plans(T, SF, 1)
    X = np.array([plan_realization(SF, pl, 0) for pl in P0])
    Y = np.array([plan_realization(SF, pl, 1) for pl in P1])
    return X @ SF.dense_A() @ Y.T, P0, P1


def matrix_game(M):
    """Spielwert und optimale gemischte Strategie des Zeilenspielers eines Matrixspiels (HiGHS): (v, x)."""
    from scipy import optimize
    M = np.asarray(M, float)
    m, n = M.shape
    c = np.zeros(m + 1)
    c[-1] = -1.0
    res = optimize.linprog(c, A_ub=np.hstack([-M.T, np.ones((n, 1))]), b_ub=np.zeros(n), A_eq=[np.concatenate([np.ones(m), [0.0]])], b_eq=[1.0],
                           bounds=[(0, None)] * m + [(None, None)], method="highs")
    if res.status != 0:
        raise RuntimeError(f"Matrixspiel nicht gelöst: {res.message}")
    return float(res.x[-1]), res.x[:m]


def regret_matching_normal(M, v0: float, steps: int, checkpoints, plus: bool = False):
    """Regret Matching (optional RM⁺: Regrets auf ≥ 0 gekappt, lineare Mittelung) beider Seiten auf der Matrix M (Zeilenspieler maximiert).

    Rückgabe: Liste (Schritt, größere Lücke, Summe der Lücken) der Durchschnittsstrategie an den Prüfpunkten; Lücke 0 = v0 − min_j (xᵀM)_j, Lücke 1 = max_i (M y)_i − v0."""
    M = np.asarray(M, float)
    m, n = M.shape
    r0, r1 = np.zeros(m), np.zeros(n)
    s0, s1 = np.zeros(m), np.zeros(n)
    out = []
    marks = set(checkpoints)
    for t in range(1, steps + 1):
        p0 = np.maximum(r0, 0)
        p0 = p0 / p0.sum() if p0.sum() > 0 else np.full(m, 1.0 / m)
        p1 = np.maximum(r1, 0)
        p1 = p1 / p1.sum() if p1.sum() > 0 else np.full(n, 1.0 / n)
        u0 = M @ p1
        u1 = -(p0 @ M)
        r0 += u0 - p0 @ u0
        r1 += u1 - p1 @ u1
        if plus:
            r0 = np.maximum(r0, 0)
            r1 = np.maximum(r1, 0)
        w = float(t) if plus else 1.0
        s0 += w * p0
        s1 += w * p1
        if t in marks:
            x, y = s0 / s0.sum(), s1 / s1.sum()
            g0, g1 = v0 - float((x @ M).min()), float((M @ y).max()) - v0
            out.append((t, max(g0, g1), g0 + g1))
    return out


def normal_matrix_exact(SF, P0, P1):
    """Normalform-Auszahlungsmatrix in Brüchen (Zeilen Pläne von Spieler 0, Spalten Pläne von Spieler 1): Summe der Einträge von A über die vom Plan gespielten Sequenzen."""
    S0 = [{0} | {SF.seqid[0][(i, a)] for i, a in pl.items()} for pl in P0]
    S1 = [{0} | {SF.seqid[1][(i, a)] for i, a in pl.items()} for pl in P1]
    cells = list(SF.A.items())
    return [[sum((v for (a, b), v in cells if a in s0 and b in s1), start=0) for s1 in S1] for s0 in S0]
