"""Vorgerechnete Messreihen (data/tables.json) mit Erzeuger-Hash.

Aufträge sind einzeln und in beliebiger Reihenfolge berechenbar; `tools/make_grid.py` verteilt sie auf Prozesse (höchstens sechs) und setzt die Datei zusammen.
Zufall nur über SplitMix64-Ströme je (Zufalls-Seed, Zelle). Ändert sich eine Quelldatei aus TABLE_SOURCES, stimmt der Hash nicht mehr: die App zeigt die Reihen dann nicht,
`tests/test_measurements.py` schlägt an. Zeiten (Sekunden) sind einmalige Messungen auf der Maschine des Aufrufs, plattformabhängig und nie Teil eines Tests."""

import hashlib
import json
import time
from fractions import Fraction as Fr
from pathlib import Path

import numpy as np

import vdi_anmeldung as AN
import vdi_cfr as CF
import vdi_constants as C
import vdi_exact as X
import vdi_games as G
import vdi_kuhn as K
import vdi_normal as N
import vdi_runs as R
import vdi_seqform as SQ
import vdi_strategy as S
import vdi_tree as TR

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TABLES_FILE = DATA / "tables.json"
TABLE_SOURCES = ("vdi_games.py", "vdi_tree.py", "vdi_strategy.py", "vdi_seqform.py", "vdi_exact.py", "vdi_normal.py", "vdi_cfr.py", "vdi_runs.py", "vdi_kuhn.py", "vdi_anmeldung.py",
                 "vdi_rng.py", "vdi_experiments.py")

KUHN_STEPS = 300_000
KUHN_VARIANTS = tuple(CF.VARIANTS)
RM_STEPS = 30_000
START_STEPS = 10_000
START_MARKS = (100, 1000, 10000)
KUHN_MC_STEPS = 100_000
KUHN_MC_MARKS = (100, 300, 1000, 3000, 10000, 30000, 100000)
LEDUC_STEPS = 2000
LEDUC_VARIANTS = ("cfr", "cfrplus", "dcfr")
LEDUC_MC_STEPS = 100_000
LEDUC_MC_MARKS = (100, 300, 1000, 3000, 10000, 30000, 100000)
SIZE_EXACT = (2, 3, 4, 5, 6)
SIZE_NS = tuple(range(2, 14))
SIZE_FLOAT_ONLY = (20, 30, 50)
ANM_P = (Fr(1, 50), Fr(1, 20), Fr(1, 10), Fr(3, 10), Fr(1, 2), Fr(9, 10))
ANM_S = (5, 10, 20, 40, 80)
ANM_EXTRA = ((2, 15, 6), (2, 6, 6), (2, 5, 6), (5, 15, 6), (0, 15, 6), (2, 15, 14), (2, 15, 15))     # (c, g, r)
ANM_STRAFEN = (5, 10, 20, 40, 80, 160)
ANM_PRUEF_P = (Fr(1, 10), Fr(3, 10), Fr(1, 2), Fr(7, 10), Fr(9, 10))


def tables_hash() -> str:
    h = hashlib.sha256()
    for name in TABLE_SOURCES:
        text = (ROOT / name).read_text(encoding="utf-8").replace("\r\n", "\n")
        h.update(name.encode() + b"\0" + text.encode("utf-8") + b"\0")
    return h.hexdigest()[:16]


