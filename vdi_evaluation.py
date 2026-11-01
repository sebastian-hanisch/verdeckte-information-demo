"""Auswertung: Ansichten (rechnen aus den Einstellungen) und Verdikte (reine Funktionen: Zahlen hinein, (Art, Text) heraus), dazu die Zeilenbauer für Tabellen.

Befundzahlen in Texten kommen aus der Rechnung oder aus den vorgerechneten Reihen (data/tables.json); was die README nennt, steht in tests/test_claims.py."""

import math
import time
from dataclasses import dataclass
from fractions import Fraction as Fr

import vdi_anmeldung as AN
import vdi_cfr as CF
import vdi_constants as C
import vdi_exact as X
import vdi_experiments as XP
import vdi_games as G
import vdi_kuhn as K
import vdi_normal as N
import vdi_runs as R
import vdi_scenario as SC
import vdi_seqform as SQ
import vdi_strategy as S
from vdi_scenario import Settings

MINUS = "−"
SUPER = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
KUHN_VALUE = Fr(-1, 18)


# --- Zahlenformat ----------------------------------------------------------------------------------------------------------------------------------
def de(x, nd: int = 2) -> str:
    """Deutsches Zahlenformat: Dezimalkomma, Tausenderpunkt, echtes Minuszeichen."""
    s = f"{float(x):,.{nd}f}"
    if float(s.replace(",", "")) == 0:
        s = s.lstrip("-")                      # kein „−0,00“
    return s.replace(",", "T").replace(".", ",").replace("T", ".").replace("-", MINUS)


def sci(x, nd: int = 1) -> str:
    """Wissenschaftliche Schreibweise 7,9·10⁻³ (für Lücken); 0 als „0“."""
    x = float(x)
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    m = x / 10 ** e
    if round(m, nd) >= 10:
        m, e = m / 10, e + 1
    return f"{de(m, nd)}·10{str(e).translate(SUPER)}"


def frac(x) -> str:
    """Bruch als Text mit echtem Minuszeichen: −1/18, 2/9, 0."""
    x = Fr(x)
    t = str(x)
    return t.replace("-", MINUS)


def frac_dec(x, nd: int = 4) -> str:
    """Bruch mit Dezimalwert: −1/18 (−0,0556)."""
    x = Fr(x)
    return frac(x) if x.denominator == 1 else f"{frac(x)} ({de(x, nd)})"


def eur(x, nd: int = 2) -> str:
    return de(x, nd)


# --- Reiter 1: Kuhn-Strategie ----------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class StrategyView:
    alpha: Fr
    value: Fr                 # Wert des Profils an den ersten Spieler (Einsätze je Hand)
    loss_first: Fr            # Lücke der Strategie des ersten Spielers (Gewinn der besten Antwort des zweiten über den Gleichgewichtswert)
    loss_second: Fr
    in_family: bool
    rows: tuple               # Wahrscheinlichkeiten je Informationsmenge (Dicts)


def kuhn_profile(s: Settings):
    """Das Profil der fünf Strategieregler (alle übrigen Entscheidungen sind in der Familie fest)."""
    T, _ = SC.kuhn_instance(3)
    q = SC.strategy_parameters(s)
    return T, K.family_profile(T, q["alpha"], king=q["king"], bluff=q["bluff"], call=q["call"], queen_call=q["queen_call"])


def strategy_rows(T, st) -> tuple:
    """Eine Zeile je Informationsmenge: Spieler, Karte, Lage, Handlung und ihre Wahrscheinlichkeit."""
    rows = []
    for p in (0, 1):
        for card in (2, 1, 0):
            for hist in (("", "pb") if p == 0 else ("p", "b")):
                i = K.info_index(T, p, card, hist)
                rows.append({"player": p, "card": card, "hist": hist, "prob": st[p][i][1]})
    return tuple(rows)


def action_name(player: int, hist: str) -> str:
    """Name der zweiten Aktion in der Lage: Setzen (am Anfang und nach Pass) bzw. Mitgehen (gegen ein Setzen)."""
    return "Setzen" if hist in ("", "p") else "Mitgehen"


def situation_name(player: int, hist: str) -> str:
    return {("0", ""): "erster Zug", ("0", "pb"): "nach Pass und Setzen des Gegners", ("1", "p"): "nach Pass des Gegners", ("1", "b"): "nach Setzen des Gegners"}[(str(player), hist)]


def strategy_view(s: Settings) -> StrategyView:
    T, st = kuhn_profile(s)
    g0, g1, _ = S.exploitability(T, st, KUHN_VALUE)
    q = SC.strategy_parameters(s)
    return StrategyView(alpha=q["alpha"], value=S.profile_value(T, st), loss_first=g1, loss_second=g0,
                        in_family=K.in_family(q["alpha"], q["king"], q["bluff"], q["call"], q["queen_call"]), rows=strategy_rows(T, st))


