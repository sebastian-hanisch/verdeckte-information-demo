"""Orakel-Tests (DEMO-PLAYBOOK §12): Spielwert, beste Antwort, Gleichgewichtsmenge, Verbote, Anmeldung und Leduc gegen unabhängige Rechenwege.

Unabhängig vom Kern: (1) der Wert einer reinen Strategienkombination durch direkten Baumdurchlauf, (2) die vollständige Normalform über ALLE reinen Strategien (jede Aktion in jeder
Informationsmenge, ohne Reduktion), (3) scipy/HiGHS auf dieser Normalform, (4) die Aufzählung aller reinen Strategien als beste Antwort, (5) exakte Brüche (Bruch-Simplex) und HiGHS auf
der Sequenzform. Bekannte Werte: Kuhn 1950 (−1/18 für den ersten Spieler), eigene Rechnung für n ≠ 3."""

import itertools
from fractions import Fraction as F

import numpy as np
import pytest

import vdi_anmeldung as AN
import vdi_exact as X
import vdi_games as G
import vdi_kuhn as K
import vdi_normal as N
import vdi_seqform as SQ
import vdi_strategy as S
import vdi_tree as TR
from conftest import kuhn_instance, leduc_instance
from vdi_rng import SplitMix64

optimize = pytest.importorskip("scipy.optimize")


# --- unabhängige Hilfen ----------------------------------------------------------------------------------------------------------------------------
def pure_value(T, plan0, plan1):
    """Wert einer Kombination reiner Strategien (jede Informationsmenge eine Aktion) durch direkten Baumdurchlauf (rekursiv, ohne Sequenzform)."""
    def rec(h):
        k = T.kind[h]
        if k == "t":
            return T.pay[h]
        if k == "c":
            return sum(pr * rec(c) for pr, c in zip(T.prob[h], T.kids[h]))
        plan = plan0 if T.player[h] == 0 else plan1
        return rec(T.kids[h][plan[T.info[h]]])
    return rec(0)


def all_pure_plans(T, p):
    """Alle reinen Strategien (jede Informationsmenge eine Aktion), ohne Reduktion."""
    return list(itertools.product(*[range(n) for n in T.nact[p]]))


def full_normal_form(T):
    P0, P1 = all_pure_plans(T, 0), all_pure_plans(T, 1)
    return [[pure_value(T, a, b) for b in P1] for a in P0]


def random_profile(T, rng, denom=12):
    """Zufällige Verhaltensstrategien mit Wahrscheinlichkeiten in Zwölfteln (Brüche)."""
    st = [[], []]
    for p in (0, 1):
        for n in T.nact[p]:
            cuts = sorted(int(rng.uniform() * (denom + 1)) for _ in range(n - 1))
            parts = [b - a for a, b in zip([0] + cuts, cuts + [denom])]
            st[p].append([F(x, denom) for x in parts])
    return st


def enumerate_best_response(T, st, p):
    """Beste Antwort von p als Maximum über alle reinen Strategien von p (Wert aus Sicht von p)."""
    best = None
    for plan in all_pure_plans(T, p):
        prof = [list(st[0]), list(st[1])]
        prof[p] = [[F(1) if a == k else F(0) for k in range(T.nact[p][i])] for i, a in enumerate(plan)]
        v = S.profile_value(T, prof)
        v = v if p == 0 else -v
        best = v if best is None else max(best, v)
    return best


# --- Spielwert auf mehreren Wegen --------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("n,expected", [(2, F(0)), (3, F(-1, 18))])
def test_kuhn_value_by_four_independent_ways(n, expected):
    T, SF = kuhn_instance(n)
    exact_seq, _ = X.exact_seq_lp(SF, 0)
    exact_seq1, _ = X.exact_seq_lp(SF, 1)
    full = full_normal_form(T)
    M = np.array([[float(v) for v in row] for row in full])
    m, k = M.shape
    c = np.zeros(m + 1)
    c[-1] = -1.0
    res = optimize.linprog(c, A_ub=np.hstack([-M.T, np.ones((k, 1))]), b_ub=np.zeros(k), A_eq=[np.concatenate([np.ones(m), [0.0]])], b_eq=[1.0],
                     bounds=[(0, None)] * m + [(None, None)], method="highs")
    reduced_plans = N.reduced_plans(T, SF, 0), N.reduced_plans(T, SF, 1)
    exact_nf, _ = X.matrix_game_exact(N.normal_matrix_exact(SF, *reduced_plans))
    assert exact_seq == exact_nf == expected
    assert exact_seq1 == -expected
    assert res.x[-1] == pytest.approx(float(expected), abs=1e-12)
    assert SQ.solve_lp(SF, 0)[0] == pytest.approx(float(expected), abs=1e-12)
    assert SQ.solve_lp(SF, 1)[0] == pytest.approx(-float(expected), abs=1e-12)


