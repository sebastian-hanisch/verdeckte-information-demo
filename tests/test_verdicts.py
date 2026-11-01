"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds."""

from fractions import Fraction as F

import pytest

import vdi_evaluation as V
from vdi_scenario import Settings


def _view(first, second, in_family=False, alpha=F(1, 6), value=F(-1, 18)):
    return V.StrategyView(alpha=alpha, value=value, loss_first=F(first), loss_second=F(second), in_family=in_family, rows=())


def test_formats():
    assert V.de(-0.0556, 4) == "−0,0556" and V.de(1234.5, 1) == "1.234,5" and V.de(-0.0000001, 2) == "0,00"
    assert V.frac(F(-1, 18)) == "−1/18" and V.frac(F(2)) == "2" and V.frac_dec(F(1, 9)) == "1/9 (0,1111)" and V.frac_dec(F(3)) == "3"
    assert V.sci(0.00786) == "7,9·10⁻³" and V.sci(0) == "0" and V.sci(0.0000099999) == "1,0·10⁻⁵" and V.sci(1.54) == "1,5·10⁰" and V.sci(123456) == "1,2·10⁵"


def test_verdict_main_success_in_family_names_alpha_and_value():
    kind, text = V.verdict_main(_view(0, 0, in_family=True))
    assert kind == "success" and "Lücke 0 auf beiden Seiten" in text and "−1/18 (−0,0556)" in text and "α = 1/6" in text


def test_verdict_main_names_each_side_with_its_gap():
    kind, text = V.verdict_main(_view(0, F(1, 9)))
    assert kind == "warning" and "Kein Gleichgewicht" in text and "zweite Spieler gibt gegen die beste Antwort des ersten 1/9 (0,1111)" in text and "erste Spieler gibt" not in text
    kind, text = V.verdict_main(_view(F(1, 24), 0))
    assert kind == "warning" and "erste Spieler gibt gegen die beste Antwort des zweiten 1/24 (0,0417)" in text and "zweite Spieler gibt" not in text
    kind, text = V.verdict_main(_view(F(1, 24), F(1, 9)))
    assert "erste Spieler" in text and "zweite Spieler" in text


def test_verdict_curves_counts_zero_points():
    xs = list(range(13))
    curves = {"Zweiter Spieler: a": (xs, [F(1) if k != 4 else F(0) for k in xs], 2), "Zweiter Spieler: b": (xs, [F(1) if k != 4 else F(0) for k in xs], 2),
              "Erster Spieler: c": (xs, [F(1) if k != 6 else F(0) for k in xs], 1), "Erster Spieler: d": (xs, [F(1) if k != 6 else F(0) for k in xs], 1),
              "Erster Spieler: Bube setzt (Familie)": (xs, [F(0) if k <= 4 else F(1) for k in xs], 1)}
    kind, text = V.verdict_curves(curves)
    assert kind == "info" and "an 1, 1, 1, 1 von je 13 Rasterpunkten 0" in text and "an 5 von 13 Rasterpunkten 0" in text


def _size(n, exact, normal, floatv=-1 / 18):
    return V.SizeView(n=n, nodes=55, sequences=13, reduced=(27, 64), entries=1728, value_float=floatv, value_exact=exact, value_normal=normal, t_seq=0.01, t_exact=0.1, t_normal=0.02)


def test_verdict_size_three_ways_agree():
    kind, text = V.verdict_size(_size(3, F(-1, 18), -1 / 18))
    assert kind == "success" and "27 × 64 = 1.728 Einträge" in text and "13 Sequenzen" in text and "−1/18" in text and text.endswith("gleich.")


def test_verdict_size_flags_a_deviation_and_the_two_reduced_cases():
    assert V.verdict_size(_size(3, F(-1, 18), -0.07))[0] == "error"
    assert V.verdict_size(_size(3, F(-1, 18), -1 / 18, floatv=-0.07))[0] == "error"
    kind, text = V.verdict_size(V.SizeView(5, 181, 21, (243, 1024), 248832, -1 / 15, F(-1, 15), None, 0.01, 1.0, None))
    assert kind == "info" and "−1/15" in text and "nicht aufgestellt" in text
    kind, text = V.verdict_size(V.SizeView(13, 1405, 53, (1594323, 67108864), 106993205379072, -0.0641, None, None, 0.01, None, None))
    assert kind == "info" and "−0,0641" in text and "53 Sequenzen" in text and "1.594.323 × 67.108.864" in text


def _run(avg, last=None):
    r = {"t": [1000, 10000, 300000], "avg": avg, "avg_sum": avg, "nodes": [10, 100, 3000]}
    if last is not None:
        r["last"] = last
    return r


def test_verdict_runs_live_names_best_and_worst():
    runs = {"cfr": _run([8e-3, 3e-3, 7e-4], [0.28, 0.22, 0.39]), "cfrplus": _run([1e-4, 1e-5, 1e-6], [3e-2, 1e-2, 3e-3]), "rm_nf": _run([6e-3, 2e-3, 1e-3])}
    kind, text = V.verdict_runs_live({"runs": runs}, 300000)
    assert kind == "info" and "T = 300000" in text
    assert "CFR⁺ die kleinste Lücke des Mittels (1,0·10⁻⁶)" in text and "Regret Matching (Normalform) die größte (1,0·10⁻³)" in text
    assert "Lücke der letzten Iteration 3,9·10⁻¹, die des Mittels 7,0·10⁻⁴" in text and "bei CFR⁺ 3,0·10⁻³ bzw. 1,0·10⁻⁶" in text