def loss_curves() -> dict:
    """Lücke der abweichenden Seite, wenn genau eine Entscheidung von 0 bis 1 (in Zwölfteln) läuft und die übrigen im Gleichgewicht mit α = 1/6 stehen; die α-Kurve läuft entlang der Familie
    (König 3α, Dame α + 1/3, begrenzt auf 1). Rückgabe: Name → (x-Werte als Zwölftel, Lücken als Brüche, Seite der Lücke)."""
    T, _ = SC.kuhn_instance(3)
    a = Fr(1, 6)
    xs = list(range(C.TWELFTHS + 1))
    out = {}

    def gaps(**kw):
        g = S.exploitability(T, K.family_profile(T, **kw), KUHN_VALUE)
        return g[0], g[1]

    out["Zweiter Spieler: Bube setzt nach Pass (Bluff)"] = (xs, [gaps(alpha=a, bluff=Fr(k, 12))[0] for k in xs], 2)
    out["Zweiter Spieler: Dame geht gegen Setzen mit"] = (xs, [gaps(alpha=a, call=Fr(k, 12))[0] for k in xs], 2)
    out["Erster Spieler: König setzt im ersten Zug"] = (xs, [gaps(alpha=a, king=Fr(k, 12))[1] for k in xs], 1)
    out["Erster Spieler: Dame geht nach Pass–Setzen mit"] = (xs, [gaps(alpha=a, queen_call=Fr(k, 12))[1] for k in xs], 1)
    out["Erster Spieler: Bube setzt (Familie: König 3α, Dame α + 1/3)"] = (xs, [gaps(alpha=Fr(k, 12), king=min(Fr(1), 3 * Fr(k, 12)), queen_call=min(Fr(1), Fr(k, 12) + Fr(1, 3)))[1] for k in xs], 1)
    return out


# --- Reiter 2: Größenvergleich ---------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class SizeView:
    n: int
    nodes: int
    sequences: int
    reduced: tuple
    entries: int
    value_float: float
    value_exact: Fr | None
    value_normal: float | None
    t_seq: float
    t_exact: float | None
    t_normal: float | None


def size_view(n: int) -> SizeView:
    """Größe und Wert des Kuhn-Spiels mit n Karten auf beiden Wegen (Zeiten: diese Rechnung, in Sekunden, plattformabhängig)."""
    T, SF = SC.kuhn_instance(n)
    SQ.solve_lp(SC.kuhn_instance(2)[1], 0)          # Anlaufkosten von scipy aus der Zeitmessung nehmen
    t0 = time.perf_counter()
    value_float = SQ.solve_lp(SF, 0)[0]
    t_seq = time.perf_counter() - t0
    reduced = (N.reduced_count(T, SF, 0), N.reduced_count(T, SF, 1))
    value_exact = t_exact = value_normal = t_normal = None
    if n <= C.N_EXACT_MAX:
        t0 = time.perf_counter()
        value_exact = X.exact_seq_lp(SF, 0)[0]
        t_exact = time.perf_counter() - t0
    if n <= C.N_NORMAL_MAX:
        t0 = time.perf_counter()
        M, _, _ = N.normal_matrix(T, SF)
        value_normal = N.matrix_game(M)[0]
        t_normal = time.perf_counter() - t0
    return SizeView(n, T.n, SF.n[0], reduced, reduced[0] * reduced[1], value_float, value_exact, value_normal, t_seq, t_exact, t_normal)


def size_rows(n_max: int = C.N_MAX) -> list[dict]:
    """Größentabelle für n = 2 … n_max aus den Formeln 4n + 1 und 3ⁿ·4ⁿ (die Tests prüfen sie gegen die Zählung am Baum)."""
    return [{"Karten n": n, "Sequenzen je Spieler": 4 * n + 1, "reine Strategien erster Spieler": 3 ** n, "reine Strategien zweiter Spieler": 4 ** n,
             "Einträge der Normalform": f"{12 ** n:,}".replace(",", ".")} for n in range(2, n_max + 1)]


# --- Reiter 3: Regret-Verfahren -------------------------------------------------------------------------------------------------------------------
def kuhn_value_float(n: int) -> float:
    T, SF = SC.kuhn_instance(n)
    return SQ.solve_lp(SF, 0)[0]


def kuhn_runs(n: int, steps: int, start: str, seed: int) -> dict:
    """Alle fünf Verfahren auf dem Kuhn-Spiel mit n Karten (und, bis n = 5, Regret Matching auf der Normalform). Der Zufallsstart gilt für die Baumverfahren."""
    T, SF = SC.kuhn_instance(n)
    v0 = kuhn_value_float(n)
    marks = R.checkpoints(steps)
    init = CF.random_regrets(T, R.stream(seed, 7)) if start == "zufall" else None
    runs = {v: R.run_variant(T, v, steps, v0, marks=marks, init_regrets=init) for v in CF.VARIANTS}
    if n <= C.N3_NORMAL_MAX:
        M, _, _ = N.normal_matrix(T, SF)
        for name, plus in (("rm_nf", False), ("rmplus_nf", True)):
            res = N.regret_matching_normal(M, v0, steps, marks, plus=plus)
            runs[name] = {"t": [r[0] for r in res], "avg": [r[1] for r in res], "avg_sum": [r[2] for r in res], "nodes": [r[0] * 2 * M.shape[0] * M.shape[1] for r in res]}
    return {"v0": v0, "runs": runs, "nodes_tree": T.n}