def test_kuhn_values_for_more_cards_exact_and_highs_agree():
    """Eigene Rechnung (nicht aus der Literatur): n = 4, 5 → −1/24, −1/15 (n = 6: −11/180, in test_measurements). Der Normalformwert für n = 4 kommt aus dem direkten Baumdurchlauf aller reduzierten Strategien."""
    expected = {4: F(-1, 24), 5: F(-1, 15)}
    for n, value in expected.items():
        T, SF = kuhn_instance(n)
        assert X.exact_seq_lp(SF, 0)[0] == value
        assert SQ.solve_lp(SF, 0)[0] == pytest.approx(float(value), abs=1e-12)
    T, SF = kuhn_instance(4)
    P0, P1 = N.reduced_plans(T, SF, 0), N.reduced_plans(T, SF, 1)
    full_plan = lambda T_, pl, p: tuple(pl.get(i, 0) for i in range(T_.ninfo[p]))   # nicht erreichbare Mengen beliebig (hier 0): ändert den Wert nicht
    M = np.array([[float(pure_value(T, full_plan(T, a, 0), full_plan(T, b, 1))) for b in P1] for a in P0])
    assert N.matrix_game(M)[0] == pytest.approx(-1 / 24, abs=1e-12)


def test_normal_form_over_realization_plans_equals_the_direct_walk():
    for n in (2, 3):
        T, SF = kuhn_instance(n)
        M, P0, P1 = N.normal_matrix(T, SF)
        for a, pa in enumerate(P0):
            for b, pb in enumerate(P1):
                fa = tuple(pa.get(i, 0) for i in range(T.ninfo[0]))
                fb = tuple(pb.get(i, 0) for i in range(T.ninfo[1]))
                assert M[a, b] == pytest.approx(float(pure_value(T, fa, fb)), abs=1e-14)


def test_reduced_strategies_are_the_distinct_rows_and_columns_of_the_full_normal_form():
    """Die 27 und 64 reduzierten Strategien sind genau die verschiedenen Zeilen bzw. Spalten der vollen 64 × 64 Matrix (Kuhn, drei Karten)."""
    T, SF = kuhn_instance(3)
    full = full_normal_form(T)
    assert len({tuple(r) for r in full}) == 27 == N.reduced_count(T, SF, 0)
    assert len({tuple(col) for col in zip(*full)}) == 64 == N.reduced_count(T, SF, 1)
    assert len(full) == len(full[0]) == 64


# --- beste Antwort ---------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("n", [2, 3])
def test_best_response_equals_enumeration_of_all_pure_strategies(n):
    T, _ = kuhn_instance(n)
    rng = SplitMix64(1000 + n)
    for _ in range(12):
        st = random_profile(T, rng)
        for p in (0, 1):
            assert S.best_response(T, st, p)[0] == enumerate_best_response(T, st, p)


def test_best_response_equals_enumeration_in_anmeldung():
    T = TR.build(G.Anmeldung())
    rng = SplitMix64(77)
    for _ in range(12):
        st = random_profile(T, rng)
        for p in (0, 1):
            assert S.best_response(T, st, p)[0] == enumerate_best_response(T, st, p)


def test_gaps_are_never_negative_and_zero_exactly_at_the_value():
    T, SF = kuhn_instance(3)
    rng = SplitMix64(5)
    for _ in range(15):
        g0, g1, total = S.exploitability(T, random_profile(T, rng), F(-1, 18))
        assert g0 >= 0 and g1 >= 0 and total == g0 + g1


# --- Gleichgewichtsfamilie und Gleichgewichtsmenge ------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("alpha", [F(0), F(1, 12), F(1, 6), F(1, 4), F(1, 3)])
def test_family_has_gap_zero_for_both_players_in_fractions(alpha):
    T, _ = kuhn_instance(3)
    st = K.family_profile(T, alpha)
    assert S.exploitability(T, st, F(-1, 18)) == (0, 0, 0)
    assert S.profile_value(T, st) == F(-1, 18)


def test_family_deviations_cost_what_the_hand_calculation_says():
    """α = 1/6, jeweils eine Abweichung (Lücke der abweichenden Seite, exakt): zweiter Spieler bluft nie 1/9; Dame geht immer mit 1/9; Dame gibt immer auf 1/6; Dame geht mit 1/2 mit 1/36;
    erster Spieler setzt mit dem König 3/4 statt 1/2: 1/24."""
    T, _ = kuhn_instance(3)
    v = F(-1, 18)
    a = F(1, 6)
    cases = {
        "bluff0": (K.family_profile(T, a, bluff=F(0)), 0, F(1, 9)),
        "call1": (K.family_profile(T, a, call=F(1)), 0, F(1, 9)),
        "call0": (K.family_profile(T, a, call=F(0)), 0, F(1, 6)),
        "callhalf": (K.family_profile(T, a, call=F(1, 2)), 0, F(1, 36)),
        "king34": (K.family_profile(T, a, king=F(3, 4)), 1, F(1, 24)),
    }
    for name, (st, side, gap) in cases.items():
        g = S.exploitability(T, st, v)
        assert g[side] == gap, name
        assert g[1 - side] == 0, name


