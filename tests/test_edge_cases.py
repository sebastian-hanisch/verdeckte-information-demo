"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 2, Gleichstände, Schwellen inklusive, Ecken der Anmeldungs-Regler, Wert 0."""

import itertools
from fractions import Fraction as F

import numpy as np
import pytest

import vdi_anmeldung as AN
import vdi_cfr as CF
import vdi_constants as C
import vdi_exact as X
import vdi_games as G
import vdi_normal as N
import vdi_scenario as SC
import vdi_seqform as SQ
import vdi_strategy as S
import vdi_tree as TR
from conftest import kuhn_instance
from vdi_rng import SplitMix64


def test_exactly_two_cards_has_value_zero_and_trivial_information_sets(kuhn2):
    """n = 2: der kleinste Fall; die eigene Karte verrät die des anderen, jede Informationsmenge hat einen Knoten, der Spielwert ist genau 0 (kein Vorzeichenfehler bei −0,0)."""
    T, SF = kuhn2["T"], kuhn2["SF"]
    v = X.exact_seq_lp(SF, 0)[0]
    assert v == 0 and isinstance(v, F)
    assert SQ.solve_lp(SF, 1)[0] == pytest.approx(0, abs=1e-12)
    assert all(len(nodes) == 1 for p in (0, 1) for nodes in T.inodes[p])


def test_cfr_on_two_cards_has_gap_near_zero_even_with_value_zero():
    T, SF = kuhn_instance(2)
    solver = CF.CFRSolver(T, "cfrplus")
    for _ in range(200):
        solver.step()
    assert S.max_gap(T, solver.average(), 0.0) < 1e-3


def test_a_game_without_cards_is_refused():
    with pytest.raises(Exception):
        TR.build(G.Kuhn(1))      # keine Austeilung möglich: der Zufallsknoten hat keinen Ausgang


def test_best_response_ties_take_the_first_action():
    """Der erste Spieler passt immer und gibt immer auf (Kuhn, zwei Karten). Zweiter Spieler mit dem König nach Pass: Passen gewinnt 1 (Vergleich), Setzen gewinnt 1 (der Gegner gibt auf):
    Gleichstand, die erste Aktion (Passen) gilt. Mit dem Buben lohnt der Bluff: Setzen +1 gegen Passen −1. Wert der besten Antwort: (1 + 1)/2 = 1."""
    T, _ = kuhn_instance(2)
    st = S.uniform_strategy(T)
    for i in range(T.ninfo[0]):
        st[0][i] = [F(1), F(0)]
    value, choice = S.best_response(T, st, 1)
    assert choice[T.ikeys[1][(1, 1, "p")]] == 0 and choice[T.ikeys[1][(1, 0, "p")]] == 1
    assert value == 1


def test_threshold_is_inclusive_in_anmeldung():
    """p = μ* gehört zu „alle lügen“ (p ≤ μ*): λ = 1; dort stimmt die gemischte Form von beiden Seiten überein (stetiger Übergang), und das LP bestätigt den Wert."""
    par = G.Anmeldung(p=F(2, 37)).par
    lam, kap, value, regime = AN.closed_form(par)
    assert regime == "alle lügen" and lam == 1 and kap == 0
    mixed = (1 - par["p"]) * (par["b"] + par["c"] * (par["g"] - par["r"]) / (par["g"] + par["s"])) + par["p"] * par["r"]
    assert value == mixed
    T = TR.build(G.Anmeldung(p=F(2, 37)))
    assert X.exact_seq_lp(SQ.SeqForm(T), 0)[0] == value
    assert AN.closed_form(G.Anmeldung(p=F(2, 37) + F(1, 1000)).par)[3] == "gemischt"


def test_honesty_boundary_g_equals_r_is_honest():
    assert AN.closed_form(G.Anmeldung(g=6, r=6).par)[3] == "ehrlich" and AN.closed_form(G.Anmeldung(g=7, r=6).par)[3] != "ehrlich"


def test_anmeldung_corners_of_the_sliders_agree_with_the_lp():
    """Alle 64 Ecken der sechs Anmeldungs-Regler (Minimum/Maximum): geschlossene Form = exaktes LP, Lücken 0."""
    bounds = [(C.A_B_MIN, C.A_B_MAX), (C.A_C_MIN, C.A_C_MAX), (C.A_G_MIN, C.A_G_MAX), (C.A_S_MIN, C.A_S_MAX), (C.A_R_MIN, C.A_R_MAX), (C.A_P_MIN, C.A_P_MAX)]
    regimes = set()
    for b, c, g, s, r, p in itertools.product(*bounds):
        game = SC.anmeldung_game(SC.Settings(b=b, c=c, g=g, s=s, r=r, p=p))
        T = TR.build(game)
        lam, kap, value, regime = AN.closed_form(game.par)
        regimes.add(regime)
        assert 0 <= lam <= 1 and 0 <= kap <= 1
        assert X.exact_seq_lp(SQ.SeqForm(T), 0)[0] == value, (b, c, g, s, r, p)
        assert S.exploitability(T, AN.equilibrium_profile(T, lam, kap), value) == (0, 0, 0), (b, c, g, s, r, p)
    assert regimes == {"ehrlich", "alle lügen", "gemischt"}


def test_reduced_count_for_n_equals_two_and_formula_for_all_n():
    for n in range(2, C.N_MAX + 1):
        T, SF = kuhn_instance(n)
        assert (N.reduced_count(T, SF, 0), N.reduced_count(T, SF, 1)) == (3 ** n, 4 ** n)
        assert SF.n == [4 * n + 1] * 2 == [SQ.sequence_count_kuhn(n)] * 2
        assert T.n == 1 + n * (n - 1) * 9


def test_regret_matching_with_one_positive_regret_and_with_none():
    assert CF.regret_matching_probs([0.0, 1e-300]) == [0.0, 1.0] and CF.regret_matching_probs([-0.0, -0.0]) == [0.5, 0.5]


def test_checkpoints_include_the_endpoint_and_stay_sorted():
    import vdi_runs as R
    for t in (1, 10, 99, 100, 300, 1000, 3000, 300000):
        pts = R.checkpoints(t)
        assert pts == sorted(set(pts)) and pts[-1] == t and pts[0] >= 1
    assert 30000 in R.checkpoints(300000) and 3000 in R.checkpoints(3000)


def test_unit_streams_do_not_collide_for_neighbouring_cells():
    import vdi_runs as R
    a, b = R.stream(11, 3), R.stream(11, 4)
    assert [a.next() for _ in range(3)] != [b.next() for _ in range(3)]
    assert R.stream(11, 3).next() == SplitMix64(11 * 1_000_003 + 3).next()


def test_numpy_scalars_in_the_json_payload_are_converted():
    import json

    import vdi_experiments as XP
    assert json.loads(json.dumps({"a": np.float64(1.5), "b": np.int64(3), "c": F(1, 3)}, default=XP._json_default)) == {"a": 1.5, "b": 3, "c": "1/3"}