def leduc_runs(steps: int, mc: int, seed: int) -> dict:
    """Leduc: Spielwert aus der Sequenzform, drei volle Verfahren und externes Sampling mit dem Zufalls-Seed."""
    T, SF = SC.leduc_instance()
    v0 = SQ.solve_lp(SF, 0)[0]
    marks = R.checkpoints(steps)
    runs = {v: R.run_variant(T, v, steps, v0, marks=marks) for v in XP.LEDUC_VARIANTS}
    sampling = R.run_sampling(T, R.stream(seed, 3), mc, v0, R.checkpoints(mc))
    return {"v0": v0, "runs": runs, "sampling": sampling, "nodes_tree": T.n}


def variant_label(key: str) -> str:
    return {**CF.VARIANTS, "rm_nf": "Regret Matching (Normalform)", "rmplus_nf": "RM⁺ (Normalform)", "mccfr": "Externes Sampling"}[key]


def run_rows(runs: dict, steps: int) -> list[dict]:
    """Eine Zeile je Verfahren: Lücke des Mittels und der letzten Iteration am letzten Prüfpunkt, Steigung ab T = 100, erster Prüfpunkt mit Lücke ≤ 10⁻³."""
    rows = []
    for key, run in runs.items():
        t_last = run["t"][-1]
        lo = 100 if t_last >= 300 else run["t"][0]
        hit = R.first_below(run, 1e-3)
        rows.append({"Verfahren": variant_label(key), "Lücke Mittel": sci(run["avg"][-1]), "Lücke letzte Iteration": sci(run["last"][-1]) if "last" in run else "–",
                     "Steigung": de(R.slope_between(run, lo, t_last), 2), "erstmals ≤ 10⁻³": f"T = {hit[0]}" if hit else "nicht erreicht"})
    return rows


# --- Reiter 4: Anmeldung -----------------------------------------------------------------------------------------------------------------------------
def anmeldung_view(s: Settings) -> dict:
    """Die Zelle zu den Reglern: geschlossene Form, Sequenzform-LP und Normalform in Brüchen, Lücken des Profils."""
    return XP.anmeldung_cell(Fr(s.p, 100), s=s.s, c=s.c, g=s.g, r=s.r, b=s.b, f=C.A_FEE)


def anmeldung_curves(s: Settings, axis: str) -> dict:
    """Lügenanteil λ, Kontrollanteil κ und Wert über dem Anteil riskanter Sendungen p (1 … 99 %) oder der Strafe s (0 … 160), geschlossene Form."""
    xs = list(range(1, 100)) if axis == "p" else list(range(0, C.A_S_MAX + 1, 2))
    lam, kap, val, reg = [], [], [], []
    for x in xs:
        game = G.Anmeldung(b=s.b, c=s.c, f=C.A_FEE, g=s.g, s=s.s if axis == "p" else x, r=s.r, p=Fr(x, 100) if axis == "p" else Fr(s.p, 100))
        l_, k_, v_, r_ = AN.closed_form(game.par)
        lam.append(float(l_))
        kap.append(float(k_))
        val.append(float(v_))
        reg.append(r_)
    return {"x": xs, "lam": lam, "kap": kap, "value": val, "regime": reg}


# --- Hilfen für die vorgerechneten Reihen ----------------------------------------------------------------------------------------------------------
def at(run: dict, t: int, key: str = "avg") -> float:
    """Wert einer Reihe am Prüfpunkt t."""
    return run[key][run["t"].index(t)]


def at_nodes(run: dict, nodes: int, key: str = "avg"):
    """(Prüfpunkt, Wert) des letzten Prüfpunkts mit höchstens `nodes` besuchten Knoten, oder None."""
    best = None
    for t, v, n in zip(run["t"], run[key], run["nodes"]):
        if n <= nodes:
            best = (t, v)
    return best


def seed_mean(runs: list, t: int) -> dict:
    """Mittel, Standardabweichung, kleinster und größter Wert der Lücke am Prüfpunkt t über die Zufalls-Seeds."""
    m = R.mean_sd([at(r, t) for r in runs])
    m["min"], m["max"] = min(m["values"]), max(m["values"])
    return m


def mean_nodes(runs: list, t: int) -> float:
    """Mittlere Zahl besuchter Knoten am Prüfpunkt t über die Zufalls-Seeds."""
    return sum(r["nodes"][r["t"].index(t)] for r in runs) / len(runs)


def decomposition(tables: dict) -> dict:
    """Zerlegung des Vorsprungs von CFR⁺ gegenüber CFR in drei Schritte (Kuhn, drei Karten): Abwechslung der Aktualisierung (cfr → cfr_alt), Kappen der Regrets (→ cfr_clip),
    lineare Mittelung (→ cfrplus). Je Stufe die Lücken bei T = 1 000 / 10 000 / 300 000, die Steigung (T = 1 000 bis 300 000) und der Faktor zur Vorstufe bei T = 1 000."""
    chain = ("cfr", "cfr_alt", "cfr_clip", "cfrplus")
    out = {}
    prev = None
    for key in chain:
        run = tables["kuhn"][key]
        out[key] = {"gaps": {t: at(run, t) for t in (1000, 10000, 300000)}, "slope": R.slope_between(run, 1000, 300000),
                    "factor": (at(tables["kuhn"][prev], 1000) / at(run, 1000)) if prev else None}
        prev = key
    return out