def test_family_membership_function():
    assert K.in_family(F(1, 6), F(1, 2), F(1, 3), F(1, 3), F(1, 2))
    assert not K.in_family(F(1, 2), F(1, 2), F(1, 3), F(1, 3), F(1, 2))    # α > 1/3
    assert not K.in_family(F(1, 6), F(1, 2), F(1, 4), F(1, 3), F(1, 2))    # anderer Bluff


def test_equilibrium_set_is_exactly_the_family():
    """Exakte Bereichsrechnung: zweiter Spieler eindeutig; erster Spieler mit Bube setzen in [0, 1/3]; mit König setzen genau 3× Bube; Dame geht nach Pass–Setzen um 1/3 häufiger mit
    als der Bube setzt. Beides als Linearkombination auf der Menge: Größe (König − 3·Bube) liegt in [0, 0], (Dame − Bube) in [1/3, 1/3]."""
    T, SF = kuhn_instance(3)
    v = F(-1, 18)
    jb = K.seq_index(T, SF, 0, 0, "", 1)
    kb = K.seq_index(T, SF, 0, 2, "", 1)
    qc = K.seq_index(T, SF, 0, 1, "pb", 1)
    assert X.exact_range(SF, 0, v, jb) == (0, F(1, 3))
    assert X.exact_linear_range(SF, 0, v, {kb: 1, jb: -3}) == (0, 0)
    assert X.exact_linear_range(SF, 0, v, {qc: 1, jb: -1}) == (F(1, 3), F(1, 3))
    bluff = K.seq_index(T, SF, 1, 0, "p", 1)
    call = K.seq_index(T, SF, 1, 1, "b", 1)
    assert X.exact_range(SF, 1, -v, bluff) == (F(1, 3), F(1, 3)) and X.exact_range(SF, 1, -v, call) == (F(1, 3), F(1, 3))


def test_a_strategy_outside_the_range_has_a_positive_gap():
    T, _ = kuhn_instance(3)
    st = K.family_profile(T, F(2, 5), king=F(1), queen_call=F(2, 5) + F(1, 3))   # α = 2/5 > 1/3: König kann nicht mehr 3α setzen
    assert S.exploitability(T, st, F(-1, 18))[1] > 0


# --- Verbote und Faustregeln ------------------------------------------------------------------------------------------------------------------------
def restricted_game_value(T, SF, case, P0, P1, M):
    """Garantierter Wert bei verbotenen Handlungen aus der Normalform (Gleitkomma, HiGHS): Matrixspiel über die reduzierten Strategien, die die verbotene Handlung nie wählen
    (andere Rechenroute als die Sequenzform)."""
    p = case[1]
    banned = [(K.info_index(T, p, c, h), a) for c, h, a in case[3]]
    plans = P0 if p == 0 else P1
    keep = [k for k, pl in enumerate(plans) if all(pl.get(i) != a for i, a in banned)]
    if p == 0:
        return N.matrix_game(np.array([[float(v) for v in M[k]] for k in keep]))[0]
    return N.matrix_game(np.array([[-float(M[i][k]) for i in range(len(P0))] for k in keep]))[0]


def test_ban_costs_equal_the_restricted_normal_form_game_and_the_hand_values():
    T, SF = kuhn_instance(3)
    v = F(-1, 18)
    expected = {"s1_no_bluff": F(1, 9), "s1_q_never_call": F(1, 6), "s1_q_always_call": F(1, 9), "s1_k_no_bet": F(1, 9), "s1_k_no_fold": F(0), "s1_no_bluff_q_never": F(2, 9),
                "s0_no_bluff": F(0), "s0_k_never_bet": F(0), "s0_k_never_pass": F(0), "s0_q_never_call": F(1, 36), "s0_q_always_call": F(1, 18), "s0_only_k_bets": F(0), "s0_never_bet": F(0)}
    assert {c[0] for c in K.BAN_CASES} == set(expected)
    P0, P1 = N.reduced_plans(T, SF, 0), N.reduced_plans(T, SF, 1)
    M = N.normal_matrix_exact(SF, P0, P1)
    for case in K.BAN_CASES:
        guaranteed, cost = K.ban_cost(T, SF, case, v)
        assert cost == expected[case[0]], case[0]
        assert float(guaranteed) == pytest.approx(restricted_game_value(T, SF, case, P0, P1, M), abs=1e-12), case[0]


