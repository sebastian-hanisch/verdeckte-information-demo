"""Vorgerechnete Messreihen (data/tables.json): gehören zum aktuellen Rechencode, sind in sich stimmig, und Proben werden neu gerechnet."""

import json
from fractions import Fraction as F

import pytest

import vdi_constants as C
import vdi_evaluation as V
import vdi_experiments as XP
import vdi_runs as R
import vdi_scenario as SC


@pytest.fixture(scope="module")
def tables():
    t = XP.load_tables()
    assert t is not None, "data/tables.json fehlt oder gehört zu einem anderen Rechencode: python tools/make_grid.py"
    return t


def test_the_file_belongs_to_the_current_generator(tables):
    assert json.loads(XP.TABLES_FILE.read_text(encoding="utf-8"))["generator_hash"] == XP.tables_hash()
    assert tables["seeds"] == list(C.TABLE_SEEDS) == [11, 22, 33, 44] and tables["kuhn_value"] == "-1/18"


def test_a_stale_hash_is_refused(tmp_path, monkeypatch):
    payload = json.loads(XP.TABLES_FILE.read_text(encoding="utf-8"))
    payload["generator_hash"] = "0" * 16
    fake = tmp_path / "tables.json"
    fake.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(XP, "TABLES_FILE", fake)
    assert XP.load_tables() is None


def test_every_job_is_in_the_file(tables):
    assert len(XP.jobs()) == 35
    assert set(tables["kuhn"]) == set(XP.KUHN_VARIANTS) and set(tables["rm"]) == {"rm_nf", "rmplus_nf"}
    assert set(tables["start"]) == {"cfr", "cfrplus", "dcfr"} and all(len(v) == 4 for v in tables["start"].values())
    assert len(tables["kuhn_mc"]) == len(tables["leduc_mc"]) == 4 and set(tables["leduc"]) == set(XP.LEDUC_VARIANTS)


def test_counts_and_formulas_in_the_size_table(tables):
    rows = {r["n"]: r for r in tables["size"]["rows"]}
    for n in range(2, 14):
        r = rows[n]
        assert r["sequences"] == 4 * n + 1 and r["reduced"] == [3 ** n, 4 ** n] and r["entries"] == 12 ** n and r["nodes"] == 1 + 9 * n * (n - 1)
    for n in (20, 30, 50):
        assert rows[n]["sequences"] == 4 * n + 1 and "reduced" not in rows[n]
    exact = {n: F(r["value_exact"]) for n, r in rows.items() if "value_exact" in r}
    assert exact == {2: F(0), 3: F(-1, 18), 4: F(-1, 24), 5: F(-1, 15), 6: F(-11, 180)}
    for n, r in rows.items():
        if "value_exact" in r:
            assert r["value_float"] == pytest.approx(float(F(r["value_exact"])), abs=1e-12) and r["value_normal"] == pytest.approx(float(F(r["value_exact"])), abs=1e-9)


def test_runs_are_monotone_in_nodes_and_their_checkpoints_are_sorted(tables):
    for run in list(tables["kuhn"].values()) + list(tables["rm"].values()) + list(tables["leduc"].values()) + tables["kuhn_mc"] + tables["leduc_mc"]:
        assert run["t"] == sorted(set(run["t"])) and run["nodes"] == sorted(run["nodes"])
        assert all(v >= 0 for v in run["avg"]) and len(run["t"]) == len(run["avg"]) == len(run["nodes"])
    for run in tables["kuhn"].values():
        assert all(v >= 0 for v in run["last"])


def test_the_family_table_is_the_family(tables):
    lin = tables["family"]
    assert lin["lin_king"] == ["0", "0"] and lin["lin_queen"] == ["1/3", "1/3"] and lin["value"] == "-1/18"
    assert all(g["gap0"] == "0" and g["gap1"] == "0" and g["value"] == "-1/18" for g in lin["family"])
    for r in lin["ranges"]["1"]:
        assert r["lo"] == r["hi"]                      # zweiter Spieler: jede Sequenz hat genau einen Wert
    first = {(r["card"], r["hist"], r["action"]): (F(r["lo"]), F(r["hi"])) for r in lin["ranges"]["0"]}
    assert first[(0, "", 1)] == (0, F(1, 3)) and first[(2, "", 1)] == (0, 1) and first[(1, "pb", 1)] == (F(1, 3), F(2, 3)) and first[(1, "", 1)] == (0, 0)


