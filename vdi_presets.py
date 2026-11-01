"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import random
from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

import vdi_constants as C
from vdi_scenario import Settings


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: float | None = None
    hi: float | None = None
    choices: tuple | None = None      # bei Auswahlreglern: die erlaubten Werte


T = C.TWELFTHS
SETTING_SPECS = {
    "jbet_slider": SettingSpec("jb", int, C.STRAT_DEFAULT["jbet"], 0, T),
    "kbet_slider": SettingSpec("kb", int, C.STRAT_DEFAULT["kbet"], 0, T),
    "qcall_slider": SettingSpec("qc", int, C.STRAT_DEFAULT["qcall"], 0, T),
    "bluff_slider": SettingSpec("bl", int, C.STRAT_DEFAULT["bluff"], 0, T),
    "call_slider": SettingSpec("ca", int, C.STRAT_DEFAULT["call"], 0, T),
    "n_slider": SettingSpec("n", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "n3_slider": SettingSpec("n3", int, C.DEFAULT_N3, C.N3_MIN, C.N3_MAX),
    "steps_slider": SettingSpec("t", int, C.DEFAULT_STEPS, C.STEPS_MIN, C.STEPS_MAX),
    "start_select": SettingSpec("start", str, C.DEFAULT_START, choices=tuple(C.START_CHOICES)),
    "leduc_slider": SettingSpec("lt", int, C.DEFAULT_LEDUC, C.LEDUC_MIN, C.LEDUC_MAX),
    "mc_slider": SettingSpec("mc", int, C.DEFAULT_MC, C.MC_MIN, C.MC_MAX),
    "b_slider": SettingSpec("ab", int, C.DEFAULT_A_B, C.A_B_MIN, C.A_B_MAX),
    "c_slider": SettingSpec("ac", int, C.DEFAULT_A_C, C.A_C_MIN, C.A_C_MAX),
    "g_slider": SettingSpec("ag", int, C.DEFAULT_A_G, C.A_G_MIN, C.A_G_MAX),
    "s_slider": SettingSpec("as", int, C.DEFAULT_A_S, C.A_S_MIN, C.A_S_MAX),
    "r_slider": SettingSpec("ar", int, C.DEFAULT_A_R, C.A_R_MIN, C.A_R_MAX),
    "p_slider": SettingSpec("ap", int, C.DEFAULT_A_P, C.A_P_MIN, C.A_P_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"jbet": "jbet_slider", "kbet": "kbet_slider", "qcall": "qcall_slider", "bluff": "bluff_slider", "call": "call_slider", "n": "n_slider", "n3": "n3_slider",
               "steps": "steps_slider", "start": "start_select", "lsteps": "leduc_slider", "mc": "mc_slider", "b": "b_slider", "c": "c_slider", "g": "g_slider", "s": "s_slider",
               "r": "r_slider", "p": "p_slider", "seed": "seed_input"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt bzw. auf erlaubte Werte geprüft."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            if spec.choices is not None:
                if value not in spec.choices:
                    continue
            else:
                if value != value:      # NaN
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
            st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    """Alle Regler setzen: was das Preset nicht nennt, bekommt den Standardwert (so ist das Preset danach genau das aktive)."""
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name].get(key, SETTING_SPECS[state_key].default)


def settings_from_state() -> Settings:
    """Die Einstellungen aus dem Session State (vor dem Zeichnen der Regler gesetzt durch Voreinstellung, Permalink oder Standard)."""
    g = st.session_state.get
    d = {k: g(k, SETTING_SPECS[k].default) for k in SETTING_SPECS}
    return Settings(jbet=int(d["jbet_slider"]), kbet=int(d["kbet_slider"]), qcall=int(d["qcall_slider"]), bluff=int(d["bluff_slider"]), call=int(d["call_slider"]),
                    n=int(d["n_slider"]), n3=int(d["n3_slider"]), steps=int(d["steps_slider"]), start=str(d["start_select"]), lsteps=int(d["leduc_slider"]), mc=int(d["mc_slider"]),
                    b=int(d["b_slider"]), c=int(d["c_slider"]), g=int(d["g_slider"]), s=int(d["s_slider"]), r=int(d["r_slider"]), p=int(d["p_slider"]), seed=int(d["seed_input"]))


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