def test_value_of_randomising_pure_strategies_only():
    """Ohne Mischen garantiert jede Seite höchstens −1/6; der Verzicht auf Zufall kostet den ersten Spieler 1/9, den zweiten 2/9."""
    T, SF = kuhn_instance(3)
    M = N.normal_matrix_exact(SF, N.reduced_plans(T, SF, 0), N.reduced_plans(T, SF, 1))
    assert K.best_pure_guarantee(M, 0) == F(-1, 6) and K.best_pure_guarantee(M, 1) == F(-1, 6)
    assert F(-1, 18) - K.best_pure_guarantee(M, 0) == F(1, 9) and F(1, 18) - K.best_pure_guarantee(M, 1) == F(2, 9)


def test_rules_of_thumb_cost_by_enumeration():
    T, _ = kuhn_instance(3)
    v = F(-1, 18)
    expected = {"immer setzen und mitgehen": (F(5, 18), F(7, 18)), "immer passen und aufgeben": (F(17, 18), F(19, 18)),
                "nur mit dem König setzen und mitgehen": (F(5, 18), F(2, 9)), "mit Dame und König setzen und mitgehen": (F(1, 9), F(2, 9))}
    for rule in K.RULES_OF_THUMB:
        assert K.rule_cost(T, rule, v) == expected[rule[0]], rule[0]
        st = K.profile(T, *rule[1:])
        assert S.best_response(T, st, 1)[0] == enumerate_best_response(T, st, 1)


# --- Anmeldung und Kontrolle -----------------------------------------------------------------------------------------------------------------------
P_GRID = [F(1, 50), F(1, 20), F(1, 10), F(3, 10), F(1, 2), F(9, 10)]
S_GRID = [5, 10, 20, 40, 80]


def test_anmeldung_closed_form_equals_lp_normal_form_and_has_zero_gaps_on_the_grid():
    modes = {"gemischt": 0, "alle lügen": 0}
    for p in P_GRID:
        for s in S_GRID:
            game = G.Anmeldung(s=s, p=p)
            T = TR.build(game)
            SF = SQ.SeqForm(T)
            lam, kap, value, regime = AN.closed_form(game.par)
            modes[regime] += 1
            M = N.normal_matrix_exact(SF, N.reduced_plans(T, SF, 0), N.reduced_plans(T, SF, 1))
            assert X.exact_seq_lp(SF, 0)[0] == value == X.matrix_game_exact(M)[0], (p, s)
            st = AN.equilibrium_profile(T, lam, kap)
            assert S.profile_value(T, st) == value
            assert S.exploitability(T, st, value) == (0, 0, 0), (p, s)
    assert modes == {"gemischt": 22, "alle lügen": 8}


@pytest.mark.parametrize("c,g,r", [(2, 15, 6), (2, 6, 6), (2, 5, 6), (5, 15, 6), (0, 15, 6), (2, 15, 14), (2, 15, 15)])
def test_anmeldung_closed_form_in_the_extra_rows(c, g, r):
    game = G.Anmeldung(c=c, g=g, r=r)
    T = TR.build(game)
    SF = SQ.SeqForm(T)
    lam, kap, value, regime = AN.closed_form(game.par)
    assert X.exact_seq_lp(SF, 0)[0] == value
    assert S.exploitability(T, AN.equilibrium_profile(T, lam, kap), value) == (0, 0, 0)


def test_anmeldung_value_does_not_depend_on_the_report_fee():
    values = {G.Anmeldung(f=f) and X.exact_seq_lp(SQ.SeqForm(TR.build(G.Anmeldung(f=f))), 0)[0] for f in (0, 1, 3, 5)}
    assert values == {F(229, 25)}


# --- Leduc ------------------------------------------------------------------------------------------------------------------------------------------
def test_leduc_lp_strategies_have_gap_zero_by_best_response():
    T, SF = leduc_instance()
    v0, x0 = SQ.solve_lp(SF, 0)
    v1, x1 = SQ.solve_lp(SF, 1)
    st = [SQ.realization_to_behavior(SF, x0, 0), SQ.realization_to_behavior(SF, x1, 1)]
    g0, g1, total = S.exploitability(T, st, v0)
    assert v0 + v1 == pytest.approx(0, abs=1e-12)
    assert abs(g0) < 1e-10 and abs(g1) < 1e-10 and abs(total) < 1e-10
    assert S.profile_value(T, st) == pytest.approx(v0, abs=1e-10)
    assert v0 == pytest.approx(-0.0856064240780005, abs=1e-12)
