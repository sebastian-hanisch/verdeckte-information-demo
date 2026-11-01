"""PDF-Export (fpdf2, Kernschriften): Einstellungen, Kennzahlen der Hauptansicht und die Verdikte. Erst nach Klick erzeugt (DEMO-PLAYBOOK §1c)."""

from __future__ import annotations

from fpdf import FPDF

import vdi_evaluation as V
from vdi_scenario import Settings

_REPLACE = {"–": "-", "—": "-", "≤": "<=", "≥": ">=", "≠": "!=", "√": "Wurzel", "²": "2", "Σ": "Summe", "°": " Grad", "·": "*", "−": "-", "„": '"', "“": '"', "∞": "unendlich",
            "→": "->", "ε": "eps", "β": "beta", "α": "alpha", "θ": "theta", "λ": "lambda", "σ": "sigma", "π": "pi", "δ": "delta", "η": "eta", "Δ": "Delta", "γ": "gamma", "ρ": "rho",
            "κ": "kappa", "μ": "mu", "φ": "phi", "≈": "~", "½": "1/2", "…": "...", "‚": ",", "‘": "'", "’": "'", "”": '"', "µ": "mu", "∈": "in", "¹": "1", "₀": "0", "₁": "1", "₂": "2",
            "±": "+-", "⋅": "*", "€": "EUR", "⁺": "+", "⁻": "-", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁰": "0", "ⁿ": "n", "⁄": "/"}


def _latin(text: str) -> str:
    """Kernschriften kennen nur Latin-1 (Umlaute gehören dazu): Sonderzeichen ersetzen, Markdown-Zeichen entfernen."""
    for a, b in _REPLACE.items():
        text = text.replace(a, b)
    return text.replace("**", "").replace("`", "").encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, view: V.StrategyView, anm: dict, verdicts: list[tuple[str, str]]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _latin("Verdeckte Information: Kuhn-Poker, Sequenzform, CFR"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _latin(
        f"Strategie (Zwölftel): Bube setzt {s.jbet}, König setzt {s.kbet}, Dame geht nach Pass-Setzen mit {s.qcall}; zweiter Spieler: Bube bluft {s.bluff}, Dame geht mit {s.call}. "
        f"Karten Reiter 2: {s.n}; Reiter 3: {s.n3} Karten, {s.steps} Schritte, Start {s.start}, Leduc {s.lsteps} Schritte, Sampling {s.mc} Iterationen; Zufalls-Seed {s.seed}. "
        f"Anmeldung: b {s.b}, c {s.c}, g {s.g}, s {s.s}, r {s.r}, p {s.p} %."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Kennzahlen (Einsaetze je Hand bzw. Euro je Sendung)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    lines = [
        f"Kuhn-Poker, drei Karten: Spielwert {V.frac_dec(V.KUHN_VALUE)} an den ersten Spieler; Wert des gewaehlten Profils {V.frac_dec(view.value)}; "
        f"Luecke des ersten Spielers {V.frac_dec(view.loss_first)}, des zweiten Spielers {V.frac_dec(view.loss_second)}; in der Gleichgewichtsfamilie: {'ja' if view.in_family else 'nein'}.",
        f"Anmeldung und Kontrolle: Regime {anm['regime']}; Luegenanteil {V.frac_dec(anm['lam'])}; Kontrollanteil {V.frac_dec(anm['kap'])}; Wert {V.frac_dec(anm['value'])} Euro je Sendung.",
    ]
    for line in lines:
        pdf.multi_cell(0, 5, _latin(line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Verdikte", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for _, text in verdicts:
        pdf.multi_cell(0, 5, _latin(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _latin("Kuhn-Poker ist ein Lehrspiel, kein Logistikspiel. Eigennutz, Nullsumme, Regeln, Einsaetze und Kosten sind Modellannahmen, keine Aussagen ueber echte Spieler oder Betriebe. "
                                "Alle Zahlen sind eigene Rechnung (exakt in Brüchen oder gemessen), gestuetzt durch Handrechnung und unabhaengige Rechenwege in den Tests."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
