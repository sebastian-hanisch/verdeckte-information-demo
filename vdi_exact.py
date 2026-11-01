"""Exakte lineare Programme in Brüchen: Zwei-Phasen-Simplex mit Blandscher Regel, dazu die Sequenzform-LPs, die Gleichgewichtsbereiche und die Verbote.

Gedacht für kleine Instanzen (Kuhn mit bis zu sechs Karten, Anmeldung und Kontrolle): dort liefert das LP den Spielwert als Bruch ohne Rundung. Große Bäume (Leduc) rechnet
vdi_seqform.solve_lp in Gleitkomma. Der Simplex ist hier der Kern, scipy erscheint nur in den Orakel-Tests und in der Gleitkomma-Fassung."""

from fractions import Fraction as Fr


def lp_max(c, A_ub, b_ub, A_eq, b_eq):
    """max c·x unter A_ub x ≤ b_ub, A_eq x = b_eq, x ≥ 0; alles Brüche. Rückgabe (Wert, x) oder None, wenn unzulässig. Unbeschränkte Programme kommen in der Demo nicht vor (AssertionError)."""
    n = len(c)
    rows, rhs, kind = [], [], []
    for a, b in zip(A_ub, b_ub):
        rows.append(list(a))
        rhs.append(b)
        kind.append("ub")
    for a, b in zip(A_eq, b_eq):
        rows.append(list(a))
        rhs.append(b)
        kind.append("eq")
    mr = len(rows)
    nsl = sum(1 for kd in kind if kd == "ub")
    ncol = n + nsl + mr
    tab = []
    si = 0
    for i in range(mr):
        row = [Fr(0)] * (ncol + 1)
        for j in range(n):
            row[j] = Fr(rows[i][j])
        if kind[i] == "ub":
            row[n + si] = Fr(1)
            si += 1
        row[-1] = Fr(rhs[i])
        if row[-1] < 0:
            row = [-v for v in row]
        row[n + nsl + i] = Fr(1)
        tab.append(row)
    basis = [n + nsl + i for i in range(mr)]

    def pivot(r, col):
        pv = tab[r][col]
        tab[r] = [v / pv for v in tab[r]]
        for i in range(mr):
            if i != r and tab[i][col] != 0:
                f = tab[i][col]
                tab[i] = [a - f * b for a, b in zip(tab[i], tab[r])]
        basis[r] = col

    def run(cost, allowed):
        while True:
            z = [cost[j] - sum(cost[basis[i]] * tab[i][j] for i in range(mr)) for j in range(ncol)]
            ent = next((j for j in allowed if z[j] < 0), None)
            if ent is None:
                return True
            cand = [(tab[i][-1] / tab[i][ent], basis[i], i) for i in range(mr) if tab[i][ent] > 0]
            assert cand, "unbeschränktes Programm"
            pivot(min(cand)[2], ent)

    run([Fr(0)] * (n + nsl) + [Fr(1)] * mr, list(range(ncol)))
    if sum(tab[i][-1] for i in range(mr) if basis[i] >= n + nsl) != 0:
        return None
    for i in range(mr):
        if basis[i] >= n + nsl:
            ent = next((j for j in range(n + nsl) if tab[i][j] != 0), None)
            if ent is not None:
                pivot(i, ent)
    run([-Fr(v) for v in c] + [Fr(0)] * (nsl + mr), list(range(n + nsl)))
    x = [Fr(0)] * n
    for i in range(mr):
        if basis[i] < n:
            x[basis[i]] = tab[i][-1]
    return sum(Fr(ci) * xi for ci, xi in zip(c, x)), x


