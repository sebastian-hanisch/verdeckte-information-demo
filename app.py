"""Verdeckte Information: Wie spielt man, wenn man den Zustand des anderen nicht sieht und die Züge nacheinander kommen? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück der Linie „Regeln setzen, verhandeln, kontrollieren“. Lehrspiel Kuhn-Poker (Informationsmengen, Gleichgewichtsfamilie, Kosten von Verboten), Sequenzform gegen Normalform (exakt in Brüchen),
Regret-Verfahren auf dem Baum (CFR, CFR⁺, Discounted CFR, Sampling) in Kuhn und Leduc und das konstruierte Nullsummenmodell „Anmeldung und Kontrolle“.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import vdi_constants as C
import vdi_evaluation as V
import vdi_experiments as XP
import vdi_scenario as SC
import vdi_texts as T
import vdi_visualization as Z
from vdi_layout import dunkles_design, kopf_css
from vdi_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    settings_from_state,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Verdeckte Information – Sebastian Hanisch", layout="wide")


# --- Zwischenspeicher (Schlüssel = alle Eingaben inklusive Zufalls-Seed) --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _tables():
    return XP.load_tables()


@st.cache_data(show_spinner=False)
def _strategy(settings):
    return V.strategy_view(settings)


@st.cache_data(show_spinner=False)
def _curves():
    return V.loss_curves()


@st.cache_data(show_spinner=False)
def _size(n):
    return V.size_view(n)


@st.cache_data(show_spinner=False)
def _kuhn_runs(n, steps, start, seed):
    return V.kuhn_runs(n, steps, start, seed)


@st.cache_data(show_spinner=False)
def _anmeldung(settings):
    return V.anmeldung_view(settings)


@st.cache_data(show_spinner=False)
def _anm_curves(settings, axis):
    return V.anmeldung_curves(settings, axis)


def show(verdict):
    kind, text = verdict
    getattr(st, kind)(text)


def table(rows):
    st.dataframe(rows, hide_index=True, width="stretch")


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in vdi_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🃏 Verdeckte Information: Spiele, in denen man den Zustand des anderen nicht sieht")
st.markdown(T.INTRO)

with st.expander("So funktioniert ein Spiel mit verdeckter Information", expanded=True):
    st.markdown(T.EXPLAINER)

with st.expander("Erklärtabelle: Begriffe und Regler"):
    st.markdown(T.CONTROLS_TABLE)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("🃏 Strategie (Reiter 1)")
    st.caption("Kuhn-Poker mit drei Karten. Werte in Zwölfteln: 4 heißt 4/12 = 1/3. Alle übrigen Entscheidungen sind wie in der Gleichgewichtsfamilie fest.")
    st.slider("Erster Spieler: Bube setzt (Zwölftel)", *bounds("jbet_slider"), key="jbet_slider", step=1, help="Wahrscheinlichkeit, mit dem Buben im ersten Zug zu setzen (bluffen). In der Familie ist sie α und liegt zwischen 0 und 4/12.")
    st.slider("Erster Spieler: König setzt (Zwölftel)", *bounds("kbet_slider"), key="kbet_slider", step=1, help="Wahrscheinlichkeit, mit dem König im ersten Zug zu setzen. In der Familie ist sie 3α.")
    st.slider("Erster Spieler: Dame geht nach Pass–Setzen mit (Zwölftel)", *bounds("qcall_slider"), key="qcall_slider", step=1,
              help="Wahrscheinlichkeit, mit der Dame mitzugehen, wenn der erste Spieler gepasst und der zweite gesetzt hat. In der Familie ist sie α + 1/3.")
    st.slider("Zweiter Spieler: Bube setzt nach Pass (Zwölftel)", *bounds("bluff_slider"), key="bluff_slider", step=1, help="Der Bluff des zweiten Spielers. Im Gleichgewicht ist er eindeutig 4/12 = 1/3.")
    st.slider("Zweiter Spieler: Dame geht gegen Setzen mit (Zwölftel)", *bounds("call_slider"), key="call_slider", step=1, help="Im Gleichgewicht eindeutig 4/12 = 1/3.")
    st.header("📏 Größe (Reiter 2)")
    st.slider("Karten n im Kuhn-Spiel", *bounds("n_slider"), key="n_slider", step=1, help="Zahl der Karten. Die Normalform wird nur bis n = 5 aufgestellt, der exakte Wert in Brüchen nur bis n = 5 gerechnet; die Sequenzform läuft bis n = 13.")
    st.header("🔁 Regret-Verfahren (Reiter 3)")
    st.slider("Karten im Kuhn-Spiel (Verfahren)", *bounds("n3_slider"), key="n3_slider", step=1, help="Kartenzahl für den Vergleich der Verfahren. Regret Matching auf der Normalform läuft bis 5 Karten.")
    st.slider("Schritte T (Kuhn)", *bounds("steps_slider"), key="steps_slider", step=100, help="Durchläufe jedes Verfahrens im Kuhn-Spiel.")
    st.selectbox("Start der Baumverfahren", list(C.START_CHOICES), key="start_select", format_func=C.START_CHOICES.get,
                 help="Gleichverteilter Start oder zufällige Anfangsregrets (Zufalls-Seed unten). Regret Matching auf der Normalform startet immer gleichverteilt.")
    st.slider("Schritte T (Leduc, auf Knopfdruck)", *bounds("leduc_slider"), key="leduc_slider", step=100, help="Durchläufe der drei vollen Verfahren in Leduc. Ein Schritt dauert Millisekunden; 1 000 Schritte einige Sekunden je Verfahren.")
    st.slider("Iterationen Sampling (Leduc, auf Knopfdruck)", *bounds("mc_slider"), key="mc_slider", step=1000, help="Iterationen des externen Samplings in Leduc.")
    st.header("📦 Anmeldung und Kontrolle (Reiter 4)")
    st.slider("Wert einer Sendung in Ordnung b (Euro)", *bounds("b_slider"), key="b_slider", step=1, help="Nutzen des Verladers, wenn die Sendung in Ordnung ist.")
    st.slider("Entschädigung bei Kontrolle c (Euro)", *bounds("c_slider"), key="c_slider", step=1,
              help="Der Kontrolleur entschädigt den Verlader für eine unbegründete Verzögerung. Konstruktion, die das Spiel zur Nullsumme macht.")
    st.slider("Gewinn einer unbemerkten riskanten Sendung g (Euro)", *bounds("g_slider"), key="g_slider", step=1, help="Was der Verlader bekommt, wenn eine riskante, als sauber gemeldete Sendung durchgelassen wird.")
    st.slider("Strafe s (Euro)", *bounds("s_slider"), key="s_slider", step=5, help="Was der Verlader zahlt, wenn eine riskante, als sauber gemeldete Sendung kontrolliert wird.")
    st.slider("Nutzen der ehrlichen Meldung r (Euro)", *bounds("r_slider"), key="r_slider", step=1, help="Was der Verlader bekommt, wenn er eine riskante Sendung als riskant meldet (ohne Kontrolle).")
    st.slider("Anteil riskanter Sendungen p (%)", *bounds("p_slider"), key="p_slider", step=1, help="Wahrscheinlichkeit, dass eine Sendung riskant ist; der Verlader weiß es, der Kontrolleur nicht.")
    st.header("🎲 Zufall")
    st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1, help="Legt den Zufallsstart (Reiter 3) und das externe Sampling in Leduc fest.")
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=randomize_seed)

settings = settings_from_state()
sync_query_params({k: st.session_state[k] for k in SETTING_SPECS})

verdicts = []      # Verdikte für den PDF-Export
tables = _tables()
if tables is None:
    st.warning("Die vorgerechneten Messreihen (data/tables.json) fehlen oder gehören zu einem anderen Rechencode: `python tools/make_grid.py` ausführen. Die Reiter zeigen dann keine Reihen.")

view = _strategy(settings)

# --- Hauptansicht --------------------------------------------------------------------------------------------------------------------------------
st.markdown("## 🎯 Ergebnis: Wie ausnutzbar ist die gewählte Strategie im Kuhn-Poker?")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Spielwert (Gleichgewicht)", V.frac(V.KUHN_VALUE), help=f"Erwartete Auszahlung an den ersten Spieler im Gleichgewicht, Einsätze je Hand (drei Karten, exakt gerechnet): {V.de(V.KUHN_VALUE, 4)}.")
m2.metric("Wert des Profils", V.frac(view.value), help=f"Erwartete Auszahlung an den ersten Spieler, wenn beide Seiten die gewählten Strategien spielen: {V.de(view.value, 4)} Einsätze je Hand.")
m3.metric("Lücke erster Spieler", V.frac(view.loss_first), help=f"Was die beste Antwort des zweiten Spielers gegen die gewählte Strategie des ersten über den Gleichgewichtswert hinaus gewinnt: {V.de(view.loss_first, 4)} Einsätze je Hand.")
m4.metric("Lücke zweiter Spieler", V.frac(view.loss_second), help=f"Was die beste Antwort des ersten Spielers gegen die gewählte Strategie des zweiten über den Gleichgewichtswert hinaus gewinnt: {V.de(view.loss_second, 4)} Einsätze je Hand.")
m5.metric("In der Familie", "ja" if view.in_family else "nein", help="Ob die fünf gewählten Entscheidungen zur Familie aller Gleichgewichte gehören (α, 3α, α + 1/3, 1/3, 1/3).")
st.plotly_chart(Z.build_strategy(view), width="stretch", key="strategy_chart")
st.caption("Wahrscheinlichkeit der zweiten Aktion (Setzen bzw. Mitgehen) in jeder Informationsmenge: blau der erste Spieler, orange der zweite. Die fest vorgegebenen Entscheidungen (zum Beispiel: Dame setzt im ersten Zug nie) sind in der Gleichgewichtsfamilie so.")
with st.expander("Zahlen im Einzelnen: Strategie je Informationsmenge"):
    table([{"Spieler": "erster" if r["player"] == 0 else "zweiter", "Karte": T_card, "Lage": V.situation_name(r["player"], r["hist"]), "Handlung": V.action_name(r["player"], r["hist"]),
            "Wahrscheinlichkeit": V.frac(r["prob"])} for r in view.rows for T_card in [V.G.card_names(3)[r["card"]]]])
st.markdown("#### ❓ Kernfrage: Wie spielt man, wenn man den Zustand des anderen nicht sieht?")
v_main = V.verdict_main(view)
show(v_main)
verdicts.append(v_main)

# --- Reiter --------------------------------------------------------------------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["1 Spielbaum und Gleichgewichtsfamilie", "2 Sequenzform gegen Normalform", "3 Regret-Verfahren", "4 Anmeldung und Kontrolle"])

# --- Reiter 1 ------------------------------------------------------------------------------------------------------------------------------------
with tab1:
    st.subheader("🔬 Experiment E1: Wie nötig ist das Bluffen, und was kostet ein Verbot?")
    st.caption("**Erwartung:** Das Kuhn-Spiel hat nicht ein Gleichgewicht, sondern eine Familie. Weicht ein Spieler von seiner Gleichgewichtsstrategie ab, kann der Gegner das mit der besten Antwort ausnutzen; "
               "ob ein Verbot (zum Beispiel: nie bluffen) etwas kostet, hängt vom Spieler ab. Live bei den Strategiereglern der Seitenleiste.")
    with st.expander("Spielbaum zeigen"):
        n_tree = st.radio("Karten", [2, 3], index=1, horizontal=True, key="tree_n", help="Bei zwei Karten verrät die eigene Karte die des anderen: jede Informationsmenge hat nur einen Knoten.")
        st.plotly_chart(Z.build_tree(SC.kuhn_instance(n_tree)[0], n_tree), width="stretch", key="tree_chart")
        st.caption("Gepunktet verbunden: Knoten derselben Informationsmenge (der Spieler sieht nur seine eigene Karte). Auszahlung der Endknoten an den ersten Spieler (Einsätze).")
    curves = _curves()
    st.plotly_chart(Z.build_loss_curves(curves), width="stretch", key="loss_chart")
    st.caption("Lücke der abweichenden Seite, wenn genau eine Entscheidung läuft und die übrigen im Gleichgewicht mit α = 1/6 stehen. Durchgezogen: zweiter Spieler, gestrichelt: erster Spieler.")
    v_curves = V.verdict_curves(curves)
    show(v_curves)
    if tables:
        st.markdown("**Gleichgewichtsmenge, exakt** (Realisierungswahrscheinlichkeit der Setzen-/Mitgehen-Sequenzen über alle Gleichgewichte; Bruch-Simplex auf der Sequenzform)")
        table(V.rows_family(tables))
        v_fam = V.verdict_family(tables)
        show(v_fam)
        verdicts.append(v_fam)
        st.markdown("**Kosten von Verboten** (garantierter Wert des eingeschränkten Spielers; Kosten = Gleichgewichtswert minus garantierter Wert; Einsätze je Hand)")
        table(V.rows_bans(tables))
        v_bans = V.verdict_bans(tables)
        show(v_bans)
        verdicts.append(v_bans)
        st.markdown("**Einfache Faustregeln** (Kosten gegen die beste Antwort, wenn die Regel auf dem jeweiligen Platz gespielt wird)")
        table(V.rows_rules(tables))

# --- Reiter 2 ------------------------------------------------------------------------------------------------------------------------------------
with tab2:
    st.subheader("🔬 Experiment E2: Wie weit trägt die Sequenzform, wo die Normalform nicht mehr passt?")
    st.caption("**Erwartung:** Die Normalform wächst mit der Kartenzahl exponentiell, die Sequenzform linear; beide Wege liefern, wo beide laufen, denselben Spielwert. Der Spielwert ist nicht monoton in der Kartenzahl. "
               "Live bei der Kartenzahl der Seitenleiste (Reiter 2).")
    sv = _size(settings.n)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Sequenzen je Spieler", sv.sequences, help="4n + 1 (die Tests prüfen das gegen die Zählung am Baum).")
    s2.metric("Einträge der Normalform", V.dots(sv.entries) if sv.entries < 10 ** 8 else V.sci(sv.entries), help=f"Reine Strategien des ersten mal des zweiten Spielers (reduziert): {V.dots(sv.entries)}.")
    s3.metric("Spielwert", V.frac(sv.value_exact) if sv.value_exact is not None else V.de(sv.value_float, 4), help=f"An den ersten Spieler, Einsätze je Hand ({V.de(sv.value_float, 4)}); bis n = 5 exakt in Brüchen, darüber HiGHS in Gleitkomma.")
    s4.metric("Zeit Sequenzform (s)", V.de(sv.t_seq, 3), help="Einmalmessung dieser Rechnung (HiGHS), plattformabhängig.")
    st.plotly_chart(Z.build_sizes(settings.n), width="stretch", key="size_chart")
    st.caption("Einträge der Normalform (3ⁿ·4ⁿ = 12ⁿ) gegen die Sequenzen je Spieler (4n + 1), logarithmische Achse.")
    v_size = V.verdict_size(sv)
    show(v_size)
    verdicts.append(v_size)
    if sv.t_normal is not None:
        st.caption(f"Zeiten dieser Rechnung: Normalform aufstellen und lösen {V.de(sv.t_normal, 3)} s, Sequenzform (HiGHS) {V.de(sv.t_seq, 3)} s" + (f", Sequenzform in Brüchen {V.de(sv.t_exact, 3)} s." if sv.t_exact is not None else "."))
    st.markdown("**Größe nach Kartenzahl** (Formeln; die Tests prüfen sie gegen die Zählung am Baum)")
    table(V.size_rows())
    if tables:
        st.markdown("**Vorgerechnet: Spielwert und Zeit** (einmalige Messung, Sekunden)")
        table(V.rows_size(tables))

# --- Reiter 3 ------------------------------------------------------------------------------------------------------------------------------------
with tab3:
    st.subheader("🔬 Experiment E3: Wie schnell finden die Regret-Verfahren das Gleichgewicht auf dem Baum?")
    st.caption("**Erwartung:** Das Mittel der Strategien nähert sich dem Gleichgewicht, die letzte Iteration nicht unbedingt. CFR⁺ und Discounted CFR sind bei gleicher Schrittzahl näher dran als das vollständige CFR; "
               "Regret Matching auf der Normalform ist langsamer als CFR auf dem Baum. Live im Kuhn-Spiel bei den Reglern der Seitenleiste (Reiter 3); darunter die vorgerechneten Langzeitreihen.")
    seed_key = settings.seed if settings.start == "zufall" else 0
    with st.spinner("Die Verfahren werden gerechnet ..."):
        result = _kuhn_runs(settings.n3, settings.steps, settings.start, seed_key)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(Z.build_convergence(result["runs"], "t", title="Lücke gegen Schritte"), width="stretch", key="conv_steps")
    with c2:
        st.plotly_chart(Z.build_convergence(result["runs"], "nodes", last=False, title="Lücke gegen besuchte Knoten (Normalform: Matrixeinträge)"), width="stretch", key="conv_nodes")
    st.caption("Größere der beiden Lücken (Bestantwort gegen den Spielwert); durchgezogen das Mittel, gepunktet die letzte Iteration (nur CFR und CFR⁺). Rechts: Aufwand in besuchten Knoten (Normalform: Matrixeinträge je Schritt), "
               "also nicht Rechenzeit.")
    v_live = V.verdict_runs_live(result, settings.steps)
    show(v_live)
    verdicts.append(v_live)
    table(V.run_rows(result["runs"], settings.steps))
    if tables:
        st.markdown("**Vorgerechnet: Langzeitreihe im Kuhn-Spiel mit drei Karten** (größere Lücke des Mittels)")
        st.plotly_chart(Z.build_mean_table_figure({**tables["kuhn"], **tables["rm"]}, "Langzeitreihe, Kuhn mit drei Karten"), width="stretch", key="long_chart")
        table(V.rows_kuhn_runs(tables))
        st.markdown("**Zerlegung des Vorsprungs von CFR⁺**")
        table(V.rows_decomposition(tables))
        v_dec = V.verdict_decomposition(tables)
        show(v_dec)
        verdicts.append(v_dec)
        st.markdown("**Letzte Iteration** (größere Lücke)")
        table(V.rows_last(tables))
        v_last = V.verdict_last(tables)
        show(v_last)
        verdicts.append(v_last)
        v_dcfr = V.verdict_dcfr(tables)
        show(v_dcfr)
        verdicts.append(v_dcfr)
        st.markdown("**Zufallsstart** (zufällige Anfangsregrets, Mittel ± Standardabweichung über vier Zufalls-Seeds)")
        table(V.rows_start(tables))
        v_start = V.verdict_start(tables)
        show(v_start)
        verdicts.append(v_start)
        st.markdown("**Externes Sampling im Kuhn-Spiel** (vier Zufalls-Seeds)")
        table(V.rows_kuhn_mc(tables))

    st.markdown("---")
    st.subheader("🔬 Experiment E4: Leduc-Poker und externes Sampling")
    st.caption("**Erwartung:** Die Literatur nennt Sampling für große Spiele als Vorteil. Auf diesem kleinen Baum (1 939 Knoten) ist offen, ob es sich schon lohnt. Leduc-Regeln aus dem Gedächtnis. "
               "Das Rechnen dauert einige Sekunden und läuft nur auf Knopfdruck.")
    key_leduc = (settings.lsteps, settings.mc, settings.seed)
    if st.button("Leduc rechnen", key="leduc_button", help="Rechnet CFR, CFR⁺ und Discounted CFR mit der gewählten Schrittzahl und das externe Sampling mit dem Zufalls-Seed."):
        t0 = time.time()
        with st.spinner("Leduc wird gerechnet (einige Sekunden) ..."):
            st.session_state["leduc_result"] = (key_leduc, V.leduc_runs(settings.lsteps, settings.mc, settings.seed), time.time() - t0)
    stored = st.session_state.get("leduc_result")
    if stored and stored[0] == key_leduc:
        _, lres, secs = stored
        st.plotly_chart(Z.build_convergence({**lres["runs"], "mccfr": lres["sampling"]}, "nodes", last=False, title="Leduc: Lücke gegen besuchte Knoten"), width="stretch", key="leduc_chart")
        v_ld = V.verdict_leduc_live(lres, settings.lsteps)
        show(v_ld)
        verdicts.append(v_ld)
        st.caption(f"Rechenzeit dieses Laufs: {V.de(secs, 1)} s (einmalig gemessen, plattformabhängig).")
    elif stored:
        st.info("Die Regler haben sich seit dem letzten Lauf geändert: „Leduc rechnen“ noch einmal drücken.")
    if tables:
        st.markdown("**Vorgerechnet: Leduc** (volle Verfahren bis T = 2 000)")
        table(V.rows_leduc(tables))
        v_lt = V.verdict_leduc_table(tables)
        show(v_lt)
        verdicts.append(v_lt)
        st.markdown("**Vorgerechnet: externes Sampling in Leduc** (vier Zufalls-Seeds, Mittel ± Standardabweichung)")
        table(V.rows_leduc_mc(tables))
        v_smp = V.verdict_sampling(tables)
        show(v_smp)
        verdicts.append(v_smp)

# --- Reiter 4 ------------------------------------------------------------------------------------------------------------------------------------
with tab4:
    st.subheader("🔬 Experiment E5: Anmeldung und Kontrolle, ein konstruiertes Nullsummenmodell")
    st.caption("**Erwartung:** Der Verlader weiß, ob eine Sendung riskant ist, der Kontrolleur sieht nur die Meldung. Liegt der Anteil riskanter Sendungen über einer Schwelle, melden manche riskanten Sendungen „sauber“ und der Kontrolleur "
               "kontrolliert nach „sauber“ mit einem festen Anteil; darunter lügen alle und es wird nicht kontrolliert. Die Entschädigung bei Kontrolle ist eine Konstruktion, die das Spiel zur Nullsumme macht; "
               "das Modell ist kein Abbild einer echten Kontrolle. Live bei den Reglern der Seitenleiste (Reiter 4).")
    cell = _anmeldung(settings)
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Regime", cell["regime"], help="ehrlich: g ≤ r; alle lügen: Anteil riskanter Sendungen unter der Schwelle; gemischt sonst.")
    a2.metric("Lügenanteil λ", V.de(float(V.Fr(cell["lam"])) * 100, 1) + " %", help="Anteil der riskanten Sendungen, die „sauber“ melden.")
    a3.metric("Kontrollanteil κ", V.de(float(V.Fr(cell["kap"])) * 100, 1) + " %", help="Anteil der als „sauber“ gemeldeten Sendungen, die kontrolliert werden.")
    a4.metric("Wert für den Verlader", V.de(float(V.Fr(cell["value"])), 2) + " €", help="Euro je Sendung im Gleichgewicht.")
    cc1, cc2 = st.columns(2)
    with cc1:
        cur_p = _anm_curves(settings, "p")
        st.plotly_chart(Z.build_anmeldung(cur_p, "p", settings.p), width="stretch", key="anm_p_chart")
    with cc2:
        cur_s = _anm_curves(settings, "s")
        st.plotly_chart(Z.build_anmeldung(cur_s, "s", settings.s), width="stretch", key="anm_s_chart")
    st.caption("Geschlossene Form über dem Anteil riskanter Sendungen (links) und über der Strafe (rechts), die übrigen Regler wie in der Seitenleiste.")
    v_anm = V.verdict_anmeldung(cell, settings)
    show(v_anm)
    verdicts.append(v_anm)
    table(V.rows_anmeldung_live(cell))
    if tables:
        st.markdown("**Vorgerechnet: Raster aus Anteil riskanter Sendungen und Strafe** (alle Wege in Brüchen verglichen)")
        table(V.rows_anmeldung_grid(tables))
        v_ag = V.verdict_anmeldung_table(tables)
        show(v_ag)
        verdicts.append(v_ag)
        st.markdown("**Wirkung der Strafe** (Anteil riskanter Sendungen 3/10, sonst Voreinstellung)")
        table(V.rows_anmeldung_strafe(tables))

# --- Verwandte Demos, Grenzen, Formeln -----------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔗 Verwandte Demos")
st.markdown(
    "- `nullsummenspiel-demo`: Nullsummenspiele in der Auszahlungsmatrix (gleichzeitige Züge), Regret Matching und Verwandte dort; hier derselbe Gedanke auf dem Baum mit verdeckter Information.\n"
    "- `noregret-demo` und `korreliert-demo`: Lernen in Normalform-Spielen (Hedge, Regret Matching); keine Informationsmengen.\n"
    "- `verhandlung-demo`: Lernen im Ultimatumspiel und im Zwei-Runden-Spiel, ein Baum mit vollständiger Information.\n"
    "- `minimax-demo`: Suche im Spielbaum mit vollständiger Information; hier kennt man den Zustand des anderen nicht.\n"
    "- `mcts-demo`: Baumsuche für ein Pfadproblem mit einem Akteur.\n"
    "- `kontrollspiel-demo`: Festlegung, die der andere beobachtet; hier legt sich niemand fest, und der andere sieht die Karte nicht.\n"
    "- `einzelgut-auktion-demo`: private Werte in einem einmaligen Zug; hier folgen die Züge nacheinander."
)

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(T.ASSUMPTIONS_MARKDOWN)

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(T.MATH_MARKDOWN)

st.subheader("📄 Ergebnisse als PDF")
if st.button("PDF erstellen", key="pdf_button"):
    from vdi_pdf_export import build_pdf
    st.session_state["pdf_bytes"] = build_pdf(settings, view, cell, verdicts)
if st.session_state.get("pdf_bytes"):
    st.download_button("⬇️ PDF herunterladen", st.session_state["pdf_bytes"], file_name="verdeckte-information.pdf", mime="application/pdf", key="pdf_download")

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