def dcfr_vs_cfrplus(tables: dict) -> dict:
    """Wie oft liegt Discounted CFR unter CFR⁺ (Kuhn, Prüfpunkte ab T = 100)? Rückgabe: Zahl der Prüfpunkte, Zahl mit Vorsprung für Discounted CFR, erster Prüfpunkt, ab dem es durchgehend so ist."""
    a, b = tables["kuhn"]["cfrplus"], tables["kuhn"]["dcfr"]
    pts = [(t, x, y) for t, x, y in zip(a["t"], a["avg"], b["avg"]) if t >= 100]
    wins = [y < x for _, x, y in pts]
    stable = None
    for k in range(len(pts)):
        if all(wins[k:]):
            stable = pts[k][0]
            break
    return {"points": len(pts), "dcfr_better": sum(wins), "stable_from": stable}


def dots(x: int) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner (deutsch)."""
    return f"{int(x):,}".replace(",", ".")


def fmt_t(t: int) -> str:
    """Schritte mit Leerzeichen als Tausendertrenner."""
    return f"{int(t):,}".replace(",", " ")


# --- Zeilenbauer (Tabellen der App und der README) -------------------------------------------------------------------------------------------------
def rows_family(tables: dict) -> list[dict]:
    """Gleichgewichtsmenge: Realisierungswahrscheinlichkeit der Setzen-/Mitgehen-Sequenzen als Bereich über alle Gleichgewichte."""
    names = G.card_names(3)
    out = []
    for p in ("0", "1"):
        for r in tables["family"]["ranges"][p]:
            if r["action"] != 1:
                continue
            lo, hi = Fr(r["lo"]), Fr(r["hi"])
            out.append({"Spieler": "erster" if p == "0" else "zweiter", "Karte": names[r["card"]], "Lage": situation_name(int(p), r["hist"]), "Handlung": action_name(int(p), r["hist"]),
                        "Bereich": frac(lo) if lo == hi else f"{frac(lo)} bis {frac(hi)}"})
    return out


def rows_bans(tables: dict) -> list[dict]:
    return [{"Verbot": b["text"], "Spieler": "erster" if b["player"] == 0 else "zweiter", "garantierter Wert": frac_dec(b["guaranteed"]), "Kosten": frac_dec(b["cost"])} for b in tables["bans"]["bans"]]


def rows_rules(tables: dict) -> list[dict]:
    return [{"Faustregel": r["name"], "Kosten als erster Spieler": frac_dec(r["cost_first"]), "Kosten als zweiter Spieler": frac_dec(r["cost_second"])} for r in tables["bans"]["rules"]]


def rows_size(tables: dict) -> list[dict]:
    out = []
    for r in tables["size"]["rows"]:
        value = frac_dec(r["value_exact"]) if "value_exact" in r else de(r["value_float"], 4)
        out.append({"Karten n": r["n"], "Knoten": r["nodes"], "Sequenzen je Spieler": r["sequences"],
                    "Normalform": f"{r['reduced'][0]:,} × {r['reduced'][1]:,}".replace(",", ".") if "reduced" in r else "–", "Spielwert": value,
                    "Zeit Sequenzform (s)": de(r["t_seq"], 3), "Zeit Normalform (s)": de(r["t_normal"], 3) if "t_normal" in r else "–"})
    return out


def rows_kuhn_runs(tables: dict) -> list[dict]:
    out = []
    for key in list(CF.VARIANTS) + ["rm_nf", "rmplus_nf"]:
        run = tables["kuhn"].get(key) or tables["rm"][key]
        top = 300000 if key in tables["kuhn"] else 30000
        hit = R.first_below(run, 1e-3)
        out.append({"Verfahren": variant_label(key), "T = 1 000": sci(at(run, 1000)), "T = 10 000": sci(at(run, 10000)), "größtes T": f"{sci(at(run, top))} (T = {fmt_t(top)})",
                    "Steigung T = 100 bis 30 000": de(R.slope_between(run, 100, 30000), 2),
                    "erstmals ≤ 10⁻³": f"T = {fmt_t(hit[0])} ({fmt_t(hit[1])} Knoten)" if hit else "nicht erreicht"})
    return out


def rows_decomposition(tables: dict) -> list[dict]:
    d = decomposition(tables)
    labels = {"cfr": "CFR (gleichzeitig)", "cfr_alt": "+ Abwechslung der Aktualisierung", "cfr_clip": "+ Kappen der Regrets", "cfrplus": "+ lineare Mittelung (= CFR⁺)"}
    return [{"Stufe": labels[k], "T = 1 000": sci(v["gaps"][1000]), "T = 10 000": sci(v["gaps"][10000]), "T = 300 000": sci(v["gaps"][300000]), "Steigung T = 1 000 bis 300 000": de(v["slope"], 2),
             "Faktor zur Vorstufe bei T = 1 000": de(v["factor"], 1) if v["factor"] else "–"} for k, v in d.items()]


def rows_last(tables: dict) -> list[dict]:
    out = []
    for key in CF.VARIANTS:
        run = tables["kuhn"][key]
        out.append({"Verfahren": variant_label(key), "T = 1 000": sci(at(run, 1000, "last")), "T = 10 000": sci(at(run, 10000, "last")), "T = 30 000": sci(at(run, 30000, "last")),
                    "T = 300 000": sci(at(run, 300000, "last"))})
    return out


def rows_start(tables: dict) -> list[dict]:
    out = []
    for key in ("cfr", "cfrplus", "dcfr"):
        runs = tables["start"][key]
        cells = {f"T = {fmt_t(t)}": f"{sci(seed_mean(runs, t)['mean'])} ± {sci(seed_mean(runs, t)['sd'])}" for t in XP.START_MARKS}
        out.append({"Verfahren": variant_label(key), **cells, "gleichverteilter Start, T = 10 000": sci(at(tables["kuhn"][key], 10000))})
    return out


def rows_kuhn_mc(tables: dict) -> list[dict]:
    out = []
    for t in XP.KUHN_MC_MARKS:
        m = seed_mean(tables["kuhn_mc"], t)
        nodes = mean_nodes(tables["kuhn_mc"], t)
        cp = at_nodes(tables["kuhn"]["cfrplus"], nodes)
        out.append({"Iterationen": fmt_t(t), "besuchte Knoten (Mittel)": fmt_t(round(nodes)), "Lücke Sampling": f"{sci(m['mean'])} ± {sci(m['sd'])}",
                    "kleinster / größter Wert": f"{sci(m['min'])} / {sci(m['max'])}", "Lücke CFR⁺ bei gleichem Aufwand": sci(cp[1]) if cp else "–"})
    return out


def rows_leduc(tables: dict) -> list[dict]:
    out = []
    for key in XP.LEDUC_VARIANTS:
        run = tables["leduc"][key]
        hit = R.first_below(run, 1e-3)
        out.append({"Verfahren": variant_label(key), "T = 1 000": sci(at(run, 1000)), "T = 2 000": sci(at(run, 2000)), "Steigung T = 100 bis 2 000": de(R.slope_between(run, 100, 2000), 2),
                    "letzte Iteration, T = 2 000": sci(at(run, 2000, "last")), "erstmals ≤ 10⁻³": f"T = {fmt_t(hit[0])} ({fmt_t(hit[1])} Knoten)" if hit else "nicht erreicht"})
    return out


def rows_leduc_mc(tables: dict) -> list[dict]:
    out = []
    for t in XP.LEDUC_MC_MARKS:
        m = seed_mean(tables["leduc_mc"], t)
        nodes = mean_nodes(tables["leduc_mc"], t)
        cells = {}
        for key in XP.LEDUC_VARIANTS:
            hit = at_nodes(tables["leduc"][key], nodes)
            cells[f"Lücke {variant_label(key)} bei gleichem Aufwand"] = sci(hit[1]) if hit else "weniger als ein Schritt"
        out.append({"Iterationen": fmt_t(t), "besuchte Knoten (Mittel)": fmt_t(round(nodes)), "Lücke Sampling": f"{sci(m['mean'])} ± {sci(m['sd'])}",
                    "kleinster / größter Wert": f"{sci(m['min'])} / {sci(m['max'])}", **cells})
    return out


def rows_anmeldung_grid(tables: dict) -> list[dict]:
    out = []
    for c in tables["anmeldung"]["grid"]:
        out.append({"Anteil riskant p": frac(c["p"]), "Strafe s": c["s"], "Regime": c["regime"], "Lügenanteil λ": frac_dec(c["lam"], 3), "Kontrollanteil κ": frac_dec(c["kap"], 3),
                    "Wert (Euro je Sendung)": frac_dec(c["value"], 3), "alle Wege gleich": "ja" if c["same"] else "nein"})
    return out


def rows_anmeldung_strafe(tables: dict) -> list[dict]:
    return [{"Strafe s": c["s"], "Lügenanteil λ": de(Fr(c["lam"]), 3), "Kontrollanteil κ": de(Fr(c["kap"]), 3), "Wert (Euro je Sendung)": de(Fr(c["value"]), 2),
             "erwartete Kontrollen je Sendung": de(Fr(c["controls"]), 3)} for c in tables["anmeldung"]["strafen"]]


def rows_anmeldung_live(cell: dict) -> list[dict]:
    return [{"Größe": "Regime", "Wert": cell["regime"]}, {"Größe": "Lügenanteil λ", "Wert": frac_dec(cell["lam"], 3)}, {"Größe": "Kontrollanteil κ nach „sauber“", "Wert": frac_dec(cell["kap"], 3)},
            {"Größe": "Wert (Sequenzform-LP, exakt)", "Wert": frac_dec(cell["value_seq"], 3)}, {"Größe": "Wert (Normalform 4 × 4, exakt)", "Wert": frac_dec(cell["value_nf"], 3)},
            {"Größe": "Wert (geschlossene Form)", "Wert": frac_dec(cell["value"], 3)}, {"Größe": "Lücken des Profils (Verlader / Kontrolleur)", "Wert": f"{frac(cell['gap0'])} / {frac(cell['gap1'])}"},
            {"Größe": "Anteil Riskanter unter den „sauber“ Gemeldeten", "Wert": frac_dec(cell["lying_share"], 3)}, {"Größe": "erwartete Kontrollen je Sendung", "Wert": frac_dec(cell["controls"], 3)}]


# --- Verdikte: reine Funktionen (Art, Text) -----------------------------------------------------------------------------------------------------
def verdict_main(view: StrategyView) -> tuple[str, str]:
    if view.loss_first == 0 and view.loss_second == 0:
        fam = f" Es gehört zur Familie mit α = {frac(view.alpha)}." if view.in_family else ""
        return "success", (f"Lücke 0 auf beiden Seiten: dieses Profil ist ein Gleichgewicht des Kuhn-Spiels, der Spielwert ist {frac_dec(KUHN_VALUE)} Einsätze je Hand an den ersten Spieler "
                           f"(das Profil erreicht {frac_dec(view.value)}).{fam}")
    parts = []
    if view.loss_first > 0:
        parts.append(f"Der erste Spieler gibt gegen die beste Antwort des zweiten {frac_dec(view.loss_first)} Einsätze je Hand gegenüber dem Gleichgewicht her.")
    if view.loss_second > 0:
        parts.append(f"Der zweite Spieler gibt gegen die beste Antwort des ersten {frac_dec(view.loss_second)} Einsätze je Hand her.")
    return "warning", "Kein Gleichgewicht. " + " ".join(parts)


def verdict_curves(curves: dict) -> tuple[str, str]:
    """Auf dem Raster 0 bis 1 in Zwölfteln: an wie vielen Punkten ist die Lücke jeder Kurve 0?"""
    zero = {name: sum(1 for g in gaps if g == 0) for name, (_, gaps, _) in curves.items()}
    family = next(n for n in curves if n.startswith("Erster Spieler: Bube"))
    singles = [zero[n] for n in curves if n != family]
    return "info", (f"Bei den vier Einzelabweichungen ist die Lücke an {', '.join(str(z) for z in singles)} von je {C.TWELFTHS + 1} Rasterpunkten 0; "
                    f"entlang der Familie ist sie an {zero[family]} von {C.TWELFTHS + 1} Rasterpunkten 0 (α = 0 bis 1/3 in Zwölfteln).")


def verdict_bans(tables: dict) -> tuple[str, str]:
    bans = tables["bans"]["bans"]
    by = {0: [Fr(b["cost"]) for b in bans if b["player"] == 0], 1: [Fr(b["cost"]) for b in bans if b["player"] == 1]}
    nb = {b["key"]: Fr(b["cost"]) for b in bans}
    pure = tables["bans"]["pure"]
    return "info", (f"Bluffen ist für den zweiten Spieler nötig und für den ersten ein Freiheitsgrad: das Verbot des Bluffens kostet den zweiten Spieler {frac_dec(nb['s1_no_bluff'])}, den ersten {frac_dec(nb['s0_no_bluff'])} "
                    f"Einsätze je Hand. Von {len(by[1])} Verboten für den zweiten Spieler kosten {sum(1 for c in by[1] if c > 0)} etwas, von {len(by[0])} für den ersten {sum(1 for c in by[0] if c > 0)} "
                    f"(größte Kosten {frac_dec(max(by[1]))} bzw. {frac_dec(max(by[0]))}). Ohne Mischen (nur reine Strategien) kostet es den ersten Spieler {frac_dec(pure['cost_first'])}, den zweiten {frac_dec(pure['cost_second'])}.")


def verdict_family(tables: dict) -> tuple[str, str]:
    fam = tables["family"]
    zero = all(Fr(g["gap0"]) == 0 and Fr(g["gap1"]) == 0 for g in fam["family"])
    return ("success" if zero else "warning"), (f"Exakt gerechnet (Bruch-Simplex auf der Sequenzform) ist die Menge aller Gleichgewichte des Kuhn-Spiels mit drei Karten genau diese Familie: der König setzt 3α "
                                                f"(Bereich der Größe „König − 3·Bube“: {frac(fam['lin_king'][0])} bis {frac(fam['lin_king'][1])}), die Dame geht nach Pass–Setzen um {frac(fam['lin_queen'][0])} "
                                                f"häufiger mit als der Bube setzt, der zweite Spieler ist eindeutig. Die fünf Familienmitglieder α = 0, 1/12, 1/6, 1/4, 1/3 haben Lücke 0 auf beiden Seiten.")


def verdict_size(v: SizeView) -> tuple[str, str]:
    base = f"Bei n = {v.n} Karten hat die Normalform {dots(v.reduced[0])} × {dots(v.reduced[1])} = {dots(v.entries)} Einträge, die Sequenzform {v.sequences} Sequenzen je Spieler."
    if v.value_normal is not None and v.value_exact is not None:
        ok = abs(v.value_normal - float(v.value_exact)) < 1e-9 and abs(v.value_float - float(v.value_exact)) < 1e-9
        return ("success" if ok else "error"), base + f" Spielwert {frac_dec(v.value_exact)} auf drei Wegen (Sequenzform in Brüchen, Sequenzform HiGHS, Normalform HiGHS)" + (": gleich." if ok else ": ABWEICHUNG.")
    if v.value_exact is not None:
        return "info", base + f" Spielwert {frac_dec(v.value_exact)} (Sequenzform in Brüchen und HiGHS); die Normalform wird hier nicht aufgestellt."
    return "info", base + f" Spielwert {de(v.value_float, 4)} (Sequenzform, HiGHS); die Normalform wird hier nicht aufgestellt."


def verdict_runs_live(result: dict, steps: int) -> tuple[str, str]:
    runs = result["runs"]
    last = {k: r["avg"][-1] for k, r in runs.items()}
    best, worst = min(last, key=last.get), max(last, key=last.get)
    return "info", (f"Nach T = {steps} Schritten hat {variant_label(best)} die kleinste Lücke des Mittels ({sci(last[best])}), {variant_label(worst)} die größte ({sci(last[worst])}). "
                    f"Beim vollständigen CFR ist die Lücke der letzten Iteration {sci(runs['cfr']['last'][-1])}, die des Mittels {sci(runs['cfr']['avg'][-1])}; "
                    f"bei CFR⁺ {sci(runs['cfrplus']['last'][-1])} bzw. {sci(runs['cfrplus']['avg'][-1])}.")


def verdict_decomposition(tables: dict) -> tuple[str, str]:
    d = decomposition(tables)
    return "info", (f"Die Steigung kommt von der Abwechslung der Aktualisierung: von {de(d['cfr']['slope'], 2)} (CFR gleichzeitig) auf {de(d['cfr_alt']['slope'], 2)} (abwechselnd). "
                    f"Kappen der Regrets und lineare Mittelung ändern die Konstante um die Faktoren {de(d['cfr_clip']['factor'], 1)} und {de(d['cfrplus']['factor'], 1)} bei T = 1 000 und die Steigung "
                    f"auf {de(d['cfr_clip']['slope'], 2)} bzw. {de(d['cfrplus']['slope'], 2)} (Kuhn, drei Karten, T = 1 000 bis 300 000).")


def verdict_last(tables: dict) -> tuple[str, str]:
    cfr, plus, dcfr = tables["kuhn"]["cfr"], tables["kuhn"]["cfrplus"], tables["kuhn"]["dcfr"]
    return "warning", (f"Das Mittel konvergiert, die letzte Iteration nicht immer: beim vollständigen CFR liegt die Lücke der letzten Iteration an allen Prüfpunkten ab T = 1 000 zwischen "
                       f"{sci(min(v for t, v in zip(cfr['t'], cfr['last']) if t >= 1000))} und {sci(max(cfr['last']))}; bei CFR⁺ ist sie {sci(at(plus, 300000, 'last'))} und bei Discounted CFR "
                       f"{sci(at(dcfr, 300000, 'last'))} bei T = 300 000.")


def verdict_dcfr(tables: dict) -> tuple[str, str]:
    w = dcfr_vs_cfrplus(tables)
    stable = f"durchgehend erst ab T = {fmt_t(w['stable_from'])}" if w["stable_from"] else "nicht durchgehend"
    return "info", (f"Discounted CFR (Parameter aus dem Gedächtnis) liegt im Kuhn-Spiel an {w['dcfr_better']} von {w['points']} Prüfpunkten ab T = 100 unter CFR⁺, {stable}; "
                    f"in Leduc bei T = 1 000: {sci(at(tables['leduc']['dcfr'], 1000))} gegen {sci(at(tables['leduc']['cfrplus'], 1000))}.")


def verdict_start(tables: dict) -> tuple[str, str]:
    plus = seed_mean(tables["start"]["cfrplus"], 10000)
    cfr = seed_mean(tables["start"]["cfr"], 10000)
    return "info", (f"Mit Zufallsstart (vier Zufalls-Seeds, T = 10 000): CFR {sci(cfr['mean'])} ± {sci(cfr['sd'])}, CFR⁺ {sci(plus['mean'])} ± {sci(plus['sd'])}. Der gleichverteilte Start liegt im Kuhn-Spiel nicht im Gleichgewicht, "
                    f"der Fall „Start im Gleichgewicht, Lücke exakt 0“ tritt hier nicht auf.")


def verdict_leduc_table(tables: dict) -> tuple[str, str]:
    lp = tables["leduc_lp"]
    big = max(abs(lp["gap0"]), abs(lp["gap1"]))
    return "info", (f"Leduc (Regeln aus dem Gedächtnis): {lp['infosets']} Informationsmengen und {lp['sequences']} Sequenzen je Spieler, Normalform {sci(lp['reduced'][0])} × {sci(lp['reduced'][1])} reine Strategien; "
                    f"die Sequenzform liefert den Spielwert {de(lp['value0'], 6)} mit Lücken unter {sci(big, 0) if big > 0 else '0'}. Bei T = 2 000 hat CFR⁺ die Lücke {sci(at(tables['leduc']['cfrplus'], 2000))}, "
                    f"CFR {sci(at(tables['leduc']['cfr'], 2000))}; die letzte Iteration von CFR ist {de(at(tables['leduc']['cfr'], 2000, 'last'), 2)}.")


def verdict_sampling(tables: dict) -> tuple[str, str]:
    t = XP.LEDUC_MC_MARKS[-1]
    m = seed_mean(tables["leduc_mc"], t)
    nodes = mean_nodes(tables["leduc_mc"], t)
    hits = {k: at_nodes(tables["leduc"][k], nodes) for k in XP.LEDUC_VARIANTS}
    worse = all(m["mean"] > hits[k][1] for k in hits)
    text = (f"In Leduc mit {fmt_t(round(nodes))} besuchten Knoten ({fmt_t(t)} Iterationen) hat externes Sampling die Lücke {sci(m['mean'])} ± {sci(m['sd'])}, "
            f"vollständiges CFR {sci(hits['cfr'][1])} (T = {fmt_t(hits['cfr'][0])}) und CFR⁺ {sci(hits['cfrplus'][1])} (T = {fmt_t(hits['cfrplus'][0])}) bei vergleichbarem Aufwand. ")
    if worse:
        return "warning", "Gegen die Erwartung (Sampling gilt für große Spiele als Vorteil): " + text + "Auf diesem kleinen Baum ist das Sampling nach Knotenbesuchen schlechter als alle drei vollen Verfahren; bei größeren Bäumen ist es nicht gemessen."
    return "info", text + "Das Sampling ist nicht bei allen vollen Verfahren schlechter."


def verdict_leduc_live(result: dict, steps: int) -> tuple[str, str]:
    runs, sm = result["runs"], result["sampling"]
    return "info", (f"Leduc, Spielwert {de(result['v0'], 6)}: nach T = {steps} Schritten haben CFR {sci(runs['cfr']['avg'][-1])}, CFR⁺ {sci(runs['cfrplus']['avg'][-1])} und Discounted CFR {sci(runs['dcfr']['avg'][-1])} die Lücke des Mittels. "
                    f"Externes Sampling hat nach {fmt_t(sm['t'][-1])} Iterationen ({fmt_t(sm['nodes'][-1])} besuchte Knoten) die Lücke {sci(sm['avg'][-1])}.")


def verdict_anmeldung(cell: dict, s: Settings) -> tuple[str, str]:
    lam, kap, val = Fr(cell["lam"]), Fr(cell["kap"]), Fr(cell["value"])
    if not cell["same"]:
        return "error", "Die geschlossene Form weicht vom linearen Programm ab."
    if cell["regime"] == "ehrlich":
        return "info", (f"Ehrlichkeit lohnt (Gewinn einer unbemerkten riskanten Sendung g = {s.g} nicht über dem Nutzen der ehrlichen Meldung r = {s.r}): niemand lügt, es wird nie kontrolliert, "
                        f"der Wert ist {de(val, 2)} Euro je Sendung. Geschlossene Form, Sequenzform-LP und Normalform sind gleich, Lücken 0.")
    if cell["regime"] == "alle lügen":
        mu = AN.threshold(anmeldung_game_of(s).par)
        return "info", (f"Der Anteil riskanter Sendungen liegt nicht über der Schwelle μ* = {frac(mu)} ({de(mu * 100, 1)} %): eine Kontrolle lohnt nicht, alle riskanten Sendungen melden „sauber“ (λ = 1), "
                        f"der Kontrolleur lässt alles durch, Wert {de(val, 2)} Euro je Sendung. Formel, Sequenzform-LP und Normalform in Brüchen sind gleich, Lücken 0.")
    return "info", (f"Gemischtes Gleichgewicht: {de(lam * 100, 1)} % der riskanten Sendungen melden „sauber“, der Kontrolleur kontrolliert nach „sauber“ mit {de(kap * 100, 1)} %, nach „riskant“ nie; "
                    f"Wert {de(val, 2)} Euro je Sendung. Formel, Sequenzform-LP und Normalform in Brüchen sind gleich, Lücken 0.")


def anmeldung_game_of(s: Settings):
    return SC.anmeldung_game(s)


def verdict_anmeldung_table(tables: dict) -> tuple[str, str]:
    a = tables["anmeldung"]
    grid, extra = a["grid"], a["extra"]
    reg = [c["regime"] for c in grid]
    kap_p = sorted({c["kap"] for c in a["p_rows"]})
    return "info", (f"Im Raster aus {len(grid)} Zellen (Anteil riskanter Sendungen × Strafe) stimmen geschlossene Form, Sequenzform-LP und Normalform in Brüchen in {sum(c['same'] for c in grid)} Zellen überein, Lücken 0; "
                    f"{reg.count('gemischt')} Zellen sind gemischt, {reg.count('alle lügen')} „alle lügen“. In den {len(extra)} Zusatzzeilen (andere c, g, r) stimmen {sum(c['same'] for c in extra)} überein. "
                    f"Der Kontrollanteil ist bei s = 20 für p = 1/10 bis 9/10 immer {', '.join(frac(k) for k in kap_p)}, die Lügenrate ändert sich.")