def seq_rows(SF, p, v_fix=None, zero_seqs=()):
    """Zeilen des Sequenzform-LP aus Sicht des Maximierers p. Variablen: x (Sequenzen von p), q⁺, q⁻ (Dualvariablen, q = q⁺ − q⁻).

    v_fix: der Maximierer soll mindestens diesen Wert garantieren (q₀ ≥ v_fix); zero_seqs: Sequenzen, die mit Wahrscheinlichkeit 0 gespielt werden müssen (Verbote).
    Rückgabe (n, rq, Zahl der Variablen, A_ub, b_ub, A_eq, b_eq)."""
    A = SF.A
    n0, n1 = SF.n
    if p == 0:
        Am = [[A.get((a, b), Fr(0)) for b in range(n1)] for a in range(n0)]
        E, F = SF.E, SF.F
    else:
        Am = [[-A.get((a, b), Fr(0)) for a in range(n0)] for b in range(n1)]
        E, F = SF.F, SF.E
    n, m = len(Am), len(Am[0])
    rq = F.shape[0]
    nv = n + 2 * rq
    A_ub, b_ub = [], []
    for j in range(m):
        row = [Fr(0)] * nv
        for a in range(n):
            row[a] = -Am[a][j]
        for r in range(rq):
            row[n + r] = Fr(int(F[r, j]))
            row[n + rq + r] = -Fr(int(F[r, j]))
        A_ub.append(row)
        b_ub.append(Fr(0))
    A_eq = [[Fr(int(v)) for v in E[r]] + [Fr(0)] * (2 * rq) for r in range(E.shape[0])]
    b_eq = [Fr(1)] + [Fr(0)] * (E.shape[0] - 1)
    for s in zero_seqs:
        row = [Fr(0)] * nv
        row[s] = Fr(1)
        A_eq.append(row)
        b_eq.append(Fr(0))
    if v_fix is not None:
        row = [Fr(0)] * nv
        row[n] = Fr(-1)
        row[n + rq] = Fr(1)
        A_ub.append(row)
        b_ub.append(-Fr(v_fix))
    return n, rq, nv, A_ub, b_ub, A_eq, b_eq


def exact_seq_lp(SF, p=0, zero_seqs=()):
    """Spielwert (aus Sicht von p, exakt) und ein optimaler Realisierungsplan; mit `zero_seqs` der beste garantierte Wert unter Verbot der Sequenzen (None, wenn unzulässig)."""
    n, rq, nv, A_ub, b_ub, A_eq, b_eq = seq_rows(SF, p, zero_seqs=zero_seqs)
    c = [Fr(0)] * nv
    c[n] = Fr(1)
    c[n + rq] = Fr(-1)
    res = lp_max(c, A_ub, b_ub, A_eq, b_eq)
    if res is None:
        return None
    return res[0], res[1][:n]


def exact_range(SF, p, v_fix, index):
    """Kleinste und größte Realisierungswahrscheinlichkeit der Sequenz `index` von Spieler p auf der Menge aller Strategien, die mindestens v_fix garantieren (exakt)."""
    n, rq, nv, A_ub, b_ub, A_eq, b_eq = seq_rows(SF, p, v_fix=v_fix)
    c = [Fr(0)] * nv
    c[index] = Fr(1)
    hi = lp_max(c, A_ub, b_ub, A_eq, b_eq)[0]
    c[index] = Fr(-1)
    lo = -lp_max(c, A_ub, b_ub, A_eq, b_eq)[0]
    return lo, hi


def exact_linear_range(SF, p, v_fix, coefs):
    """Wie exact_range für eine Linearkombination Σ coefs[s]·x[s] der Realisierungswahrscheinlichkeiten (zum Beispiel x(König, Setzen) − 3·x(Bube, Setzen))."""
    n, rq, nv, A_ub, b_ub, A_eq, b_eq = seq_rows(SF, p, v_fix=v_fix)
    c = [Fr(0)] * nv
    for k, v in coefs.items():
        c[k] = Fr(v)
    hi = lp_max(c, A_ub, b_ub, A_eq, b_eq)[0]
    c = [-v for v in c]
    lo = -lp_max(c, A_ub, b_ub, A_eq, b_eq)[0]
    return lo, hi


def matrix_game_exact(M):
    """Matrixspiel max_x min_j (xᵀM)_j in Brüchen (Zeilenspieler maximiert): (Wert, x). Zeilen und Spalten sind reine Strategien der Normalform."""
    m, n = len(M), len(M[0])
    A_ub = [[-Fr(M[i][j]) for i in range(m)] + [Fr(1), Fr(-1)] for j in range(n)]
    A_eq = [[Fr(1)] * m + [Fr(0), Fr(0)]]
    c = [Fr(0)] * m + [Fr(1), Fr(-1)]
    res = lp_max(c, A_ub, [Fr(0)] * n, A_eq, [Fr(1)])
    return res[0], res[1][:m]
