"""Einheiten an Mini-Instanzen, Handrechnung im Docstring: Spiele, Baum, Strategiewerte, Sequenzform, Normalform, Regret-Einheiten, exakter Simplex, Anmeldung."""

from fractions import Fraction as F

import numpy as np
import pytest

import vdi_anmeldung as AN
import vdi_cfr as C
import vdi_exact as X
import vdi_games as G
import vdi_normal as N
import vdi_seqform as SQ
import vdi_strategy as S
import vdi_tree as TR
from vdi_rng import SplitMix64


# --- Spiele und Baum -------------------------------------------------------------------------------------------------------------------------------
def test_kuhn2_has_the_hand_counted_sizes(kuhn2):
    T, SF = kuhn2["T"], kuhn2["SF"]
    assert (T.n, T.nterm, T.ninfo, SF.n) == (19, 10, [4, 4], [9, 9])
    assert (N.reduced_count(T, SF, 0), N.reduced_count(T, SF, 1)) == kuhn2["reduced"]
    assert TR.perfect_recall(T)


def test_kuhn3_has_the_hand_counted_sizes(kuhn3):
    T, SF = kuhn3["T"], kuhn3["SF"]
    assert (T.n, T.nterm, T.ninfo, SF.n) == (55, 30, [6, 6], [13, 13])
    assert (N.reduced_count(T, SF, 0), N.reduced_count(T, SF, 1)) == kuhn3["reduced"]


def test_kuhn_payoffs_of_every_ending_by_hand():
    """Karten (0, 1) = Bube gegen Dame. Pass–Pass: Vergleich, Einsatz 1 → −1. Setzen–Aufgeben: erster gewinnt 1. Setzen–Mitgehen: −2 (Dame höher). Pass–Setzen–Aufgeben: erster verliert 1.
    Pass–Setzen–Mitgehen: −2."""
    g = G.Kuhn(3)
    pay = {h: g.payoff0(((0, 1), h)) for h in G.KUHN_TERMINALS}
    assert pay == {"pp": -1, "bp": 1, "bb": -2, "pbp": -1, "pbb": -2}
    assert g.payoff0(((2, 1), "bb")) == 2 and g.payoff0(((2, 1), "pp")) == 1


def test_card_names():
    assert G.card_names(2) == ["Bube", "König"] and G.card_names(3) == ["Bube", "Dame", "König"] and G.card_names(5) == ["1", "2", "3", "4", "5"]


def test_leduc_terminal_count_matches_a_hand_derivation(leduc):
    """Eine Runde hat neun Setzfolgen (cc, crf, crc, crrf, crrc, rf, rc, rrf, rrc), davon enden vier mit Aufgeben. Private Ränge: 9 geordnete Paare; öffentliche Karte: 2 mögliche Ränge bei
    gleichen privaten Rängen (3 Paare), sonst 3 (6 Paare) = 24 Kombinationen. Endknoten: 9 Paare × 4 Aufgabefolgen der Runde 1 + 24 × 5 weiter × 9 Folgen der Runde 2 = 36 + 1080 = 1116."""
    T = leduc["T"]
    assert T.nterm == 9 * 4 + 24 * 5 * 9 == 1116 and T.n == 1939 and T.ninfo == [144, 144]
    assert TR.perfect_recall(T)


def test_leduc_betting_arithmetic():
    """Erhöhen in Runde 1: Einsatz 1 + 2 = 3; zweite Erhöhung 3 + 2 = 5; Mitgehen gleicht aus. In Runde 2 ist die Einsatzgröße 4: r, r, c → beide bei 1 + 4 + 4 = 9."""
    g = G.Leduc()
    s = ((2, 0), 1, 2, "", 1, 1, "cc")
    for a in "rrc":
        s = g.child(s, a)
    assert (s[4], s[5]) == (9, 9)
    s1 = ((0, 1), None, 1, "", 1, 1, "")
    for a in "rr":
        s1 = g.child(s1, a)
    assert (s1[4], s1[5]) == (3, 5) and g.actions(s1) == ("f", "c")