def _tables_for_chain():
    def r(avg, last):
        return {"t": [1000, 10000, 30000, 300000], "avg": avg, "last": last, "nodes": [1, 2, 3, 4]}
    return {"kuhn": {
        "cfr": r([1e-2, 1e-3, 5e-4, 1e-4], [0.3, 0.2, 0.3, 0.4]),
        "cfr_alt": r([1e-3, 1e-5, 4e-6, 1e-6], [0.06, 0.03, 0.02, 0.02]),
        "cfr_clip": r([5e-4, 5e-6, 2e-6, 5e-7], [0.03, 0.01, 0.01, 0.003]),
        "cfrplus": r([1e-4, 1e-6, 5e-7, 1e-7], [0.03, 0.01, 0.01, 0.003]),
        "dcfr": r([2e-4, 2e-6, 4e-7, 2e-8], [0.02, 0.01, 0.007, 0.004]),
    }}


def test_decomposition_factors_and_slopes():
    d = V.decomposition(_tables_for_chain())
    assert d["cfr"]["factor"] is None
    assert d["cfr_alt"]["factor"] == 10 and d["cfr_clip"]["factor"] == 2 and d["cfrplus"]["factor"] == 5      # 1e-2/1e-3, 1e-3/5e-4, 5e-4/1e-4
    ts = [1000, 10000, 30000, 300000]
    law = {"t": ts, "last": [1.0] * 4, "nodes": [1, 2, 3, 4]}
    power = {"kuhn": {"cfr": {**law, "avg": [t ** -0.5 for t in ts]}, "cfr_alt": {**law, "avg": [t ** -1.0 for t in ts]}, "cfr_clip": {**law, "avg": [t ** -0.9 for t in ts]},
                      "cfrplus": {**law, "avg": [2 * t ** -0.8 for t in ts]}}}
    slopes = [V.decomposition(power)[k]["slope"] for k in ("cfr", "cfr_alt", "cfr_clip", "cfrplus")]
    assert slopes == [pytest.approx(x) for x in (-0.5, -1.0, -0.9, -0.8)]                                    # Potenzgesetze: die Steigung im Doppellogarithmus ist der Exponent
    kind, text = V.verdict_decomposition(_tables_for_chain())
    assert kind == "info" and "Faktoren 2,0 und 5,0 bei T = 1 000" in text and "von " in text


def test_verdict_last_uses_checkpoints_from_t_1000():
    t = _tables_for_chain()
    kind, text = V.verdict_last(t)
    assert kind == "warning" and "zwischen 2,0·10⁻¹ und 4,0·10⁻¹" in text and "CFR⁺ ist sie 3,0·10⁻³" in text and "Discounted CFR 4,0·10⁻³" in text


def test_dcfr_vs_cfrplus_counts_checkpoints_from_t_100():
    t = {"kuhn": {"cfrplus": {"t": [10, 100, 1000, 10000, 300000], "avg": [1, 1e-3, 1e-4, 1e-5, 1e-6]},
                  "dcfr": {"t": [10, 100, 1000, 10000, 300000], "avg": [1, 2e-3, 2e-4, 5e-6, 5e-7]}}}
    assert V.dcfr_vs_cfrplus(t) == {"points": 4, "dcfr_better": 2, "stable_from": 10000}
    t["kuhn"]["dcfr"]["avg"][-1] = 5e-6
    assert V.dcfr_vs_cfrplus(t)["stable_from"] is None


def test_at_nodes_picks_the_last_checkpoint_within_the_budget():
    run = {"t": [10, 100, 1000], "avg": [0.5, 0.1, 0.01], "nodes": [100, 1000, 10000]}
    assert V.at_nodes(run, 1000) == (100, 0.1) and V.at_nodes(run, 99) is None and V.at_nodes(run, 10 ** 9) == (1000, 0.01)


def _cell(regime, same=True, lam="2/15", kap="9/35", value="229/25"):
    return {"regime": regime, "same": same, "lam": lam, "kap": kap, "value": value}


def test_verdict_anmeldung_each_regime_names_its_numbers():
    s = Settings()
    kind, text = V.verdict_anmeldung(_cell("gemischt"), s)
    assert kind == "info" and "13,3 % der riskanten Sendungen melden" in text and "25,7 %" in text and "9,16 Euro je Sendung" in text
    kind, text = V.verdict_anmeldung(_cell("alle lügen", lam="1", kap="0", value="101/10"), Settings(p=5))
    assert "μ* = 2/37 (5,4 %)" in text and "10,10 Euro" in text and "λ = 1" in text
    kind, text = V.verdict_anmeldung(_cell("ehrlich", lam="0", kap="0", value="9"), Settings(g=5))
    assert "g = 5" in text and "r = 6" in text and "niemand lügt" in text
    assert V.verdict_anmeldung(_cell("gemischt", same=False), s)[0] == "error"


def test_verdict_anmeldung_table_counts_cells():
    def c(regime, same=True, kap="9/35"):
        return {"regime": regime, "same": same, "kap": kap}
    tables = {"anmeldung": {"grid": [c("gemischt")] * 22 + [c("alle lügen")] * 7 + [c("alle lügen", same=False)], "extra": [c("gemischt")] * 7,
                            "p_rows": [c("gemischt")] * 5}}
    kind, text = V.verdict_anmeldung_table(tables)
    assert "30 Zellen" in text and "in 29 Zellen überein" in text and "22 Zellen sind gemischt, 8 „alle lügen“" in text and "7 Zusatzzeilen" in text and "stimmen 7 überein" in text and "immer 9/35" in text