def load_tables():
    """Die vorgerechneten Reihen, oder None, wenn die Datei fehlt oder zu einem anderen Rechencode gehört."""
    if not TABLES_FILE.exists():
        return None
    try:
        payload = json.loads(TABLES_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if payload.get("generator_hash") == tables_hash() else None


def write_json(path: Path, payload: dict):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def fs(x) -> str:
    """Bruch als Text „a/b“ (ganze Zahlen ohne Nenner)."""
    return str(Fr(x))


# --- Aufträge --------------------------------------------------------------------------------------------------------------------------------------
def jobs() -> list[tuple]:
    out = [("family",), ("bans",), ("size",), ("leduc_lp",), ("anmeldung",)]
    out += [("kuhn", v) for v in KUHN_VARIANTS]
    out += [("rm", v) for v in ("rm_nf", "rmplus_nf")]
    out += [("start", v, seed) for v in ("cfr", "cfrplus", "dcfr") for seed in C.TABLE_SEEDS]
    out += [("kuhn_mc", seed) for seed in C.TABLE_SEEDS]
    out += [("leduc_full", v) for v in LEDUC_VARIANTS]
    out += [("leduc_mc", seed) for seed in C.TABLE_SEEDS]
    return out


def run_job(job: tuple):
    return job, JOB_FUNCS[job[0]](*job[1:])


def job_family() -> dict:
    """Gleichgewichtsmenge des Kuhn-Spiels mit drei Karten, exakt: Bereich jeder Sequenz beider Spieler und die beiden Linearkombinationen."""
    T, SF = _kuhn(3)
    v = Fr(-1, 18)
    ranges = K.equilibrium_ranges(T, SF, v)
    jb, kb, qc = K.seq_index(T, SF, 0, 0, "", 1), K.seq_index(T, SF, 0, 2, "", 1), K.seq_index(T, SF, 0, 1, "pb", 1)
    lin_k = X.exact_linear_range(SF, 0, v, {kb: 1, jb: -3})
    lin_q = X.exact_linear_range(SF, 0, v, {qc: 1, jb: -1})
    rows = {p: [{"card": r["card"], "hist": r["hist"], "action": r["action"], "lo": fs(r["lo"]), "hi": fs(r["hi"])} for r in ranges[p]] for p in (0, 1)}
    alphas = [Fr(0), Fr(1, 12), Fr(1, 6), Fr(1, 4), Fr(1, 3)]
    gaps = []
    for a in alphas:
        g = S.exploitability(T, K.family_profile(T, a), v)
        gaps.append({"alpha": fs(a), "value": fs(S.profile_value(T, K.family_profile(T, a))), "gap0": fs(g[0]), "gap1": fs(g[1])})
    return {"value": fs(v), "ranges": {"0": rows[0], "1": rows[1]}, "lin_king": [fs(lin_k[0]), fs(lin_k[1])], "lin_queen": [fs(lin_q[0]), fs(lin_q[1])], "family": gaps}


def job_bans() -> dict:
    """Verbote (garantierter Wert und Kosten), Faustregeln und der Verzicht auf Zufall, alles exakt im Kuhn-Spiel mit drei Karten."""
    T, SF = _kuhn(3)
    v = Fr(-1, 18)
    bans = []
    for case in K.BAN_CASES:
        guaranteed, cost = K.ban_cost(T, SF, case, v)
        bans.append({"key": case[0], "player": case[1], "text": case[2], "guaranteed": fs(guaranteed), "cost": fs(cost)})
    rules = []
    for rule in K.RULES_OF_THUMB:
        first, second = K.rule_cost(T, rule, v)
        rules.append({"name": rule[0], "cost_first": fs(first), "cost_second": fs(second)})
    M = N.normal_matrix_exact(SF, N.reduced_plans(T, SF, 0), N.reduced_plans(T, SF, 1))
    pure0, pure1 = K.best_pure_guarantee(M, 0), K.best_pure_guarantee(M, 1)
    return {"bans": bans, "rules": rules, "pure": {"first": fs(pure0), "second": fs(pure1), "cost_first": fs(v - pure0), "cost_second": fs(-v - pure1)}}


def job_size() -> dict:
    SQ.solve_lp(_kuhn(2)[1], 0)          # Anlaufkosten von scipy aus der Zeitmessung nehmen
    rows = []
    for n in SIZE_NS + SIZE_FLOAT_ONLY:
        t0 = time.perf_counter()
        T, SF = TR.build(G.Kuhn(n)), None
        SF = SQ.SeqForm(T)
        t_build = time.perf_counter() - t0
        t0 = time.perf_counter()
        v_float = SQ.solve_lp(SF, 0)[0]
        t_seq = time.perf_counter() - t0
        row = {"n": n, "nodes": T.n, "infosets": T.ninfo[0], "sequences": SF.n[0], "t_build": t_build, "t_seq": t_seq, "value_float": v_float}
        if n <= 13:
            row["reduced"] = [N.reduced_count(T, SF, 0), N.reduced_count(T, SF, 1)]
            row["entries"] = row["reduced"][0] * row["reduced"][1]
        if n in SIZE_EXACT:
            t0 = time.perf_counter()
            row["value_exact"] = fs(X.exact_seq_lp(SF, 0)[0])
            row["t_exact"] = time.perf_counter() - t0
            t0 = time.perf_counter()
            M, P0, P1 = N.normal_matrix(T, SF)
            v_nf = N.matrix_game(M)[0]
            row["t_normal"] = time.perf_counter() - t0
            row["value_normal"] = v_nf
        rows.append(row)
    return {"rows": rows}


def job_kuhn(variant: str) -> dict:
    T, _ = _kuhn(3)
    return R.run_variant(T, variant, KUHN_STEPS, -1 / 18)


def job_rm(variant: str) -> dict:
    T, SF = _kuhn(3)
    M, _, _ = N.normal_matrix(T, SF)
    marks = R.checkpoints(RM_STEPS)
    res = N.regret_matching_normal(M, -1 / 18, RM_STEPS, marks, plus=(variant == "rmplus_nf"))
    nodes_per_step = 2 * M.shape[0] * M.shape[1]
    return {"t": [r[0] for r in res], "avg": [r[1] for r in res], "avg_sum": [r[2] for r in res], "nodes": [r[0] * nodes_per_step for r in res]}


def job_start(variant: str, seed: int) -> dict:
    T, _ = _kuhn(3)
    init = CF.random_regrets(T, R.stream(seed, 7))
    run = R.run_variant(T, variant, START_STEPS, -1 / 18, marks=START_MARKS, init_regrets=init)
    return {"t": run["t"], "avg": run["avg"]}


def job_kuhn_mc(seed: int) -> dict:
    T, _ = _kuhn(3)
    return R.run_sampling(T, R.stream(seed, 3), KUHN_MC_STEPS, -1 / 18, KUHN_MC_MARKS)


def job_leduc_lp() -> dict:
    T, SF = _leduc()
    t0 = time.perf_counter()
    v0, x0 = SQ.solve_lp(SF, 0)
    v1, x1 = SQ.solve_lp(SF, 1)
    t_lp = time.perf_counter() - t0
    st = [SQ.realization_to_behavior(SF, x0, 0), SQ.realization_to_behavior(SF, x1, 1)]
    g0, g1, total = S.exploitability(T, st, v0)
    return {"nodes": T.n, "terminals": T.nterm, "infosets": T.ninfo[0], "sequences": SF.n[0], "reduced": [N.reduced_count(T, SF, 0), N.reduced_count(T, SF, 1)],
            "value0": v0, "value1": v1, "gap0": g0, "gap1": g1, "t_lp": t_lp}


def job_leduc_full(variant: str) -> dict:
    T, SF = _leduc()
    v0 = SQ.solve_lp(SF, 0)[0]
    t0 = time.perf_counter()
    run = R.run_variant(T, variant, LEDUC_STEPS, v0)
    run["seconds"] = time.perf_counter() - t0
    run["nodes_per_step"] = T.n * (1 if variant == "cfr" else 2)
    return run


def job_leduc_mc(seed: int) -> dict:
    T, SF = _leduc()
    v0 = SQ.solve_lp(SF, 0)[0]
    t0 = time.perf_counter()
    run = R.run_sampling(T, R.stream(seed, 3), LEDUC_MC_STEPS, v0, LEDUC_MC_MARKS)
    run["seconds"] = time.perf_counter() - t0
    return run


def anmeldung_cell(p, s=20, c=2, g=15, r=6, b=10, f=1) -> dict:
    """Eine Zelle von Reiter 4: geschlossene Form, Sequenzform-LP (exakt), Normalform (exakt), Lücken des Profils; alles als Text-Brüche."""
    game = G.Anmeldung(b=b, c=c, f=f, g=g, s=s, r=r, p=p)
    T = TR.build(game)
    SF = SQ.SeqForm(T)
    lam, kap, value, regime = AN.closed_form(game.par)
    v_seq = X.exact_seq_lp(SF, 0)[0]
    v_nf = X.matrix_game_exact(N.normal_matrix_exact(SF, N.reduced_plans(T, SF, 0), N.reduced_plans(T, SF, 1)))[0]
    st = AN.equilibrium_profile(T, lam, kap)
    g0, g1, _ = S.exploitability(T, st, value)
    return {"p": fs(p), "s": s, "c": c, "g": g, "r": r, "regime": regime, "lam": fs(lam), "kap": fs(kap), "value": fs(value), "value_seq": fs(v_seq), "value_nf": fs(v_nf),
            "gap0": fs(g0), "gap1": fs(g1), "same": bool(v_seq == value == v_nf and g0 == 0 and g1 == 0),
            "lying_share": fs(AN.lying_share(game.par, lam)), "controls": fs(AN.expected_controls(game.par, lam, kap))}


def job_anmeldung() -> dict:
    grid = [anmeldung_cell(p, s=s) for p in ANM_P for s in ANM_S]
    extra = [anmeldung_cell(Fr(3, 10), c=c, g=g, r=r) for c, g, r in ANM_EXTRA]
    strafen = [anmeldung_cell(Fr(3, 10), s=s) for s in ANM_STRAFEN]
    p_rows = [anmeldung_cell(p) for p in ANM_PRUEF_P]
    fees = [fs(X.exact_seq_lp(SQ.SeqForm(TR.build(G.Anmeldung(f=f))), 0)[0]) for f in (0, 1, 3, 5)]
    return {"grid": grid, "extra": extra, "strafen": strafen, "p_rows": p_rows, "fee_values": fees}


# --- Hilfen (je Prozess einmal gebaut) ----------------------------------------------------------------------------------------------------------------
_CACHE: dict = {}


def _kuhn(n: int):
    if ("kuhn", n) not in _CACHE:
        T = TR.build(G.Kuhn(n))
        _CACHE[("kuhn", n)] = (T, SQ.SeqForm(T))
    return _CACHE[("kuhn", n)]


def _leduc():
    if "leduc" not in _CACHE:
        T = TR.build(G.Leduc())
        _CACHE["leduc"] = (T, SQ.SeqForm(T))
    return _CACHE["leduc"]


JOB_FUNCS = {"family": job_family, "bans": job_bans, "size": job_size, "kuhn": job_kuhn, "rm": job_rm, "start": job_start, "kuhn_mc": job_kuhn_mc, "leduc_lp": job_leduc_lp,
             "leduc_full": job_leduc_full, "leduc_mc": job_leduc_mc, "anmeldung": job_anmeldung}


def assemble_payload(results: dict) -> dict:
    """Setzt die Ergebnisse aller Aufträge zur Datei zusammen (Schlüssel = Auftrag als Text), mit Erzeuger-Hash und Seeds."""
    def get(*job):
        return results[job]

    payload = {
        "generator_hash": tables_hash(), "seeds": list(C.TABLE_SEEDS), "kuhn_value": "-1/18",
        "family": get("family"), "bans": get("bans"), "size": get("size"), "anmeldung": get("anmeldung"), "leduc_lp": get("leduc_lp"),
        "kuhn": {v: get("kuhn", v) for v in KUHN_VARIANTS},
        "rm": {v: get("rm", v) for v in ("rm_nf", "rmplus_nf")},
        "start": {v: [get("start", v, seed) for seed in C.TABLE_SEEDS] for v in ("cfr", "cfrplus", "dcfr")},
        "kuhn_mc": [get("kuhn_mc", seed) for seed in C.TABLE_SEEDS],
        "leduc": {v: get("leduc_full", v) for v in LEDUC_VARIANTS},
        "leduc_mc": [get("leduc_mc", seed) for seed in C.TABLE_SEEDS],
    }
    return json.loads(json.dumps(payload, default=_json_default))


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, Fr):
        return fs(o)
    raise TypeError(type(o))
