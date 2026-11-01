"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_leduc_button_runs_at_the_slider_maximum():
    """Leduc auf Knopfdruck mit den größten Schrittzahlen (1 000 Schritte der vollen Verfahren, 20 000 Iterationen Sampling): kein Fehler, das Verdikt erscheint."""
    at = _fresh_app()
    at.sidebar.slider(key="leduc_slider").set_value(1000).run(timeout=TIMEOUT)
    at.sidebar.slider(key="mc_slider").set_value(20000).run(timeout=TIMEOUT)
    at.button(key="leduc_button").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Leduc, Spielwert" in i.value for i in at.info)
    at.sidebar.slider(key="leduc_slider").set_value(500).run(timeout=TIMEOUT)      # geänderter Regler: der alte Lauf wird nicht mehr gezeigt
    assert not at.exception and any("noch einmal drücken" in i.value for i in at.info)


def test_pdf_button_produces_a_pdf_with_the_verdicts():
    at = _fresh_app()
    at.button(key="pdf_button").click().run(timeout=TIMEOUT)
    assert not at.exception
    pdf = at.session_state["pdf_bytes"]
    assert pdf[:5] == b"%PDF-" and len(pdf) > 2000


def test_all_minima_and_all_maxima_together_do_not_raise():
    """Alle Regler zugleich am Minimum bzw. Maximum (größter Rechenaufwand: 13 Karten, 6 Karten und 3 000 Schritte für die Verfahren, Anmeldung mit allen Maxima)."""
    for edge in ("min", "max"):
        at = _fresh_app()
        for slider in at.sidebar.slider:
            value = slider.min if edge == "min" else slider.max
            slider.set_value(int(value) if isinstance(slider.value, int) else value)
        for box in at.sidebar.number_input:
            box.set_value(box.min if edge == "min" else box.max)
        at.run(timeout=TIMEOUT)
        assert not at.exception, (edge, [str(e) for e in at.exception])


def test_every_start_choice_and_seed_edge_does_not_raise():
    for choice in ("gleich", "zufall"):
        for seed in (0, 999999):
            at = _fresh_app()
            at.sidebar.selectbox(key="start_select").set_value(choice)
            at.sidebar.number_input(key="seed_input").set_value(seed)
            at.run(timeout=TIMEOUT)
            assert not at.exception, (choice, seed, [str(e) for e in at.exception])


def test_the_tabs_show_their_tables_and_verdicts():
    at = _fresh_app()
    texts = " ".join(m.value for m in at.markdown)
    for needle in ("Experiment E1", "Experiment E2", "Experiment E3", "Experiment E4", "Experiment E5", "Kosten von Verboten", "Gleichgewichtsmenge, exakt", "Zerlegung des Vorsprungs"):
        assert needle in texts or any(needle in s.value for s in at.subheader), needle
    assert len(at.dataframe) >= 15 and not at.error
