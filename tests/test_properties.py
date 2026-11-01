"""Eigenschaftstests und Zweigtests (Nullspalten-Regel): Skalierung, Umbenennen, Nebenbedingungen, Prozessunabhängigkeit; jedes Verfahren weicht von den anderen ab, jeder Zweig läuft."""

import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

import vdi_anmeldung as AN
import vdi_cfr as CF
import vdi_exact as X
import vdi_games as G
import vdi_kuhn as K
import vdi_runs as R
import vdi_seqform as SQ
import vdi_strategy as S
import vdi_tree as TR
from conftest import kuhn_instance
from vdi_rng import SplitMix64
from test_oracle_verdeckte_information import random_profile

ROOT = Path(__file__).resolve().parent.parent


# --- Eigenschaften ---------------------------------------------------------------------------------------------------------------------------------
class ScaledKuhn(G.Kuhn):
    """Alle Auszahlungen mit k > 0 multipliziert."""
    def __init__(self, n, k):
        super().__init__(n)
        self.k = F(k)

    def payoff0(self, s):
        return self.k * super().payoff0(s)


class RelabeledKuhn(G.Kuhn):
    """Karten tragen andere Namen (Rangzahlen 10, 20, 30, ...), verglichen wird nach dem Rang: ein reines Umbenennen."""
    def payoff0(self, s):
        (c0, c1), h = s
        return super().payoff0(((10 * (c0 + 1), 10 * (c1 + 1)), h))


class ReversedKuhn(G.Kuhn):
    """Die Rangfolge der Karten ist umgekehrt (niedrigste gewinnt): spiegelbildliches Spiel mit demselben Wert."""
    def payoff0(self, s):
        (c0, c1), h = s
        return super().payoff0(((-c0, -c1), h))


def test_scaling_all_payoffs_scales_value_and_gaps():
    base_T, base_SF = kuhn_instance(3)
    for k in (F(2), F(1, 3), F(7)):
        T = TR.build(ScaledKuhn(3, k))
        SF = SQ.SeqForm(T)
        assert X.exact_seq_lp(SF, 0)[0] == k * F(-1, 18)
        st = K.family_profile(T, F(1, 6), bluff=F(0))
        base = S.exploitability(base_T, K.family_profile(base_T, F(1, 6), bluff=F(0)), F(-1, 18))
        scaled = S.exploitability(T, st, k * F(-1, 18))
        assert scaled == tuple(k * x for x in base)


def test_renaming_the_cards_changes_nothing_and_reversing_the_order_keeps_the_value():
    for cls in (RelabeledKuhn, ReversedKuhn):
        T = TR.build(cls(3))
        assert X.exact_seq_lp(SQ.SeqForm(T), 0)[0] == F(-1, 18), cls.__name__


def test_scaling_anmeldung_money_scales_value_and_keeps_the_strategy():
    base = G.Anmeldung().par
    for k in (2, 5):
        par = G.Anmeldung(b=10 * k, c=2 * k, f=1 * k, g=15 * k, s=20 * k, r=6 * k).par
        lam, kap, value, regime = AN.closed_form(par)
        lam0, kap0, value0, regime0 = AN.closed_form(base)
        assert (lam, kap, regime) == (lam0, kap0, regime0) and value == k * value0


def test_realization_plans_satisfy_the_constraints_and_behavior_is_a_distribution():
    import numpy as np
    T, SF = kuhn_instance(3)
    rng = SplitMix64(9)
    for _ in range(10):
        st = random_profile(T, rng)
        for p, M in ((0, SF.E), (1, SF.F)):
            x = SQ.behavior_to_realization(SF, st[p], p)
            e = np.zeros(M.shape[0])
            e[0] = 1
            assert all(a == b for a, b in zip(M @ np.array(x, dtype=object), e))
            assert all(v >= 0 for v in x)
    for p in (0, 1):
        value, x = SQ.solve_lp(SF, p)
        for row in SQ.realization_to_behavior(SF, x, p):
            assert all(-1e-12 <= v <= 1 + 1e-12 for v in row) and sum(row) == pytest.approx(1)


def test_values_of_both_sides_sum_to_zero_for_two_to_four_cards():
    for n in range(2, 5):
        T, SF = kuhn_instance(n)
        assert X.exact_seq_lp(SF, 0)[0] + X.exact_seq_lp(SF, 1)[0] == 0