def test_leduc_payoffs_by_hand():
    """Der König (Rang 2) gegen den Buben (0) mit öffentlichem Dame (1) und Einsätzen 9/9 gewinnt 9. Ein Paar schlägt den höheren Rang: privat (0, 2), öffentlich 0 → Spieler 0 gewinnt 1.
    Gleicher Rang teilt (0). Aufgeben von Spieler 1 nach einer Erhöhung von Spieler 0 (Einsätze 3/1): Spieler 0 gewinnt 1."""
    g = G.Leduc()
    assert g.payoff0(((2, 0), 1, 2, "rrc", 9, 9, "cc")) == 9
    assert g.payoff0(((0, 2), 0, 2, "cc", 1, 1, "cc")) == 1
    assert g.payoff0(((1, 1), 0, 2, "cc", 1, 1, "cc")) == 0
    assert g.payoff0(((0, 1), None, 1, "rf", 3, 1, "")) == 1
    assert g.payoff0(((0, 2), 1, 2, "cc", 1, 1, "cc")) == -1


def test_anmeldung_payoffs_by_hand():
    """Standard b 10, c 2, f 1, g 15, s 20, r 6: in Ordnung und „sauber“ gemeldet: 10 (durchlassen) bzw. 12 (Kontrolle). Riskant, „sauber“: 15 bzw. −20. Riskant, „riskant“: 6 bzw. 8."""
    g = G.Anmeldung()
    cases = {("ok", "S", "P"): 10, ("ok", "S", "K"): 12, ("ok", "R", "P"): 9, ("riskant", "S", "P"): 15, ("riskant", "S", "K"): -20, ("riskant", "R", "P"): 6, ("riskant", "R", "K"): 8}
    for s, v in cases.items():
        assert g.payoff0(s) == v


# --- Strategiewerte und beste Antwort ----------------------------------------------------------------------------------------------------------------
def test_uniform_profile_value_of_kuhn2_is_one_eighth(kuhn2):
    """Austeilung mit Vorzeichen hi (+1 wenn der erste die höhere Karte hat): Pass (1/2): 1/2·hi + 1/2·(1/2·(−1) + 1/2·2hi) = hi − 1/4; Setzen (1/2): 1/2·1 + 1/2·2hi = 1/2 + hi.
    Mittel 1/2(hi − 1/4) + 1/2(1/2 + hi) = hi + 1/8; über hi = ±1 gleich häufig: 1/8."""
    T = kuhn2["T"]
    assert S.profile_value(T, S.uniform_strategy(T)) == F(1, 8)
    assert S.profile_value(T, S.uniform_strategy(T, exact=False)) == pytest.approx(1 / 8)


def test_best_response_to_always_bet_in_kuhn2(kuhn2):
    """Der erste Spieler setzt immer. Der zweite gibt mit dem Buben auf (−1 für ihn) und geht mit dem König mit (+2): Mittel (−1 + 2)/2 = 1/2. Beste Antwort des zweiten Spielers: 1/2."""
    T = kuhn2["T"]
    st = S.uniform_strategy(T)
    for i in range(T.ninfo[0]):
        st[0][i] = [F(0), F(1)]
    value, choice = S.best_response(T, st, 1)
    assert value == F(1, 2)
    j_bet = T.ikeys[1][(1, 0, "b")]
    k_bet = T.ikeys[1][(1, 1, "b")]
    assert choice[j_bet] == 0 and choice[k_bet] == 1


def test_hand_pure_equilibrium_of_kuhn2_has_zero_gaps(kuhn2):
    T = kuhn2["T"]
    st = [[None] * 4, [None] * 4]
    for c in (0, 1):
        st[0][T.ikeys[0][(0, c, "")]] = [F(1 - c), F(c)]        # Bube passt, König setzt
        st[0][T.ikeys[0][(0, c, "pb")]] = [F(1 - c), F(c)]      # Bube gibt auf, König geht mit
        st[1][T.ikeys[1][(1, c, "b")]] = [F(1 - c), F(c)]       # Bube gibt auf, König geht mit
        st[1][T.ikeys[1][(1, c, "p")]] = [F(1 - c), F(c)]       # Bube passt, König setzt
    assert S.profile_value(T, st) == 0
    assert S.exploitability(T, st, F(0)) == (0, 0, 0)