def test_probe_family_and_bans_are_recomputed_identically(tables):
    assert json.loads(json.dumps(XP.job_family())) == tables["family"]
    assert json.loads(json.dumps(XP.job_bans())) == tables["bans"]


def test_probe_exact_value_for_six_cards_is_recomputed():
    T, SF = SC.kuhn_instance(6)
    import vdi_exact as X
    assert X.exact_seq_lp(SF, 0)[0] == F(-11, 180)


def test_probe_variant_run_is_recomputed(tables):
    T, _ = SC.kuhn_instance(3)
    for variant in ("cfrplus", "dcfr", "cfr_alt"):
        run = R.run_variant(T, variant, 3000, -1 / 18, marks=[100, 1000, 3000])
        for t, avg, last in zip(run["t"], run["avg"], run["last"]):
            assert avg == pytest.approx(V.at(tables["kuhn"][variant], t), rel=1e-6)
            assert last == pytest.approx(V.at(tables["kuhn"][variant], t, "last"), rel=1e-6)


def test_probe_sampling_start_and_normal_form_runs_are_recomputed(tables):
    import vdi_cfr as CF
    T, _ = SC.kuhn_instance(3)
    mc = R.run_sampling(T, R.stream(11, 3), 3000, -1 / 18, [1000, 3000])
    assert mc["avg"] == pytest.approx([V.at(tables["kuhn_mc"][0], 1000), V.at(tables["kuhn_mc"][0], 3000)], rel=1e-9)
    init = CF.random_regrets(T, R.stream(22, 7))
    run = R.run_variant(T, "cfrplus", 1000, -1 / 18, marks=[100, 1000], init_regrets=init)
    assert run["avg"] == pytest.approx([V.at(tables["start"]["cfrplus"][1], 100), V.at(tables["start"]["cfrplus"][1], 1000)], rel=1e-6)
    job = XP.job_rm("rmplus_nf")
    assert job["avg"][job["t"].index(1000)] == pytest.approx(V.at(tables["rm"]["rmplus_nf"], 1000), rel=1e-6)


def test_probe_leduc_and_anmeldung_are_recomputed(tables):
    lp = XP.job_leduc_lp()
    assert lp["value0"] == pytest.approx(tables["leduc_lp"]["value0"], abs=1e-12) and lp["nodes"] == 1939 and lp["sequences"] == 337
    T, SF = SC.leduc_instance()
    run = R.run_variant(T, "cfrplus", 100, lp["value0"], marks=[100])
    assert run["avg"][0] == pytest.approx(V.at(tables["leduc"]["cfrplus"], 100), rel=1e-6)
    mc = R.run_sampling(T, R.stream(33, 3), 1000, lp["value0"], [1000])
    assert mc["avg"][0] == pytest.approx(V.at(tables["leduc_mc"][2], 1000), rel=1e-6)
    assert json.loads(json.dumps(XP.job_anmeldung())) == tables["anmeldung"]


def test_rows_and_verdicts_of_the_tables_render(tables):
    for fn in (V.rows_family, V.rows_bans, V.rows_rules, V.rows_size, V.rows_kuhn_runs, V.rows_decomposition, V.rows_last, V.rows_start, V.rows_kuhn_mc, V.rows_leduc, V.rows_leduc_mc,
               V.rows_anmeldung_grid, V.rows_anmeldung_strafe):
        rows = fn(tables)
        assert rows and all(isinstance(r, dict) and r for r in rows), fn.__name__
    for fn in (V.verdict_family, V.verdict_bans, V.verdict_decomposition, V.verdict_last, V.verdict_dcfr, V.verdict_start, V.verdict_leduc_table, V.verdict_sampling, V.verdict_anmeldung_table):
        kind, text = fn(tables)
        assert kind in ("info", "success", "warning") and text, fn.__name__
