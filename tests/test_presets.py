"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und jede Zahl der Preset-Hilfen (DEMO-PLAYBOOK §8) steht hier als Messung."""

from fractions import Fraction as F

import vdi_anmeldung as AN
import vdi_constants as C
import vdi_evaluation as V
import vdi_presets as P
import vdi_scenario as SC
from conftest import kuhn_instance
from vdi_scenario import Settings

DEFAULT_PRESET = "Kuhn Gleichgewicht (α = 1/6)"


def _settings(name) -> Settings:
    return Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_only_known_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_or_choices():
    for name, preset in C.PRESETS.items():
        for key, value in preset.items():
            spec = P.SETTING_SPECS[P.PRESET_KEYS[key]]
            if spec.choices:
                assert value in spec.choices, (name, key)
            else:
                assert spec.lo <= value <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    assert C.PRESETS[DEFAULT_PRESET] == {}
    assert _settings(DEFAULT_PRESET) == Settings()


def test_setting_specs_cover_every_preset_key_and_every_default_is_in_range():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for key, spec in P.SETTING_SPECS.items():
        assert (spec.default in spec.choices) if spec.choices else (spec.lo <= spec.default <= spec.hi), key


def test_presets_differ_from_each_other():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


def test_preset_help_numbers_for_the_kuhn_presets():
    """Gleichgewicht α = 1/6: Lücke 0. α = 0: Gleichgewicht, Lücke 0. Zweiter Spieler bluft nie: Lücke des zweiten Spielers 1/9."""
    eq = V.strategy_view(_settings(DEFAULT_PRESET))
    assert (eq.loss_first, eq.loss_second, eq.in_family, eq.alpha) == (0, 0, True, F(1, 6))
    zero = V.strategy_view(_settings("Erster Spieler bluft nie (α = 0)"))
    assert (zero.loss_first, zero.loss_second, zero.in_family, zero.alpha) == (0, 0, True, 0)
    nb = V.strategy_view(_settings("Zweiter Spieler bluft nie"))
    assert (nb.loss_first, nb.loss_second) == (0, F(1, 9))
    assert "1/9" in C.PRESET_HELP["Zweiter Spieler bluft nie"]


def test_preset_help_numbers_for_sizes():
    """n = 2: Spielwert 0, jede Informationsmenge hat einen Knoten. n = 5: 243 × 1 024 und 21 Sequenzen. n = 13: 1 594 323 × 67 108 864 und 53 Sequenzen."""
    two = V.size_view(2)
    assert two.value_exact == 0
    five, thirteen = V.size_view(5), V.size_view(13)
    assert five.reduced == (243, 1024) and five.sequences == 21
    assert thirteen.reduced == (1594323, 67108864) and thirteen.sequences == 53 and thirteen.value_exact is None
    help5, help13 = C.PRESET_HELP["Sequenzform gegen Normalform (n = 5)"], C.PRESET_HELP["Viele Karten (n = 13)"]
    assert "243 × 1 024" in help5 and "21 Sequenzen" in help5
    assert "1 594 323 × 67 108 864" in help13 and "53 Sequenzen" in help13


def test_preset_help_numbers_for_two_cards():
    T, _ = kuhn_instance(2)
    assert all(len(nodes) == 1 for p in (0, 1) for nodes in T.inodes[p])           # jede Informationsmenge hat nur einen Knoten
    kuhn3, _ = kuhn_instance(3)
    assert all(len(nodes) == 2 for p in (0, 1) for nodes in kuhn3.inodes[p])        # bei drei Karten sind es zwei


def test_preset_help_numbers_for_anmeldung():
    """p = 5 % liegt unter μ* = 2/37 (5,4 %): alle lügen. g = 5 ≤ r = 6: ehrlich. Strafe 160 statt 20: λ und κ sind kleiner."""
    base = Settings()
    assert AN.closed_form(SC.anmeldung_game(Settings(p=5)).par)[3] == "alle lügen"
    assert AN.closed_form(SC.anmeldung_game(Settings(g=5)).par)[3] == "ehrlich"
    lam0, kap0, _, _ = AN.closed_form(SC.anmeldung_game(base).par)
    lam1, kap1, _, _ = AN.closed_form(SC.anmeldung_game(Settings(s=160)).par)
    assert lam1 < lam0 and kap1 < kap0
    assert F(5, 100) < AN.threshold(SC.anmeldung_game(base).par) < F(6, 100)
    for name in ("Anmeldung: hohe Strafe (s = 160)", "Anmeldung: alle lügen (p = 5 %)", "Anmeldung: Ehrlichkeit lohnt (g = 5)"):
        assert _settings(name).s == (160 if "160" in name else 20)


def test_leduc_preset_help_names_the_steps():
    assert _settings("Leduc (600 Schritte)").lsteps == 600 and "600" in C.PRESET_HELP["Leduc (600 Schritte)"]
    assert _settings("CFR gegen CFR⁺ (3 000 Schritte)").steps == 3000
    assert _settings("Zufallsstart").start == "zufall"


def test_n3_never_exceeds_the_tree_limit_and_normal_form_limits_are_consistent():
    assert C.N3_MAX <= C.N_MAX and C.N3_NORMAL_MAX <= C.N3_MAX - 1 and C.N_EXACT_MAX <= C.N_NORMAL_MAX
