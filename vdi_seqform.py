"""Sequenzform (Koller, Megiddo, von Stengel): ein Spiel mit Zügen nacheinander als lineares Programm, dessen Größe mit dem Baum wächst, nicht mit der Zahl reiner Strategien.

Eine Sequenz eines Spielers ist die Folge seiner eigenen Entscheidungen bis zu einer Stelle (Paare aus Informationsmenge und Aktion). Ein Realisierungsplan x ordnet jeder Sequenz die
Wahrscheinlichkeit zu, mit der der Spieler sie spielt, wenn die anderen mitspielen; er erfüllt E·x = e. Die Auszahlungsmatrix A (Zeilen Sequenzen von Spieler 0, Spalten Sequenzen von
Spieler 1) enthält die mit dem Zufall gewichteten Auszahlungen der Endknoten. Das LP dieser Datei rechnet in Gleitkomma (HiGHS); die exakte Fassung in Brüchen steht in vdi_exact."""

from fractions import Fraction as Fr

import numpy as np


class SeqForm:
    """Sequenzen `seq[p]` (Index 0 ist die leere Sequenz, sonst (Informationsmenge, Aktion)), `seqid[p]` (Paar → Index), `ipar[p]` (Informationsmenge → Elternsequenz), die Matrizen
    `E`, `F` (Nebenbedingungen der Realisierungspläne, ganzzahlig) und `A` (Wörterbuch (s0, s1) → Bruch) sowie die Zahl der Sequenzen `n`."""

    def __init__(self, T):
        self.T = T
        seqid = [{(): 0}, {(): 0}]
        seq = [[None], [None]]
        ipar = [{}, {}]
        A = {}
        stack = [(0, 0, 0, Fr(1))]
        while stack:
            h, s0, s1, cw = stack.pop()
            k = T.kind[h]
            if k == "t":
                A[(s0, s1)] = A.get((s0, s1), Fr(0)) + cw * T.pay[h]
                continue
            if k == "c":
                for pr, c in zip(T.prob[h], T.kids[h]):
                    stack.append((c, s0, s1, cw * pr))
                continue
            p = T.player[h]
            i = T.info[h]
            cur = (s0, s1)[p]
            if i in ipar[p]:
                assert ipar[p][i] == cur, "kein perfektes Erinnern"
            else:
                ipar[p][i] = cur
            for a, c in enumerate(T.kids[h]):
                key = (i, a)
                if key not in seqid[p]:
                    seqid[p][key] = len(seq[p])
                    seq[p].append(key)
                sid = seqid[p][key]
                stack.append((c, sid, s1, cw) if p == 0 else (c, s0, sid, cw))
        self.seqid, self.seq, self.ipar, self.A = seqid, seq, ipar, A
        self.n = [len(seq[0]), len(seq[1])]
        mats = []
        for p in (0, 1):
            M = np.zeros((1 + T.ninfo[p], self.n[p]), dtype=np.int64)
            M[0, 0] = 1
            for i in range(T.ninfo[p]):
                M[1 + i, ipar[p][i]] = -1
                for a in range(T.nact[p][i]):
                    M[1 + i, seqid[p][(i, a)]] = 1
            mats.append(M)
        self.E, self.F = mats

    def dense_A(self):
        """Auszahlungsmatrix als Gleitkomma-Feld (Zeilen Sequenzen von Spieler 0, Spalten Sequenzen von Spieler 1)."""
        M = np.zeros(tuple(self.n))
        for (a, b), v in self.A.items():
            M[a, b] = float(v)
        return M

    def label(self, p: int, s: int, namer=None) -> str:
        """Lesbare Bezeichnung einer Sequenz (leer, oder Schlüssel der Informationsmenge und Aktionsnummer)."""
        if s == 0:
            return "leere Sequenz"
        i, a = self.seq[p][s]
        key = self.T.ilist[p][i]
        return namer(p, key, a) if namer else f"{key}: {a}"


def sequence_count_kuhn(n: int) -> int:
    """Zahl der Sequenzen je Spieler im Kuhn-Spiel mit n Karten: 4n + 1 (die leere Sequenz, dazu je Karte zwei Informationsmengen mit je zwei Aktionen)."""
    return 4 * n + 1


def solve_lp(SF: SeqForm, p: int = 0):
    """Sequenzform-LP (HiGHS) aus Sicht des Maximierers p. Rückgabe (Wert aus Sicht von p, Realisierungsplan x von p).

    max q₀ unter E x = e, x ≥ 0, Fᵀ q ≤ Aᵀ x (für p = 1 mit −Aᵀ und vertauschten E, F). Die Rechnung steht hier ohne Brüche; die Bruchfassung ist vdi_exact.exact_seq_lp."""
    from scipy import optimize
    A = SF.dense_A()
    E, F = SF.E.astype(float), SF.F.astype(float)
    if p == 1:
        A, E, F = -A.T, F, E
    n, m = A.shape
    rq = F.shape[0]
    c = np.concatenate([np.zeros(n), -np.eye(rq)[0]])
    A_ub = np.hstack([-A.T, F.T])
    A_eq = np.hstack([E, np.zeros((E.shape[0], rq))])
    b_eq = np.zeros(E.shape[0])
    b_eq[0] = 1.0
    res = optimize.linprog(c, A_ub=A_ub, b_ub=np.zeros(m), A_eq=A_eq, b_eq=b_eq, bounds=[(0, None)] * n + [(None, None)] * rq, method="highs")
    if res.status != 0:
        raise RuntimeError(f"Sequenzform-LP nicht gelöst: {res.message}")
    return float(-res.fun), res.x[:n]


def realization_to_behavior(SF: SeqForm, x, p: int):
    """Verhaltensstrategie aus einem Realisierungsplan: σ(I, a) = x(I, a) / x(Elternsequenz von I); wo die Elternsequenz nie gespielt wird, gleichverteilt."""
    T = SF.T
    st = []
    for i in range(T.ninfo[p]):
        par = x[SF.ipar[p][i]]
        na = T.nact[p][i]
        if par > 1e-12:
            row = [max(float(x[SF.seqid[p][(i, a)]]), 0.0) / par for a in range(na)]
            tot = sum(row)
            row = [v / tot for v in row]
        else:
            row = [1.0 / na] * na
        st.append(row)
    return st


def behavior_to_realization(SF: SeqForm, st, p: int):
    """Realisierungsplan einer Verhaltensstrategie: x(I, a) = x(Elternsequenz von I) · σ(I, a), x(leer) = 1 (Informationsmengen in Vorordnung der Elternsequenzen)."""
    T = SF.T
    x = [None] * SF.n[p]
    x[0] = 1.0 if isinstance(st[0][0], float) else Fr(1)
    pending = list(range(T.ninfo[p]))
    while pending:
        rest = []
        for i in pending:
            par = x[SF.ipar[p][i]]
            if par is None:
                rest.append(i)
                continue
            for a in range(T.nact[p][i]):
                x[SF.seqid[p][(i, a)]] = par * st[i][a]
        if len(rest) == len(pending):
            raise RuntimeError("Elternsequenz nicht auflösbar")
        pending = rest
    return x