def test_exploitability_sum_does_not_need_the_game_value(kuhn2):
    T = kuhn2["T"]
    st = S.uniform_strategy(T)
    g0, g1, total = S.exploitability(T, st, F(0))
    assert total == g0 + g1 and total > 0


# --- Sequenzform -----------------------------------------------------------------------------------------------------------------------------------
def test_sequence_constraints_of_kuhn2(kuhn2):
    """E hat eine Zeile für die leere Sequenz und eine je Informationsmenge: x(leer) = 1 und x(Eltern) = Summe der Aktionen. Ein Realisierungsplan der Gleichverteilung erfüllt E·x = e:
    zum Beispiel x(Bube, Setzen) = 1/2 und x(Bube, Passen) = 1/2, nach Passen und Setzen des Gegners je 1/4."""
    T, SF = kuhn2["T"], kuhn2["SF"]
    assert SF.E.shape == (5, 9) and SF.F.shape == (5, 9)
    x = SQ.behavior_to_realization(SF, S.uniform_strategy(T)[0], 0)
    e = np.zeros(5)
    e[0] = 1
    assert np.allclose(SF.E @ np.array([float(v) for v in x]), e)
    first = T.ikeys[0][(0, 0, "")]
    assert x[SF.seqid[0][(first, 1)]] == F(1, 2)
    after = T.ikeys[0][(0, 0, "pb")]
    assert x[SF.seqid[0][(after, 0)]] == F(1, 4)


def test_realization_and_behavior_are_inverse(kuhn3):
    T, SF = kuhn3["T"], kuhn3["SF"]
    st = S.uniform_strategy(T)
    st[0][2] = [F(1, 5), F(4, 5)]
    for p in (0, 1):
        x = SQ.behavior_to_realization(SF, st[p], p)
        back = SQ.realization_to_behavior(SF, [float(v) for v in x], p)
        assert np.allclose(back, [[float(v) for v in row] for row in st[p]])


def test_payoff_matrix_entry_by_hand(kuhn2):
    """Sequenz (Bube, Setzen) des ersten gegen (König, Aufgeben) des zweiten: nur die Austeilung (Bube, König) mit Wahrscheinlichkeit 1/2, Auszahlung +1: Eintrag 1/2."""
    T, SF = kuhn2["T"], kuhn2["SF"]
    s0 = SF.seqid[0][(T.ikeys[0][(0, 0, "")], 1)]
    s1 = SF.seqid[1][(T.ikeys[1][(1, 1, "b")], 0)]
    assert SF.A[(s0, s1)] == F(1, 2)


# --- Normalform ------------------------------------------------------------------------------------------------------------------------------------
def test_reduced_plans_of_kuhn2_cover_all_choices(kuhn2):
    T, SF = kuhn2["T"], kuhn2["SF"]
    plans0 = N.reduced_plans(T, SF, 0)
    assert len(plans0) == 9
    # ein Plan entscheidet nach Passen nur dann über Aufgeben/Mitgehen, wenn er mit der Karte zuerst Passen wählt
    for pl in plans0:
        for c in (0, 1):
            i, j = T.ikeys[0][(0, c, "")], T.ikeys[0][(0, c, "pb")]
            assert (j in pl) == (pl[i] == 0)


def test_plan_realization_marks_exactly_the_played_sequences(kuhn2):
    T, SF = kuhn2["T"], kuhn2["SF"]
    plan = {T.ikeys[0][(0, 0, "")]: 0, T.ikeys[0][(0, 0, "pb")]: 1, T.ikeys[0][(0, 1, "")]: 1}
    x = N.plan_realization(SF, plan, 0)
    assert x[0] == 1 and x.sum() == 4   # leere Sequenz + drei gespielte


