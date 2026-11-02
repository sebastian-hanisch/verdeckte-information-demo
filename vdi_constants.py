"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets.

Rechenaufwand am Slider-Maximum (Python, eine Größenordnung): Kuhn mit 13 Karten hat 1 405 Knoten und 53 Sequenzen je Spieler, das Sequenzform-LP (HiGHS) braucht Hundertstelsekunden;
die Normalform wird nur bis n = 5 (243 × 1 024 Einträge) aufgestellt. Reiter 3, Kuhn bis n = 6 (271 Knoten) und 3 000 Schritte: ein Schritt eines Verfahrens besucht den Baum ein- bis zweimal,
fünf Verfahren plus zwei Normalform-Verfahren rechnen einige Sekunden. Leduc: 1 939 Knoten, 337 Sequenzen je Spieler, LP etwa 0,03 s, ein Schritt von CFR⁺ rund 5 ms,
1 000 Schritte also rund 5 s je Verfahren; externes Sampling 20 000 Iterationen rund 3 s. Exakter Simplex in Brüchen: Kuhn bis n = 5 in Sekunden (Zeit wächst etwa mit der dritten Potenz)."""

N_MIN, N_MAX, DEFAULT_N = 2, 13, 3                     # Karten im Größenvergleich (Reiter 2)
N_EXACT_MAX = 5                                        # bis hierher wird auch der exakte Wert in Brüchen gerechnet
N_NORMAL_MAX = 5                                       # bis hierher wird die Normalform aufgestellt
N3_MIN, N3_MAX, DEFAULT_N3 = 2, 6, 3                   # Karten für die Regret-Verfahren (Reiter 3)
N3_NORMAL_MAX = 5                                      # Regret Matching auf der Normalform bis hierher
STEPS_MIN, STEPS_MAX, DEFAULT_STEPS = 100, 3000, 1000  # Schritte der Verfahren im Kuhn-Spiel
LEDUC_MIN, LEDUC_MAX, DEFAULT_LEDUC = 100, 1000, 300   # Schritte der vollen Verfahren in Leduc (auf Knopfdruck)
MC_MIN, MC_MAX, DEFAULT_MC = 1000, 20000, 5000         # Iterationen des externen Samplings in Leduc (auf Knopfdruck)
TWELFTHS = 12                                          # Strategieregler in Zwölfteln
STRAT_DEFAULT = {"jbet": 2, "kbet": 6, "qcall": 6, "bluff": 4, "call": 4}   # Gleichgewicht mit α = 1/6, in Zwölfteln
A_B_MIN, A_B_MAX, DEFAULT_A_B = 1, 30, 10              # Wert einer Sendung in Ordnung (Euro je Sendung)
A_C_MIN, A_C_MAX, DEFAULT_A_C = 0, 10, 2               # Entschädigung bei Kontrolle
A_G_MIN, A_G_MAX, DEFAULT_A_G = 1, 40, 15              # Gewinn einer unbemerkten riskanten Sendung
A_S_MIN, A_S_MAX, DEFAULT_A_S = 0, 160, 20             # Strafe bei Kontrolle einer falsch gemeldeten Sendung
A_R_MIN, A_R_MAX, DEFAULT_A_R = 0, 30, 6               # Nutzen einer ehrlich gemeldeten riskanten Sendung
A_P_MIN, A_P_MAX, DEFAULT_A_P = 1, 99, 30              # Anteil riskanter Sendungen in Prozent
A_FEE = 1                                              # Gebühr, die nur eine in Ordnung befindliche Sendung bei der Meldung „riskant“ zahlt (fest, ohne Einfluss auf das Gleichgewicht)
SEED_MAX, DEFAULT_SEED = 999999, 35
TABLE_SEEDS = (11, 22, 33, 44)                         # Zufalls-Seeds der vorgerechneten Reihen
START_CHOICES = {"gleich": "gleichverteilt", "zufall": "Zufallsstart"}
DEFAULT_START = "gleich"

COLOR_FIRST = "#4c78a8"       # erster Spieler
COLOR_SECOND = "#e8a838"      # zweiter Spieler
COLOR_GOOD = "#2F6B65"        # Gleichgewicht, Sequenzform
COLOR_LOSS = "#d62728"        # Lücke, Warnung
COLOR_NEUTRAL = "rgba(150,150,150,0.55)"
VARIANT_COLORS = {"cfr": "#999999", "cfr_alt": "#4c78a8", "cfr_clip": "#8c6bb1", "cfrplus": "#2F6B65", "dcfr": "#e8a838", "rm_nf": "#c97b84", "rmplus_nf": "#7fb3d5", "mccfr": "#d62728"}

PRESETS = {
    "Kuhn Gleichgewicht (α = 1/6)": {},
    "Erster Spieler bluft nie (α = 0)": {"jbet": 0, "kbet": 0, "qcall": 4},
    "Zweiter Spieler bluft nie": {"bluff": 0},
    "Kuhn mit zwei Karten": {"n": 2, "n3": 2},
    "Sequenzform gegen Normalform (n = 5)": {"n": 5},
    "Viele Karten (n = 13)": {"n": 13},
    "CFR gegen CFR⁺ (3 000 Schritte)": {"steps": 3000},
    "Zufallsstart": {"start": "zufall"},
    "Leduc (600 Schritte)": {"lsteps": 600},
    "Anmeldung: hohe Strafe (s = 160)": {"s": 160},
    "Anmeldung: alle lügen (p = 5 %)": {"p": 5},
    "Anmeldung: Ehrlichkeit lohnt (g = 5)": {"g": 5},
}
PRESET_HELP = {
    "Kuhn Gleichgewicht (α = 1/6)": "Kuhn-Poker mit drei Karten, alle Strategieregler im Gleichgewicht der Familie mit α = 1/6: Lücke 0 auf beiden Seiten. Alle anderen Regler auf ihren Voreinstellungen.",
    "Erster Spieler bluft nie (α = 0)": "Der erste Spieler setzt mit dem Buben nie und mit dem König nie im ersten Zug: ebenfalls ein Gleichgewicht (α = 0), Lücke 0. Bluffen ist für den ersten Spieler ein Freiheitsgrad.",
    "Zweiter Spieler bluft nie": "Der zweite Spieler setzt mit dem Buben nach einem Pass nie. Der erste Spieler kann das ausnutzen; die Lücke ist 1/9 Einsatz je Hand.",
    "Kuhn mit zwei Karten": "Bube und König: das kleinste Spiel mit verdeckter Information, Spielwert 0. Gilt für Reiter 2 und 3 (Reiter 1 bleibt bei drei Karten).",
    "Sequenzform gegen Normalform (n = 5)": "Fünf Karten: 243 × 1 024 reine Strategien gegen 21 Sequenzen je Spieler. Beide Wege liefern denselben Spielwert.",
    "Viele Karten (n = 13)": "Dreizehn Karten: die Normalform hätte 1 594 323 × 67 108 864 Einträge; die Sequenzform hat 53 Sequenzen je Spieler. Nur die Sequenzform wird gerechnet.",
    "CFR gegen CFR⁺ (3 000 Schritte)": "Dreitausend Schritte im Kuhn-Spiel: die Verfahren unterscheiden sich in Lücke und Steigung deutlich; das vollständige CFR hat die größte Lücke.",
    "Zufallsstart": "Die Verfahren starten mit zufälligen Anfangsregrets statt gleichverteilt (Zufalls-Seed der Seitenleiste).",
    "Leduc (600 Schritte)": "Leduc-Poker (Regeln aus dem Gedächtnis): der Lauf auf Knopfdruck in Reiter 3 nimmt 600 Schritte. Dauert einige Sekunden.",
    "Anmeldung: hohe Strafe (s = 160)": "Reiter 4 mit Strafe 160 statt 20: die Kontrolle wird seltener, die Lügen auch.",
    "Anmeldung: alle lügen (p = 5 %)": "Nur 5 Prozent riskante Sendungen: unter der Schwelle lohnt keine Kontrolle, alle riskanten Sendungen werden als sauber gemeldet.",
    "Anmeldung: Ehrlichkeit lohnt (g = 5)": "Der Gewinn einer unbemerkten riskanten Sendung (5) liegt nicht über dem Nutzen der ehrlichen Meldung (6): niemand lügt, niemand kontrolliert.",
}
