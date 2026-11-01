"""Jede Zahl aus der README, nachgerechnet (DEMO-PLAYBOOK §4).

Drei Quellen, alle plattformsicher:
* die gespeicherten Messreihen (`data/tables.json`; Erzeuger-Hash geprüft in `test_measurements.py`, Proben dort neu gerechnet): die README-Zahl ist der gespeicherte Wert, gerundet;
* exakte Rechnung (Brüche, Formeln, Zählungen am Baum): Gleitkommagleichheit nur mit `approx`;
* die Zeilenbauer der App (`vdi_evaluation.rows_*`): jede Zeile der README-Tabellen steht als Text in der README.
Formatierung unabhängig von `vdi_evaluation` (eigene Fassung von Dezimalkomma und Zehnerpotenz). Keine Zeit-Assertion, keine exakten Zufallswerte einzelner Läufe."""

import math
import re
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest

import vdi_evaluation as V
import vdi_experiments as XP
import vdi_scenario as SC
import vdi_texts as T
from conftest import kuhn_instance

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻"}


def german(x, nd):
    """Eigene Fassung des deutschen Zahlenformats (unabhängig von V.de): Dezimalkomma, Tausenderpunkt, echtes Minus."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "T").replace(".", ",").replace("T", ".").replace("-", "−")


def sci(x, nd=1):
    """7,9·10⁻³ (unabhängige Fassung)."""
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    m = round(x / 10 ** e, nd)
    if m >= 10:
        m, e = m / 10, e + 1
    return f"{m:.{nd}f}".replace(".", ",") + "·10" + "".join(SUP[c] for c in str(e))


def frac(x):
    return str(F(x)).replace("-", "−")


def row_of(label):
    """Die Tabellenzeile der Hypothese (eine Zeile der README, beginnt mit `| Hn |`)."""
    return next(line for line in README.splitlines() if line.startswith(f"| {label} |"))


def has(row, *needles):
    missing = [n for n in needles if n not in row]
    assert not missing, missing


def md_row(d):
    return "| " + " | ".join(str(v) for v in d.values()) + " |"


def slope(run, lo, hi):
    pts = [(t, v) for t, v in zip(run["t"], run["avg"]) if lo <= t <= hi]
    return float(np.polyfit(np.log([p[0] for p in pts]), np.log([p[1] for p in pts]), 1)[0])


def at(run, t, key="avg"):
    return run[key][run["t"].index(t)]


def mean_sd(values):
    m = sum(values) / len(values)
    return m, math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


@pytest.fixture(scope="module")
def tables():
    t = XP.load_tables()
    assert t is not None
    return t


# --- README und App: dieselben Texte, dieselben Tabellenzeilen ---------------------------------------------------------------------------------
def test_assumption_text_is_the_same_in_app_and_readme():
    assert T.ASSUMPTIONS_MARKDOWN.strip() in README


def test_readme_tables_are_built_by_the_same_row_builders(tables):
    builders = (V.rows_family, V.rows_bans, V.rows_rules, V.rows_size, V.rows_kuhn_runs, V.rows_decomposition, V.rows_last, V.rows_start, V.rows_kuhn_mc, V.rows_leduc, V.rows_leduc_mc,
                V.rows_anmeldung_grid, V.rows_anmeldung_strafe)
    for fn in builders:
        rows = fn(tables)
        assert rows
        for row in rows:
            assert md_row(row) in README, (fn.__name__, row)


def test_hypothesis_table_has_h1_to_h12_with_a_clear_stand():
    rows = re.findall(r"^\| (H\d+) \|(?:\\\||[^|])*\|\s*\*\*([^*]+)\*\*", README, flags=re.M)
    assert [h for h, _ in rows] == [f"H{i}" for i in range(1, 13)]
    assert [a.split()[0].rstrip(",:") for _, a in rows] == ["Ja", "Ja", "Ja", "Teilweise", "Ja", "Teilweise", "Nein", "Teilweise", "Ja", "Ja", "Offen", "Offen"]


def test_math_blocks_are_display_equations_one_per_block():
    blocks = re.findall(r"^\$\$.*\$\$$", T.MATH_MARKDOWN, flags=re.M)
    assert len(blocks) >= 8 and T.MATH_MARKDOWN.count("$$") == 2 * len(blocks)


# --- Kernfrage und Modell ----------------------------------------------------------------------------------------------------------------------
def test_kernfrage_numbers(tables):
    core = README[README.index("## Kernfrage"):README.index("## Befunde und Korrekturen")]
    bans = {b["key"]: F(b["cost"]) for b in tables["bans"]["bans"]}
    assert bans["s1_no_bluff"] == F(1, 9) and bans["s0_no_bluff"] == 0
    has(core, "−1/18 (−0,0556)", "1/9 (0,1111)", "den ersten 0 Einsätze", f"{4 * 13 + 1} Sequenzen", german(12 ** 13, 0), "(H1, H2)", "(H8)", "(H3)", "(H5)", "(H4)", "(H6)", "(H7)")


def test_model_section_sizes(tables):
    model = README[README.index("## Modell"):README.index("## Methodik")]
    T3, _ = kuhn_instance(3)
    lp = tables["leduc_lp"]
    has(model, f"Baum: {T3.n} Knoten, {T3.nterm} Endknoten, je Spieler {T3.ninfo[0]} Informationsmengen mit je zwei Knoten",
        f"Baum: {german(lp['nodes'], 0)} Knoten, {german(lp['terminals'], 0)} Endknoten, {lp['infosets']} Informationsmengen und {lp['sequences']} Sequenzen je Spieler",
        f"{sci(lp['reduced'][0])} × {sci(lp['reduced'][1])} reine Strategien")
    s = SC.Settings()
    assert (s.b, s.c, s.g, s.s, s.r, s.p) == (10, 2, 15, 20, 6, 30)
    has(model, "*b* = 10, *c* = 2, *g* = 15, *s* = 20, *r* = 6, *p* = 30 %", "Gebühr *f* = 1")


def test_plan_deviation_bullets(tables):
    sect = README[README.index("## Befunde und Korrekturen"):README.index("## Modell")]
    k = tables["kuhn"]
    has(sect, f"sind {german(slope(k['cfr_alt'], 1000, 300000), 2)}, {german(slope(k['cfr_clip'], 1000, 300000), 2)} und {german(slope(k['cfrplus'], 1000, 300000), 2)}")
    mc = [at(r, 100000) for r in tables["leduc_mc"]]
    m, sd = mean_sd(mc)
    has(sect, f"{sci(m)} ± {sci(sd)}")
    st = [at(r, 10000) for r in tables["start"]["cfrplus"]]
    m, sd = mean_sd(st)
    has(sect, f"{sci(m)} ± {sci(sd)}")
    has(sect, f"({len(tables['bans']['bans'])} Verbote, {len(tables['bans']['rules'])} Faustregeln", "alle 24 Sequenzen")
    assert len(tables["family"]["ranges"]["0"]) + len(tables["family"]["ranges"]["1"]) == 24
    fees = tables["anmeldung"]["fee_values"]
    assert len(fees) == 4 and set(fees) == {"229/25"}
    has(sect, "4 Werte von *f*", "229/25 Euro je Sendung", "Port 9227")


# --- Hypothesen -----------------------------------------------------------------------------------------------------------------------------------
def test_h1_exact_values(tables):
    row = row_of("H1")
    exact = {r["n"]: F(r["value_exact"]) for r in tables["size"]["rows"] if "value_exact" in r}
    assert exact == {2: 0, 3: F(-1, 18), 4: F(-1, 24), 5: F(-1, 15), 6: F(-11, 180)}
    has(row, "**Ja**", "Spielwerte für n = 2 bis 6 exakt: " + ", ".join(f"n = {n}: {frac(v)}" for n, v in exact.items()) + ".", "(27 × 64)", "64 × 64", "(n = 2 bis 4 geprüft)")


def test_h2_family(tables):
    row = row_of("H2")
    fam = tables["family"]
    assert fam["lin_king"] == ["0", "0"] and fam["lin_queen"] == ["1/3", "1/3"]
    has(row, "**Ja**", "allen 24 Sequenzen", "[0, 1/3]", "„König − 3·Bube“ in [0, 0]", "„Dame − Bube“ in [1/3, 1/3]", "α = 0, 1/12, 1/6, 1/4, 1/3")
    assert [g["alpha"] for g in fam["family"]] == ["0", "1/12", "1/6", "1/4", "1/3"] and all(g["gap0"] == g["gap1"] == "0" for g in fam["family"])
    assert all(r["lo"] == r["hi"] for r in fam["ranges"]["1"])


def test_h3_sizes_counted_at_the_tree(tables):
    row = row_of("H3")
    rows = {r["n"]: r for r in tables["size"]["rows"]}
    for n in range(2, 14):
        T_, SF = kuhn_instance(n)
        assert SF.n[0] == 4 * n + 1 and rows[n]["reduced"] == [3 ** n, 4 ** n]
    has(row, "4n + 1", "3ⁿ · 4ⁿ", "n = 2 bis 13", f"bei n = 6 braucht die Sequenzform {german(rows[6]['t_seq'], 3)} s", f"lösen {german(rows[6]['t_normal'], 1)} s", "nicht monoton")
    values = [rows[n]["value_float"] for n in range(2, 14)]
    diffs = [b - a for a, b in zip(values, values[1:])]
    assert any(d > 0 for d in diffs) and any(d < 0 for d in diffs)          # der Spielwert steigt und fällt in n: nicht monoton


def test_h4_last_iteration(tables):
    row = row_of("H4")
    k = tables["kuhn"]
    late = [v for t, v in zip(k["cfr"]["t"], k["cfr"]["last"]) if t >= 1000]
    has(row, "**Teilweise**", f"zwischen {sci(min(late))} und {sci(max(k['cfr']['last']))}", f"das Mittel bei {sci(at(k['cfr'], 300000))} (T = 300 000)",
        f"{sci(at(k['cfrplus'], 300000, 'last'))} und {sci(at(k['dcfr'], 300000, 'last'))}", f"{sci(at(k['cfrplus'], 300000))} und {sci(at(k['dcfr'], 300000))}")
    assert max(k["cfr"]["last"]) > 0.2 and at(k["cfr"], 300000, "last") > 100 * at(k["cfr"], 300000)       # die letzte Iteration liegt weit über dem Mittel
    assert at(k["cfrplus"], 300000, "last") > 1000 * at(k["cfrplus"], 300000)


def test_h5_decomposition(tables):
    row = row_of("H5")
    k = tables["kuhn"]
    has(row, "**Ja**", f"{sci(at(k['cfr'], 1000))} (CFR) gegen {sci(at(k['cfrplus'], 1000))} (CFR⁺), Faktor {german(at(k['cfr'], 1000) / at(k['cfrplus'], 1000), 0)}",
        f"von {german(slope(k['cfr'], 1000, 300000), 2)} auf {german(slope(k['cfr_alt'], 1000, 300000), 2)}",
        f"(Faktor {german(at(k['cfr_alt'], 1000) / at(k['cfr_clip'], 1000), 1)} und {german(at(k['cfr_clip'], 1000) / at(k['cfrplus'], 1000), 1)})")
    # die Steigung kommt von der Abwechslung: der Sprung CFR → abwechselnd ist größer als jede der beiden späteren Änderungen zusammen
    s = [slope(k[v], 1000, 300000) for v in ("cfr", "cfr_alt", "cfr_clip", "cfrplus")]
    assert abs(s[1] - s[0]) > 0.3 and abs(s[2] - s[1]) < 0.1 and abs(s[3] - s[2]) < 0.1
    assert at(k["cfr_alt"], 1000) > at(k["cfr_clip"], 1000) > at(k["cfrplus"], 1000)


def test_h6_discounted_cfr(tables):
    row = row_of("H6")
    k, ld = tables["kuhn"], tables["leduc"]
    pts = [(t, x, y) for t, x, y in zip(k["cfrplus"]["t"], k["cfrplus"]["avg"], k["dcfr"]["avg"]) if t >= 100]
    wins = [y < x for _, x, y in pts]
    stable = next(pts[i][0] for i in range(len(pts)) if all(wins[i:]))
    assert at(k["dcfr"], 1000) > at(k["cfrplus"], 1000) and at(ld["dcfr"], 1000) < at(ld["cfrplus"], 1000)
    has(row, "**Teilweise**", f"{sci(at(k['dcfr'], 1000))} gegen {sci(at(k['cfrplus'], 1000))}", f"{sci(at(ld['dcfr'], 1000))} gegen {sci(at(ld['cfrplus'], 1000))}",
        f"an {sum(wins)} von {len(pts)} Prüfpunkten ab T = 100", f"durchgehend erst ab T = {german(stable, 0).replace('.', ' ')}")


def test_h7_sampling(tables):
    row = row_of("H7")
    worse_leduc = 0
    for t in (1000, 3000, 10000, 30000, 100000):
        m = sum(at(r, t) for r in tables["leduc_mc"]) / 4
        nodes = sum(r["nodes"][r["t"].index(t)] for r in tables["leduc_mc"]) / 4
        for v in XP.LEDUC_VARIANTS:
            run = tables["leduc"][v]
            best = max(((tt, g) for tt, g, n in zip(run["t"], run["avg"], run["nodes"]) if n <= nodes), key=lambda x: x[0])
            assert m > best[1], (t, v)
        worse_leduc += 1
    worse_kuhn = 0
    for t in XP.KUHN_MC_MARKS:
        m = sum(at(r, t) for r in tables["kuhn_mc"]) / 4
        nodes = sum(r["nodes"][r["t"].index(t)] for r in tables["kuhn_mc"]) / 4
        run = tables["kuhn"]["cfrplus"]
        best = max(((tt, g) for tt, g, n in zip(run["t"], run["avg"], run["nodes"]) if n <= nodes), key=lambda x: x[0])
        worse_kuhn += m > best[1]
    has(row, "**Nein**", f"an {worse_leduc} von 5 vergleichbaren Prüfpunkten", "(1 000 bis 100 000 Iterationen)", f"an {worse_kuhn} von {len(XP.KUHN_MC_MARKS)} Prüfpunkten über der von CFR⁺")
    assert worse_leduc == 5 and worse_kuhn == len(XP.KUHN_MC_MARKS)


def test_h8_bluffing_and_pure_strategies(tables):
    row = row_of("H8")
    pure = tables["bans"]["pure"]
    assert (F(pure["first"]), F(pure["second"]), F(pure["cost_first"]), F(pure["cost_second"])) == (F(-1, 6), F(-1, 6), F(1, 9), F(2, 9))
    has(row, "**Teilweise, asymmetrisch**", "1/9 (0,1111) Einsätze je Hand", "für den ersten 0 (Freiheitsgrad", "1/9 (0,1111) für den ersten, 2/9 (0,2222) für den zweiten Spieler")


def test_h9_normal_form_regret_matching(tables):
    row = row_of("H9")
    k, rm = tables["kuhn"], tables["rm"]
    assert at(rm["rmplus_nf"], 10000) > 10 * at(k["cfrplus"], 10000)
    has(row, "**Ja**", f"{sci(at(rm['rmplus_nf'], 10000))} (RM⁺, Normalform) gegen {sci(at(k['cfrplus'], 10000))} (CFR⁺)",
        f"{german(slope(rm['rmplus_nf'], 100, 30000), 2)} gegen {german(slope(k['cfrplus'], 100, 30000), 2)}", f"{sci(at(rm['rm_nf'], 30000))} bei T = 30 000")


def test_h10_anmeldung(tables):
    row = row_of("H10")
    a = tables["anmeldung"]
    assert sum(c["same"] for c in a["grid"]) == 30 == len(a["grid"]) and sum(c["same"] for c in a["extra"]) == 7 == len(a["extra"])
    assert [c["regime"] for c in a["grid"]].count("gemischt") == 22 and [c["regime"] for c in a["grid"]].count("alle lügen") == 8
    std = a["strafen"][2]
    assert std["s"] == 20 and (F(std["lam"]), F(std["kap"]), F(std["value"])) == (F(2, 15), F(9, 35), F(229, 25))
    has(row, "**Ja**", "30 von 30 Zellen", "7 von 7 Zusatzzeilen", "*λ* = 2/15", "*κ* = 9/35", "Wert 229/25 (9,16) Euro je Sendung")


def test_h11_h12_are_open(tables):
    assert "**Offen**" in row_of("H11") and "**Offen**" in row_of("H12")
    has(row_of("H12"), german(tables["leduc_lp"]["value0"], 6))
    assert tables["leduc_lp"]["value0"] == pytest.approx(-0.0856064240780005, abs=1e-12)


def test_further_findings_paragraph(tables):
    para = README[README.index("Weitere Befunde:"):README.index("## Ehrliche Grenzen")]
    a, k = tables["anmeldung"], tables["kuhn"]
    assert {c["kap"] for c in a["p_rows"]} == {"9/35"} and [c["p"] for c in a["p_rows"]] == ["1/10", "3/10", "1/2", "7/10", "9/10"] and all(c["regime"] == "gemischt" for c in a["p_rows"])
    assert len({c["lam"] for c in a["p_rows"]}) == 5
    inc = lambda r: sum(1 for x, y in zip(r["avg"], r["avg"][1:]) if y > x)
    has(para, "9/35 für *p* = 1/10 bis 9/10", "*f* = 0, 1, 3, 5 geben alle 229/25 Euro", f"steigt an {inc(k['cfrplus'])} von {len(k['cfrplus']['t']) - 1} aufeinanderfolgenden",
        f"Discounted CFR {inc(k['dcfr'])}, abwechselndes CFR {inc(k['cfr_alt'])}, mit gekappten Regrets {inc(k['cfr_clip'])}")
    assert inc(k["cfrplus"]) > 0 and inc(k["dcfr"]) > 0                                          # das Mittel fällt nicht monoton


def test_strafe_effects_are_monotone(tables):
    """Je höher die Strafe, desto kleiner Lügenanteil und Kontrollanteil (p = 3/10, Strafen 5 bis 160)."""
    rows = tables["anmeldung"]["strafen"]
    lam = [F(c["lam"]) for c in rows]
    kap = [F(c["kap"]) for c in rows]
    assert [c["s"] for c in rows] == [5, 10, 20, 40, 80, 160] and lam == sorted(lam, reverse=True) and kap == sorted(kap, reverse=True)
    assert len(set(lam)) == 6 and len(set(kap)) == 6


def test_readme_names_the_tool_facts(tables):
    has(README, "Port 9227", "vdi_rng.py", "ab-test-demo/abt_rng.py", "nicht im Volltext geprüft", "Linux-CI (Python 3.12) ist noch nicht gelaufen")
    assert "Mutationstest läuft für diese Demo nicht" in README


def test_loss_curves_have_one_zero_each_and_five_along_the_family():
    """Die Einzelabweichungen sind nur im Gleichgewichtspunkt selbst ohne Lücke (je 1 von 13 Rasterpunkten), entlang der Familie sind es α = 0 bis 1/3 in Zwölfteln (5 von 13)."""
    curves = V.loss_curves()
    zero = {name: sum(1 for g in gaps if g == 0) for name, (_, gaps, _) in curves.items()}
    assert sorted(zero.values()) == [1, 1, 1, 1, 5]
    family = next(n for n in curves if n.startswith("Erster Spieler: Bube"))
    assert zero[family] == 5 and all(g == 0 for g in curves[family][1][:5]) and all(g > 0 for g in curves[family][1][5:])
    assert "an 1, 1, 1, 1 von je 13 Rasterpunkten 0" in V.verdict_curves(curves)[1] and "an 5 von 13" in V.verdict_curves(curves)[1]