def test_in_family_is_the_same_as_gap_zero_on_random_and_structured_choices():
    """Auf 300 zufälligen und allen 5 × 5 × 4 strukturierten Wahlen der fünf Regler (Zwölftel): Lücke 0 auf beiden Seiten genau dann, wenn die Wahl in der Familie liegt."""
    T, _ = kuhn_instance(3)
    rng = SplitMix64(31)
    picks = [tuple(int(rng.uniform() * 13) for _ in range(5)) for _ in range(300)]
    picks += [(j, k, q, b, c) for j in (0, 2, 4, 6, 12) for k in (0, 6, 12) for q in (4, 6, 8, 12) for b in (4, 5) for c in (4,)]
    picks += [(j, 3 * j, j + 4, 4, 4) for j in range(0, 5)]
    hits = 0
    for j, k, q, b, c in picks:
        st = K.family_profile(T, F(j, 12), king=F(k, 12), queen_call=F(q, 12), bluff=F(b, 12), call=F(c, 12))
        g = S.exploitability(T, st, F(-1, 18))
        fam = K.in_family(F(j, 12), F(k, 12), F(b, 12), F(c, 12), F(q, 12))
        assert (g[0] == 0 and g[1] == 0) == fam, (j, k, q, b, c)
        hits += fam
    assert hits >= 5            # die Stichprobe enthält Mitglieder der Familie


def test_results_do_not_depend_on_the_hash_seed_of_the_process():
    code = ("import sys; sys.path.insert(0, %r)\n"
            "from fractions import Fraction as F\n"
            "import vdi_games as G, vdi_tree as TR, vdi_seqform as SQ, vdi_exact as X, vdi_cfr as CF, vdi_strategy as S, vdi_kuhn as K\n"
            "T = TR.build(G.Kuhn(3)); SF = SQ.SeqForm(T)\n"
            "s = CF.CFRSolver(T, 'cfrplus')\n"
            "[s.step() for _ in range(200)]\n"
            "print(X.exact_seq_lp(SF, 0)[0], SF.seq[0][:5], repr(S.max_gap(T, s.average(), -1/18)), [c[0] for c in K.BAN_CASES][:3])\n") % str(ROOT)
    outs = []
    for seed in ("1", "2"):
        res = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code], env={"PYTHONHASHSEED": seed, "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")},
                             capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
        assert res.returncode == 0, res.stderr
        outs.append(res.stdout)
    assert outs[0] == outs[1] and "-1/18" in outs[0]


# --- Zweigtests -------------------------------------------------------------------------------------------------------------------------------------
def test_every_variant_differs_from_every_other_at_t_1000():
    T, _ = kuhn_instance(3)
    gaps = {v: R.run_variant(T, v, 1000, -1 / 18, marks=[1000])["avg"][0] for v in CF.VARIANTS}
    values = sorted(gaps.values())
    assert len(set(values)) == len(CF.VARIANTS)
    assert all(b / a > 1.05 for a, b in zip(values, values[1:])), gaps         # kein Paar liegt dicht beieinander (Faktor mindestens 1,05)


def test_clip_and_cfrplus_have_the_same_last_iteration_but_different_averages():
    """Die lineare Mittelung ändert nur die Durchschnittsstrategie, nicht den Verlauf der Regrets: letzte Iteration gleich, Mittel verschieden."""
    T, _ = kuhn_instance(3)
    a = R.run_variant(T, "cfr_clip", 300, -1 / 18, marks=[300])
    b = R.run_variant(T, "cfrplus", 300, -1 / 18, marks=[300])
    assert a["last"] == b["last"] and a["avg"] != b["avg"]


def test_random_start_differs_from_uniform_start_and_from_other_seeds():
    T, _ = kuhn_instance(3)
    uniform = R.run_variant(T, "cfrplus", 300, -1 / 18, marks=[300])["avg"][0]
    starts = [R.run_variant(T, "cfrplus", 300, -1 / 18, marks=[300], init_regrets=CF.random_regrets(T, R.stream(seed, 7)))["avg"][0] for seed in (11, 22)]
    assert len({uniform, *starts}) == 3


def test_sampling_differs_between_seeds_and_repeats_for_the_same_seed():
    T, _ = kuhn_instance(3)
    runs = [R.run_sampling(T, R.stream(seed, 3), 500, -1 / 18, [500])["avg"][0] for seed in (11, 22, 11)]
    assert runs[0] != runs[1] and runs[0] == runs[2]


def test_the_alternating_update_is_a_real_difference_in_the_first_step():
    """Im ersten Schritt sieht der zweite Spieler beim abwechselnden Verfahren schon die Regrets des ersten; die Regrets des zweiten Spielers unterscheiden sich vom gleichzeitigen Verfahren."""
    T, _ = kuhn_instance(3)
    sim, alt = CF.CFRSolver(T, "cfr"), CF.CFRSolver(T, "cfr_alt")
    sim.step()
    alt.step()
    assert sim.reg[0] == alt.reg[0] and sim.reg[1] != alt.reg[1]


def test_bans_with_cost_and_without_cost_both_occur():
    T, SF = kuhn_instance(3)
    costs = [K.ban_cost(T, SF, case, F(-1, 18))[1] for case in K.BAN_CASES]
    assert any(c > 0 for c in costs) and any(c == 0 for c in costs)


def test_all_three_anmeldung_regimes_run():
    seen = {AN.closed_form(G.Anmeldung(p=p, g=g).par)[3] for p in (F(1, 50), F(3, 10)) for g in (5, 15)}
    assert seen == {"ehrlich", "alle lügen", "gemischt"}
