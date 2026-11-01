"""Kuhn-Poker mit drei Karten: die Gleichgewichtsfamilie, Verbote mit ihren Kosten und einfache Faustregeln (alles exakt in Brüchen).

Karten 0, 1, 2 sind Bube, Dame, König. Die Familie (Kuhn 1950, hier nachgerechnet): der erste Spieler setzt mit dem Buben mit α ∈ [0, 1/3], mit dem König mit 3α, mit der Dame passt er
und geht nach Pass–Setzen mit α + 1/3 mit; der zweite Spieler ist eindeutig (Bube nach Pass setzen 1/3, Dame gegen Setzen mitgehen 1/3, König immer setzen und mitgehen)."""

from fractions import Fraction as Fr

import vdi_exact as X
import vdi_strategy as S

CARDS = ("Bube", "Dame", "König")


def info_index(T, p: int, card: int, hist: str) -> int:
    """Nummer der Informationsmenge von Spieler p mit der Karte `card` und dem Verlauf `hist` (p = Passen, b = Setzen)."""
    return T.ikeys[p][(p, card, hist)]


def seq_index(T, SF, p: int, card: int, hist: str, action: int) -> int:
    """Index der Sequenz (Informationsmenge, Aktion) im Realisierungsplan von Spieler p."""
    return SF.seqid[p][(info_index(T, p, card, hist), action)]


def _pair(q):
    q = Fr(q)
    return [1 - q, q]


def profile(T, first_open, first_pb, second_b, second_p):
    """Strategieprofil aus vier Tabellen (Karte → Wahrscheinlichkeit der zweiten Aktion: Setzen bzw. Mitgehen):
    erster Spieler am Anfang (Setzen) und nach Pass–Setzen (Mitgehen), zweiter Spieler gegen Setzen (Mitgehen) und nach Pass (Setzen)."""
    st = [[None] * T.ninfo[0], [None] * T.ninfo[1]]
    for c in range(3):
        st[0][info_index(T, 0, c, "")] = _pair(first_open[c])
        st[0][info_index(T, 0, c, "pb")] = _pair(first_pb[c])
        st[1][info_index(T, 1, c, "b")] = _pair(second_b[c])
        st[1][info_index(T, 1, c, "p")] = _pair(second_p[c])
    return st


def family_profile(T, alpha, king=None, bluff=Fr(1, 3), call=Fr(1, 3), queen_call=None):
    """Das Profil der Familie zum Parameter α. Die Voreinstellungen sind die Familie selbst; wer `king`, `bluff`, `call` oder `queen_call` ändert, verlässt sie.
    king: Setzen des Königs im ersten Zug (Familie: 3α); bluff: der zweite Spieler setzt mit dem Buben nach Pass; call: der zweite geht mit der Dame gegen Setzen mit;
    queen_call: der erste geht mit der Dame nach Pass–Setzen mit (Familie: α + 1/3)."""
    alpha = Fr(alpha)
    king = 3 * alpha if king is None else Fr(king)
    queen_call = alpha + Fr(1, 3) if queen_call is None else Fr(queen_call)
    return profile(
        T,
        first_open=[alpha, Fr(0), king],
        first_pb=[Fr(0), queen_call, Fr(1)],
        second_b=[Fr(0), Fr(call), Fr(1)],
        second_p=[Fr(bluff), Fr(0), Fr(1)],
    )


def in_family(alpha, king, bluff, call, queen_call) -> bool:
    """Liegt die Wahl (α, König, Bluff, Mitgehen der Dame, Mitgehen der Dame nach Pass–Setzen) in der Gleichgewichtsfamilie?"""
    alpha = Fr(alpha)
    return (0 <= alpha <= Fr(1, 3) and Fr(king) == 3 * alpha and Fr(bluff) == Fr(1, 3) and Fr(call) == Fr(1, 3) and Fr(queen_call) == alpha + Fr(1, 3))