def test_regret_matching_on_a_matrix_game_finds_rock_paper_scissors():
    """Stein–Schere–Papier hat den Wert 0; Regret Matching mit Durchschnitt nähert sich der Gleichverteilung (Lücke unter 0,05 bei 2000 Schritten)."""
    M = np.array([[0, -1, 1], [1, 0, -1], [-1, 1, 0]], float)
    out = N.regret_matching_normal(M, 0.0, 2000, [2000])
    assert out[0][1] < 0.05


# --- Regret-Einheiten ------------------------------------------------------------------------------------------------------------------------------
def test_regret_matching_probs():
    assert C.regret_matching_probs([3.0, 1.0, -2.0]) == pytest.approx([0.75, 0.25, 0.0])
    assert C.regret_matching_probs([-1.0, -2.0]) == [0.5, 0.5]
    assert C.regret_matching_probs([0.0, 0.0, 0.0]) == pytest.approx([1 / 3] * 3)


def test_clip_regrets():
    reg = [[1.0, -2.0], [0.0, -0.5]]
    C.clip_regrets(reg)
    assert reg == [[1.0, 0.0], [0.0, 0.0]]


def test_discount_factors_at_t1_and_t2():
    """α = 3/2, β = 0, γ = 2. t = 1: positive 1/(1+1) = 1/2, negative 1/(1+1) = 1/2, Summe ((1−1)/1)² nicht angewandt (Faktor 1). t = 2: positive 2^1,5/(2^1,5 + 1), negative 1/2, Summe (1/2)² = 1/4."""
    reg, avg = [[4.0, -4.0]], [[8.0, 8.0]]
    C.apply_discount(reg, avg, 1)
    assert reg == [[2.0, -2.0]] and avg == [[8.0, 8.0]]
    reg, avg = [[4.0, -4.0]], [[8.0, 8.0]]
    C.apply_discount(reg, avg, 2)
    assert reg[0][0] == pytest.approx(4.0 * 2 ** 1.5 / (2 ** 1.5 + 1)) and reg[0][1] == pytest.approx(-2.0) and avg == [[2.0, 2.0]]


def test_first_cfr_iteration_of_kuhn2_by_hand(kuhn2):
    """Zweiter Spieler mit dem Buben gegen Setzen (Aufgeben, Mitgehen). Gleichverteilter Start. Erreichbarkeit für Gegner und Zufall: der König muss beim ersten sein (1/2) und setzen (1/2) = 1/4.
    Gegenwerte aus Sicht des zweiten Spielers: Aufgeben −1, Mitgehen −2, Mittel −3/2. Regret = 1/4 · (−1 + 3/2, −2 + 3/2) = (1/8, −1/8)."""
    T = kuhn2["T"]
    solver = C.CFRSolver(T, "cfr")
    solver.step()
    assert solver.reg[1][T.ikeys[1][(1, 0, "b")]] == pytest.approx([1 / 8, -1 / 8])
    # Strategiesumme: Gewicht 1 · eigene Erreichbarkeit (1, der Spieler hat vorher nicht entschieden; Zufall und Gegner zählen nicht) · σ = (1/2, 1/2); die Menge hat nur einen Knoten
    assert solver.avg[1][T.ikeys[1][(1, 0, "b")]] == pytest.approx([1 / 2, 1 / 2])


def test_external_sampling_pass_with_a_fixed_stream_by_hand(kuhn2):
    """Strom, der immer 0 liefert: gezogen wird stets die erste mögliche Aktion. Austeilung (Bube, König). Spieler 0 am Zug mit dem Buben (Regrets 0 → gleichverteilt): beide Aktionen
    werden besucht. Passen: der Gegner zieht Passen → Pass–Pass, Auszahlung −1. Setzen: der Gegner zieht Aufgeben → +1. Wert 0, Regrets (−1 − 0, +1 − 0) = (−1, 1),
    Strategiesumme des Gegners (1/2, 1/2) an beiden Stellen. Besuchte Knoten: Wurzel, Austeilung, Passen, Pass–Pass, Setzen, Setzen–Aufgeben = 6."""
    class Zero:
        @staticmethod
        def uniform():
            return 0.0
    T = kuhn2["T"]
    reg, avg = C.zero_tables(T)
    value, visited = C.external_sampling_pass(T, reg, avg, Zero(), 0)
    assert value == 0.0 and visited == 6
    assert reg[0][T.ikeys[0][(0, 0, "")]] == [-1.0, 1.0]
    assert avg[1][T.ikeys[1][(1, 1, "p")]] == [0.5, 0.5] and avg[1][T.ikeys[1][(1, 1, "b")]] == [0.5, 0.5]