# --- Verbote ---------------------------------------------------------------------------------------------------------------------------------------
# (Schlüssel, Spieler, Beschreibung, verbotene Handlungen als (Karte, Verlauf, Aktion)); Aktion 1 = Setzen bzw. Mitgehen, 0 = Passen bzw. Aufgeben
BAN_CASES = (
    ("s1_no_bluff", 1, "Zweiter Spieler bluft nie (Bube setzt nach Pass nicht)", [(0, "p", 1)]),
    ("s1_q_never_call", 1, "Zweiter Spieler geht mit der Dame gegen Setzen nie mit", [(1, "b", 1)]),
    ("s1_q_always_call", 1, "Zweiter Spieler geht mit der Dame gegen Setzen immer mit", [(1, "b", 0)]),
    ("s1_k_no_bet", 1, "Zweiter Spieler setzt mit dem König nach Pass nie", [(2, "p", 1)]),
    ("s1_k_no_fold", 1, "Zweiter Spieler gibt mit dem König gegen Setzen nie auf (nur Mitgehen erlaubt)", [(2, "b", 0)]),
    ("s1_no_bluff_q_never", 1, "Zweiter Spieler bluft nie und geht mit der Dame nie mit", [(0, "p", 1), (1, "b", 1)]),
    ("s0_no_bluff", 0, "Erster Spieler bluft nie (Bube setzt nicht)", [(0, "", 1)]),
    ("s0_k_never_bet", 0, "Erster Spieler setzt mit dem König nie", [(2, "", 1)]),
    ("s0_k_never_pass", 0, "Erster Spieler passt mit dem König nie", [(2, "", 0)]),
    ("s0_q_never_call", 0, "Erster Spieler geht mit der Dame nach Pass–Setzen nie mit", [(1, "pb", 1)]),
    ("s0_q_always_call", 0, "Erster Spieler geht mit der Dame nach Pass–Setzen immer mit", [(1, "pb", 0)]),
    ("s0_only_k_bets", 0, "Erster Spieler setzt nur mit dem König", [(0, "", 1), (1, "", 1)]),
    ("s0_never_bet", 0, "Erster Spieler setzt im ersten Zug nie", [(0, "", 1), (1, "", 1), (2, "", 1)]),
)


def ban_sequences(T, SF, case):
    """Die verbotenen Sequenzen eines Falls als Indizes im Realisierungsplan des betroffenen Spielers."""
    _, p, _, moves = case
    return [seq_index(T, SF, p, c, h, a) for c, h, a in moves]


def game_value_exact(SF) -> Fr:
    """Spielwert an Spieler 0 (exakt aus dem Sequenzform-LP)."""
    return X.exact_seq_lp(SF, 0)[0]


def ban_cost(T, SF, case, value0: Fr):
    """Kosten eines Verbots: (garantierter Wert des beschränkten Spielers, Gleichgewichtswert minus garantierter Wert), exakt. Der Gleichgewichtswert des zweiten Spielers ist −value0."""
    p = case[1]
    res = X.exact_seq_lp(SF, p, zero_seqs=ban_sequences(T, SF, case))
    eq = value0 if p == 0 else -value0
    return res[0], eq - res[0]


# --- Faustregeln -----------------------------------------------------------------------------------------------------------------------------------
# (Name, erster Zug des ersten Spielers, Mitgehen des ersten nach Pass–Setzen, Mitgehen des zweiten gegen Setzen, Setzen des zweiten nach Pass), je Karte (Bube, Dame, König)
RULES_OF_THUMB = (
    ("immer setzen und mitgehen", [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]),
    ("immer passen und aufgeben", [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]),
    ("nur mit dem König setzen und mitgehen", [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]),
    ("mit Dame und König setzen und mitgehen", [0, 1, 1], [0, 1, 1], [0, 1, 1], [0, 1, 1]),
)


def rule_cost(T, rule, value0: Fr):
    """Kosten einer Faustregel als erster und als zweiter Spieler gespielt: (Kosten als erster, Kosten als zweiter), jeweils der Gewinn der besten Antwort des Gegners
    gegenüber dem Gleichgewichtswert. Die Regel wird für beide Plätze gleich gespielt; der jeweilige Gegner antwortet bestmöglich."""
    _, o, pb, b, p = rule
    st = profile(T, o, pb, b, p)
    b1, _ = S.best_response(T, st, 1)   # Wert des zweiten Spielers gegen die Regel des ersten
    b0, _ = S.best_response(T, st, 0)   # Wert des ersten Spielers gegen die Regel des zweiten
    return b1 - (-value0), b0 - value0


def best_pure_guarantee(M_exact, p: int) -> Fr:
    """Bester garantierter Wert mit einer reinen Strategie (kein Mischen) aus der exakten Normalform M (Zeilen Spieler 0, Spalten Spieler 1), aus Sicht von Spieler p."""
    if p == 0:
        return max(min(row) for row in M_exact)
    return max(min(-M_exact[i][j] for i in range(len(M_exact))) for j in range(len(M_exact[0])))


def equilibrium_ranges(T, SF, value0: Fr):
    """Für jede Sequenz beider Spieler die kleinste und größte Realisierungswahrscheinlichkeit auf der Menge aller Strategien, die den Spielwert garantieren (exakt)."""
    out = {0: [], 1: []}
    for p, v in ((0, value0), (1, -value0)):
        for s in range(1, SF.n[p]):
            i, a = SF.seq[p][s]
            _, card, hist = T.ilist[p][i]
            lo, hi = X.exact_range(SF, p, v, s)
            out[p].append({"seq": s, "card": card, "hist": hist, "action": a, "lo": lo, "hi": hi})
    return out