def test_sampling_solver_uses_only_the_given_stream(kuhn3):
    T = kuhn3["T"]
    a, b = C.SamplingSolver(T, SplitMix64(5)), C.SamplingSolver(T, SplitMix64(5))
    for _ in range(50):
        a.step()
        b.step()
    assert a.reg == b.reg and a.avg == b.avg and a.nodes == b.nodes


def test_random_start_regrets_come_from_the_stream(kuhn3):
    T = kuhn3["T"]
    r1, r2 = C.random_regrets(T, SplitMix64(3)), C.random_regrets(T, SplitMix64(3))
    assert r1 == r2 and all(0.0 <= x < 1.0 for p in r1 for row in p for x in row)
    assert r1 != C.random_regrets(T, SplitMix64(4))


# --- exakter Simplex -------------------------------------------------------------------------------------------------------------------------------
def test_exact_simplex_small_programs():
    """max x + y, x ≤ 1/2, y ≤ 1/3: Wert 5/6. Gleichung x + y = 1 mit x ≤ 1/4 ist unzulässig, wenn zusätzlich y ≤ 1/2."""
    value, x = X.lp_max([1, 1], [[1, 0], [0, 1]], [F(1, 2), F(1, 3)], [], [])
    assert value == F(5, 6) and x == [F(1, 2), F(1, 3)]
    assert X.lp_max([1, 0], [[1, 0], [0, 1]], [F(1, 4), F(1, 2)], [[1, 1]], [1]) is None


def test_exact_matrix_game_matching_pennies_and_a_saddle_point():
    assert X.matrix_game_exact([[1, -1], [-1, 1]])[0] == 0
    assert X.matrix_game_exact([[3, 2], [1, 0]])[0] == 2          # Sattelpunkt: Zeile 0, Spalte 1
    value, x = X.matrix_game_exact([[2, 0], [0, 1]])
    assert value == F(2, 3) and x == [F(1, 3), F(2, 3)]           # 2x = (1 − x) → x = 1/3, Wert 2/3


# --- Anmeldung -------------------------------------------------------------------------------------------------------------------------------------
def test_anmeldung_standard_closed_form_by_hand():
    """b 10, c 2, g 15, s 20, r 6, p 3/10. μ* = 2/(2 + 15 + 20) = 2/37 < 3/10, also gemischt. λ = 2·(7/10)/((3/10)·35) = (7/5)/(21/2) = 2/15. κ = (15 − 6)/35 = 9/35.
    Wert = (7/10)(10 + 2·9/35) + (3/10)·6 = 7 + (7/10)(18/35) + 9/5 = 7 + 9/25 + 9/5 = 229/25."""
    lam, kap, value, regime = AN.closed_form(G.Anmeldung().par)
    assert (lam, kap, value, regime) == (F(2, 15), F(9, 35), F(229, 25), "gemischt")
    assert AN.threshold(G.Anmeldung().par) == F(2, 37)


def test_anmeldung_regimes():
    par = G.Anmeldung(p=F(1, 20)).par                      # 1/20 < 2/37: alle lügen
    assert AN.closed_form(par) == (1, 0, F(19, 20) * 10 + F(1, 20) * 15, "alle lügen")
    par = G.Anmeldung(g=5).par                             # g ≤ r: ehrlich
    assert AN.closed_form(par) == (0, 0, F(7, 10) * 10 + F(3, 10) * 6, "ehrlich")
