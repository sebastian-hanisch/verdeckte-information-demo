# Verdeckte Information: Spiele, in denen man den Zustand des anderen nicht sieht – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-verdeckte-information-demo.streamlit.app/)**

Stück der Linie **regeln-verhandeln** (Arbeitsname; Name, Bereich und Themenfeld werden erst bei der Einbindung in die Website festgelegt) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Demo rechnet **Spiele mit verdeckter Information und Zügen nacheinander**: wie man sie ohne die ausgeschriebene Normalform löst (Sequenzform), wie das Gleichgewicht aussieht (eine ganze Familie; Bluffen ist für die beiden Spieler nicht gleich nötig) und wie schnell die Regret-Verfahren (CFR, CFR⁺, Discounted CFR, externes Sampling) es auf dem Baum finden. **Das Lehrspiel ist Kuhn-Poker** (zwei Spieler, drei Karten), ausdrücklich **kein Logistikspiel**: es ist das kleinste Spiel, an dem sich das Problem exakt zeigen lässt. Nur Reiter 4 („Anmeldung und Kontrolle“) hat einen Logistikbezug und ist ein **konstruiertes Nullsummenmodell**. Karten, Regeln, Einsätze, Kosten und Eigennutz sind **Modellannahmen**, keine Aussagen über echte Spieler oder Betriebe.

Abgrenzung: [`nullsummenspiel-demo`](https://github.com/sebastian-hanisch/nullsummenspiel-demo) rechnet Nullsummenspiele in der Auszahlungsmatrix (gleichzeitige Züge, volle Kenntnis der Matrix; Regret Matching, RM⁺, Multiplicative Weights, Fictitious Play, LP) und nennt verdeckte Information mit Sequenzform-LP und CFR dort ausdrücklich als nicht gebaut; hier steht diese Rechnung, und Regret Matching erscheint nur als Vergleich auf der Normalform des Kuhn-Spiels. [`noregret-demo`](https://github.com/sebastian-hanisch/noregret-demo) (Hedge, EXP3), [`korreliert-demo`](https://github.com/sebastian-hanisch/korreliert-demo) (Regret Matching, korreliertes Gleichgewicht) und [`verhandlung-demo`](https://github.com/sebastian-hanisch/verhandlung-demo) (Lernen im Ultimatumspiel und im Zwei-Runden-Spiel, ein Baum mit vollständiger Information) lernen in Normalform oder in Bäumen ohne Informationsmengen. [`minimax-demo`](https://github.com/sebastian-hanisch/minimax-demo) sucht in Bäumen mit vollständiger Information; [`mcts-demo`](https://github.com/sebastian-hanisch/mcts-demo) ist Baumsuche für ein Pfadproblem mit einem Akteur. [`kontrollspiel-demo`](https://github.com/sebastian-hanisch/kontrollspiel-demo) hat Festlegung, die der andere beobachtet; [`einzelgut-auktion-demo`](https://github.com/sebastian-hanisch/einzelgut-auktion-demo) private Werte in einem einmaligen Zug.

## Kernfrage

*Wie rechnet man ein Spiel, in dem man den Zustand des anderen nicht sieht und die Züge nacheinander kommen, ohne die Normalform auszuschreiben, und wie schnell findet man damit ein Gleichgewicht?* Die Antwort hat fünf Teile. (1) **Die Gleichgewichtsmenge des Kuhn-Spiels mit drei Karten ist exakt eine Familie** (Setzen mit dem Buben α ∈ [0, 1/3], mit dem König 3α), der zweite Spieler ist eindeutig; der Spielwert ist −1/18 (−0,0556) Einsätze je Hand an den ersten Spieler (H1, H2). (2) **Bluffen ist asymmetrisch:** das Verbot des Bluffens kostet den zweiten Spieler 1/9 (0,1111), den ersten 0 Einsätze je Hand (H8). (3) **Die Sequenzform wächst linear, die Normalform exponentiell:** 53 Sequenzen je Spieler gegen 106.993.205.379.072 Einträge der Normalform bei 13 Karten (H3). (4) **Im Kuhn-Spiel mit drei Karten ändert sich die Steigung des Mittels schon durch die Abwechslung der Aktualisierung,** Kappen der Regrets und lineare Mittelung ändern dort vor allem die Konstante (H5); das Mittel konvergiert, die letzte Iteration beim vollständigen CFR nicht (H4); Discounted CFR schlägt CFR⁺ nur teilweise (H6). (5) **Externes Sampling ist auf dem kleinen Leduc-Baum ab etwa 3 000 Iterationen nach besuchten Knoten deutlich schlechter als die vollen Verfahren** (bei 1 000 Iterationen nicht von CFR⁺ zu unterscheiden) (H7), gegen die Erwartung aus der Literatur über große Spiele.

## Befunde und Korrekturen gegenüber dem Plan

Der Einzelplan (Vormessung vom 2026-11-01, Wegwerfskripte) wurde nicht blind übernommen; jede Zahl ist im Bau neu gemessen, mit SplitMix64-Strömen statt der numpy-Ströme der Vormessung. Abweichungen und neue Funde:

- **Die Richtung der Befunde H1 bis H10 bleibt, einzelne Zahlen weichen ab** (andere Prüfpunkte und Zufallsströme): Steigungen im Langzeitlauf T = 1 000 bis 300 000 für abwechselndes CFR, Kappen und CFR⁺ sind −0,84, −0,88 und −0,83 (Plan: −0,86 / −0,86 / −0,81); externes Sampling in Leduc nach 100 000 Iterationen 5,1·10⁻² ± 7,8·10⁻³ (Plan 0,053 ± 0,0075); Zufallsstart mit CFR⁺ bei T = 10 000 5,4·10⁻⁵ ± 3,4·10⁻⁵ (Plan 4,5·10⁻⁵ ± 1,4·10⁻⁵).
- **Neu: die Zerlegung auch für Discounted CFR und die Kosten der Verbote vollständig** (13 Verbote, 4 Faustregeln, Verzicht auf Zufall) und **die Gleichgewichtsmenge für alle 24 Sequenzen** (Tabelle unten), nicht nur die beiden Linearkombinationen.
- **Reiter 4 („Anmeldung und Kontrolle“) ist aufgenommen** (Plan: Empfehlung ja, gelb): die Gebühr *f* ist fest, weil sie das Gleichgewicht nicht ändert (4 Werte von *f* geben alle denselben Wert 229/25 Euro je Sendung; sie trifft nur in Ordnung befindliche Sendungen, die fälschlich „riskant“ melden, und das ist nie optimal), und kein Regler ist damit ohne Wirkung.
- **Kern mit Bruch-Simplex statt nur in `tests/`:** der Plan legte den Simplex in die Tests. Er liegt hier im Kern (`vdi_exact.py`), weil die Tabellen der Verbote und der Gleichgewichtsmenge exakt in Brüchen gerechnet werden; scipy (HiGHS) rechnet Leduc und große Kartenzahlen und dient in den Tests als Gegenprobe.
- **Strategieregler statt eines Reglers α:** fünf Regler in Zwölfteln (Bube setzt, König setzt, Dame geht mit; Bluff und Mitgehen des zweiten Spielers); die Familie ist am Preset „Kuhn Gleichgewicht (α = 1/6)“ und „α = 0“ abgelesen, und ein Kennzeichen zeigt, ob die Wahl in der Familie liegt.
- **Normalform live bis 5 Karten** (der Plan nannte n ≤ 5 live und n = 6 als 4-Sekunden-Fall): n = 6 steht in der vorgerechneten Tabelle.
- **Modulname `vdi_strategy.py`** statt `vdi_eval.py` (Bewertung von Strategien); `vdi_evaluation.py` trägt wie in den Nachbarn die Ansichten, Zeilenbauer und Verdikte.
- **Port 9227** (Vorschlag des Plans, frei geprüft).
- **Gefundene Fehler beim Bau:** im Kern keiner (alle Orakel waren beim ersten Lauf grün); in den Tests und Messungen: eine falsche Handrechnung der Strategiesumme im ersten CFR-Schritt (Test, nicht Kern), die Prüfpunktliste ohne T = 30 000 (die Langzeitreihe hatte keine Spalte dafür) und die Anlaufzeit von scipy, die in der ersten Zeitmessung 1,5 s statt einiger Millisekunden für zwei Karten auswies (jetzt vorgewärmt).

## Modell

**Kuhn-Poker mit n Karten** (n = 3: Kuhn 1950). Jeder zahlt 1 ein und bekommt eine andere Karte, gleichverteilt. Der erste Spieler passt oder setzt (1 mehr). Nach Pass darf der zweite passen (höhere Karte gewinnt 1) oder setzen; setzt er, entscheidet der erste zwischen Aufgeben (verliert 1) und Mitgehen (höhere Karte gewinnt 2). Nach einem Setzen des ersten gibt der zweite auf (der erste gewinnt 1) oder geht mit (höhere Karte gewinnt 2). Auszahlungen aus Sicht des ersten Spielers, Zwei-Personen-Nullsumme. Baum: 55 Knoten, 30 Endknoten, je Spieler 6 Informationsmengen mit je zwei Knoten; bei zwei Karten hat jede Informationsmenge nur einen Knoten, weil die eigene Karte die des anderen verrät.

**Leduc-Poker** (Rangabstraktion, Regeln aus dem Gedächtnis, Quelle nicht eingesehen): drei Ränge je zweimal, Anfangseinsatz 1, Runde 1 mit Einsatzgröße 2, öffentliche Karte, Runde 2 mit Einsatzgröße 4, höchstens zwei Erhöhungen je Runde, Paar mit der öffentlichen Karte schlägt alles, sonst der höhere Rang, bei Gleichstand wird geteilt. Baum: 1.939 Knoten, 1.116 Endknoten, 144 Informationsmengen und 337 Sequenzen je Spieler, Normalform 1,0·10¹⁴ × 4,7·10²⁶ reine Strategien.

**Anmeldung und Kontrolle** (konstruiertes Nullsummenmodell, Euro je Sendung): eine Sendung ist in Ordnung (1 − p) oder riskant (p); der Verlader weiß es und meldet „sauber“ oder „riskant“ (die Gebühr *f* = 1 zahlt nur eine in Ordnung befindliche Sendung, die „riskant“ meldet; eine riskante Sendung, die „riskant“ meldet, erhält *r* ohne Gebühr). Der Kontrolleur sieht nur die Meldung und kontrolliert oder lässt durch. Auszahlung an den Verlader: in Ordnung *b*, bei Kontrolle zusätzlich die Entschädigung *c* (Konstruktion, die das Spiel zur Nullsumme macht); riskant und „sauber“ gemeldet *g* beim Durchlassen und −*s* bei Kontrolle; riskant und „riskant“ gemeldet *r* (bei Kontrolle plus *c*). Voreinstellung: *b* = 10, *c* = 2, *g* = 15, *s* = 20, *r* = 6, *p* = 30 %.

## Methodik

- **Spielbaum und Informationsmengen** (`vdi_games.py`, `vdi_tree.py`): Spielbeschreibung → flacher Baum in Vorordnung, Prüfung auf perfektes Erinnern (alle drei Spiele bestehen).
- **Bewertung** (`vdi_strategy.py`): Wert eines Profils und **beste Antwort durch Baumdurchlauf**, unabhängig von jedem LP und jedem Regret-Verfahren; Ausnutzbarkeit = Lücke zum Spielwert.
- **Sequenzform** (`vdi_seqform.py`, `vdi_exact.py`): Sequenzen, Nebenbedingungen *E*, *F*, Auszahlungsmatrix *A*, das LP in Gleitkomma (HiGHS) und exakt im Bruch-Simplex (Blandsche Regel), dazu die Gleichgewichtsbereiche je Sequenz und die Verbote als Zusatzbedingung *x*(Sequenz) = 0.
- **Normalform** (`vdi_normal.py`): reduzierte reine Strategien, Matrix *X*·*A*·*Y*ᵀ über Realisierungspläne, Regret Matching und RM⁺ auf der Matrix.
- **Regret-Verfahren** (`vdi_cfr.py`, `vdi_runs.py`): CFR (beide Seiten gleichzeitig), CFR abwechselnd, abwechselnd mit gekappten Regrets, CFR⁺ (zusätzlich lineare Mittelung), Discounted CFR (Parameter 3/2, 0, 2 aus dem Gedächtnis) und externes Sampling, jeweils aus kleinen Einheiten zusammengesetzt; Zufall nur über SplitMix64-Ströme je (Zufalls-Seed, Zelle).
- **Vorgerechnete Reihen** (`tools/make_grid.py` → `data/tables.json`, Erzeuger-Hash, vier Zufalls-Seeds 11 / 22 / 33 / 44): Gleichgewichtsmenge, Verbote, Größenvergleich, Langzeitläufe, Zufallsstart, Sampling, Leduc, Anmeldung. Die Reihen sind pro Prüfpunkt eine **Messung**; das Mittel fällt nicht monoton.
- **Orakel:** direkter Baumdurchlauf aller reinen Strategien (volle 64 × 64-Normalform), scipy/HiGHS auf der Normalform, Aufzählung aller reinen Strategien als beste Antwort, Bruch-Simplex gegen HiGHS, Normalform der eingeschränkten Spiele für die Verbote, geschlossene Form gegen LP für Anmeldung (Abschnitt „Tests“).

## Befunde (gemessen, keine Behauptungen)

Hypothesen des Einzelplans und Stand nach dem Bau. „Teilweise“ heißt: gilt unter den genannten Bedingungen, nicht allgemein; „Offen“: nicht geprüft.

| Nr. | Hypothese | Stand und Beleg |
|---|---|---|
| H1 | Kuhn-Spielwert −1/18 (Literatur aus dem Gedächtnis) | **Ja**, exakt auf drei Wegen: Sequenzform in Brüchen, Normalform (27 × 64) im Bruch-Simplex und HiGHS auf der vollen 64 × 64-Normalform; die Werte beider Seiten summieren sich zu 0 (n = 2 bis 4 geprüft). Spielwerte für n = 2 bis 6 exakt: n = 2: 0, n = 3: −1/18, n = 4: −1/24, n = 5: −1/15, n = 6: −11/180. |
| H2 | Familie α ∈ [0, 1/3], zweiter Spieler eindeutig, und sie ist die **vollständige** Menge | **Ja** (nur Kuhn mit drei Karten): exakte Bereichsrechnung auf allen 24 Sequenzen; Bube setzt in [0, 1/3], „König − 3·Bube“ in [0, 0], „Dame − Bube“ in [1/3, 1/3]; Lücke 0 auf beiden Seiten für α = 0, 1/12, 1/6, 1/4, 1/3 |
| H3 | Sequenzform linear, Normalform exponentiell | **Ja**: 4n + 1 Sequenzen je Spieler gegen 3ⁿ bzw. 4ⁿ reduzierte reine Strategien (3ⁿ · 4ⁿ Matrixeinträge), für n = 2 bis 13 am Baum gezählt; bei n = 6 braucht die Sequenzform 0,005 s, die Normalform aufstellen und lösen 7,4 s (Einmalmessung, plattformabhängig). Der Spielwert ist nicht monoton in n |
| H4 | Das Mittel konvergiert, die letzte Iteration nicht (vollständiges CFR) | **Teilweise**: beim vollständigen CFR liegt die Lücke der letzten Iteration an allen Prüfpunkten ab T = 1 000 zwischen 2,0·10⁻¹ und 4,4·10⁻¹, das Mittel bei 6,7·10⁻⁴ (T = 300 000); CFR⁺ und Discounted CFR haben bei T = 300 000 2,9·10⁻³ und 4,3·10⁻³ in der letzten Iteration, das Mittel 1,1·10⁻⁶ und 7,3·10⁻⁷ |
| H5 | CFR⁺ ist schneller als CFR, und die Steigung kommt von der Abwechslung | **Ja**: bei T = 1 000 ist die Lücke des Mittels 7,9·10⁻³ (CFR) gegen 1,3·10⁻⁴ (CFR⁺), Faktor 63; im Kuhn-Spiel mit drei Karten ändert sich die Steigung des Mittels (T = 1 000 bis 300 000) von −0,48 auf −0,84 schon durch die Abwechslung allein, Kappen und lineare Mittelung ändern dort vor allem die Konstante (Faktor 1,9 und 4,8); die Steigung hängt am Fenster (T = 100 bis 30 000: −0,48 auf −0,92), eine Spur ohne Streuung |
| H6 | Discounted CFR schlägt CFR⁺ (Literatur laut Abstract: in allen getesteten Spielen) | **Teilweise**: Kuhn bei T = 1 000 nein (2,2·10⁻⁴ gegen 1,3·10⁻⁴), Leduc ja (2,2·10⁻⁴ gegen 3,6·10⁻⁴); im Kuhn-Spiel liegt Discounted CFR an 17 von 39 Prüfpunkten ab T = 100 unter CFR⁺, durchgehend erst ab T = 277 837. Parameter aus dem Gedächtnis |
| H7 | Sampling (MCCFR) spart Aufwand | **Nein** (kleine Bäume): in Leduc ist die mittlere Lücke des Samplings an 5 von 5 vergleichbaren Prüfpunkten (1 000 bis 100 000 Iterationen) größer als die jedes der drei vollen Verfahren bei gleich vielen besuchten Knoten, bei 1 000 Iterationen aber nur knapp über CFR⁺ (nicht unterscheidbar, vier Zufalls-Seeds), ab etwa 3 000 deutlich; im Kuhn-Spiel liegt sie an 7 von 7 Prüfpunkten über der von CFR⁺. Bei größeren Bäumen nicht gemessen |
| H8 | Bluffen ist nötig | **Teilweise, asymmetrisch**: für den zweiten Spieler kostet das Verbot 1/9 (0,1111) Einsätze je Hand, für den ersten 0 (Freiheitsgrad in der Familie); ohne Mischen (nur reine Strategien) 1/9 (0,1111) für den ersten, 2/9 (0,2222) für den zweiten Spieler |
| H9 | Regret Matching auf der Normalform konvergiert langsamer als CFR auf dem Baum | **Ja** (Kuhn, drei Karten): bei T = 10 000 6,9·10⁻⁴ (RM⁺, Normalform) gegen 1,0·10⁻⁵ (CFR⁺); Steigung T = 100 bis 30 000 −0,46 gegen −0,90; Regret Matching ohne Plus erreicht 1,5·10⁻³ bei T = 30 000 |
| H10 | Anmeldung: geschlossene Form = LP | **Ja**: 30 von 30 Zellen des Rasters (Anteil riskanter Sendungen × Strafe) und 7 von 7 Zusatzzeilen, alle Wege in Brüchen gleich, Lücken 0; Standard: *λ* = 2/15, *κ* = 9/35, Wert 229/25 (9,16) Euro je Sendung |
| H11 | Reiter 4 trägt als Logistik-Vehikel | **Offen**: ein eigenes Modell mit konstruierter Nullsumme (die Entschädigung bei Kontrolle ist so gewählt), keine Aussage über echte Kontrollen |
| H12 | Leduc-Regeln und -Wert stimmen mit der Literatur | **Offen**: die Regeln sind aus dem Gedächtnis, die Quelle ist nicht eingesehen; der berechnete Spielwert −0,085606 stimmt mit der Erinnerung an die Literatur überein (ungeprüft) |

**Gleichgewichtsmenge des Kuhn-Spiels mit drei Karten** (Realisierungswahrscheinlichkeit der Setzen-/Mitgehen-Sequenzen über alle Gleichgewichte, exakt):

| Spieler | Karte | Lage | Handlung | Bereich |
|---|---|---|---|---|
| erster | König | erster Zug | Setzen | 0 bis 1 |
| erster | König | nach Pass und Setzen des Gegners | Mitgehen | 0 bis 1 |
| erster | Dame | erster Zug | Setzen | 0 |
| erster | Dame | nach Pass und Setzen des Gegners | Mitgehen | 1/3 bis 2/3 |
| erster | Bube | erster Zug | Setzen | 0 bis 1/3 |
| erster | Bube | nach Pass und Setzen des Gegners | Mitgehen | 0 |
| zweiter | Dame | nach Setzen des Gegners | Mitgehen | 1/3 |
| zweiter | Dame | nach Pass des Gegners | Setzen | 0 |
| zweiter | Bube | nach Setzen des Gegners | Mitgehen | 0 |
| zweiter | Bube | nach Pass des Gegners | Setzen | 1/3 |
| zweiter | König | nach Setzen des Gegners | Mitgehen | 1 |
| zweiter | König | nach Pass des Gegners | Setzen | 1 |

**Kosten von Verboten** (garantierter Wert des eingeschränkten Spielers und Kosten gegenüber dem Gleichgewichtswert; Einsätze je Hand):

| Verbot | Spieler | garantierter Wert | Kosten |
|---|---|---|---|
| Zweiter Spieler bluft nie (Bube setzt nach Pass nicht) | zweiter | −1/18 (−0,0556) | 1/9 (0,1111) |
| Zweiter Spieler geht mit der Dame gegen Setzen nie mit | zweiter | −1/9 (−0,1111) | 1/6 (0,1667) |
| Zweiter Spieler geht mit der Dame gegen Setzen immer mit | zweiter | −1/18 (−0,0556) | 1/9 (0,1111) |
| Zweiter Spieler setzt mit dem König nach Pass nie | zweiter | −1/18 (−0,0556) | 1/9 (0,1111) |
| Zweiter Spieler gibt mit dem König gegen Setzen nie auf (nur Mitgehen erlaubt) | zweiter | 1/18 (0,0556) | 0 |
| Zweiter Spieler bluft nie und geht mit der Dame nie mit | zweiter | −1/6 (−0,1667) | 2/9 (0,2222) |
| Erster Spieler bluft nie (Bube setzt nicht) | erster | −1/18 (−0,0556) | 0 |
| Erster Spieler setzt mit dem König nie | erster | −1/18 (−0,0556) | 0 |
| Erster Spieler passt mit dem König nie | erster | −1/18 (−0,0556) | 0 |
| Erster Spieler geht mit der Dame nach Pass–Setzen nie mit | erster | −1/12 (−0,0833) | 1/36 (0,0278) |
| Erster Spieler geht mit der Dame nach Pass–Setzen immer mit | erster | −1/9 (−0,1111) | 1/18 (0,0556) |
| Erster Spieler setzt nur mit dem König | erster | −1/18 (−0,0556) | 0 |
| Erster Spieler setzt im ersten Zug nie | erster | −1/18 (−0,0556) | 0 |

**Einfache Faustregeln** (Kosten gegen die beste Antwort, wenn die Regel auf dem jeweiligen Platz gespielt wird):

| Faustregel | Kosten als erster Spieler | Kosten als zweiter Spieler |
|---|---|---|
| immer setzen und mitgehen | 5/18 (0,2778) | 7/18 (0,3889) |
| immer passen und aufgeben | 17/18 (0,9444) | 19/18 (1,0556) |
| nur mit dem König setzen und mitgehen | 5/18 (0,2778) | 2/9 (0,2222) |
| mit Dame und König setzen und mitgehen | 1/9 (0,1111) | 2/9 (0,2222) |

**Größe und Zeit nach Kartenzahl** (Zeiten einmalig gemessen auf dem Rechner der Messung, plattformabhängig):

| Karten n | Knoten | Sequenzen je Spieler | Normalform | Spielwert | Zeit Sequenzform (s) | Zeit Normalform (s) |
|---|---|---|---|---|---|---|
| 2 | 19 | 9 | 9 × 16 | 0 | 0,005 | 0,004 |
| 3 | 55 | 13 | 27 × 64 | −1/18 (−0,0556) | 0,005 | 0,006 |
| 4 | 109 | 17 | 81 × 256 | −1/24 (−0,0417) | 0,008 | 0,041 |
| 5 | 181 | 21 | 243 × 1.024 | −1/15 (−0,0667) | 0,005 | 0,563 |
| 6 | 271 | 25 | 729 × 4.096 | −11/180 (−0,0611) | 0,005 | 7,448 |
| 7 | 379 | 29 | 2.187 × 16.384 | −0,0714 | 0,007 | – |
| 8 | 505 | 33 | 6.561 × 65.536 | −0,0625 | 0,021 | – |
| 9 | 649 | 37 | 19.683 × 262.144 | −0,0648 | 0,012 | – |
| 10 | 811 | 41 | 59.049 × 1.048.576 | −0,0611 | 0,007 | – |
| 11 | 991 | 45 | 177.147 × 4.194.304 | −0,0636 | 0,045 | – |
| 12 | 1189 | 49 | 531.441 × 16.777.216 | −0,0619 | 0,014 | – |
| 13 | 1405 | 53 | 1.594.323 × 67.108.864 | −0,0641 | 0,071 | – |
| 20 | 3421 | 81 | – | −0,0601 | 0,011 | – |
| 30 | 7831 | 121 | – | −0,0588 | 0,051 | – |
| 50 | 22051 | 201 | – | −0,0576 | 0,045 | – |

**Regret-Verfahren im Kuhn-Spiel mit drei Karten** (größere Lücke der Durchschnittsstrategie gegen den Spielwert; Langzeitreihe, RM bis T = 30 000):

| Verfahren | T = 1 000 | T = 10 000 | größtes T | Steigung T = 100 bis 30 000 | erstmals ≤ 10⁻³ |
|---|---|---|---|---|---|
| CFR (beide Seiten gleichzeitig) | 7,9·10⁻³ | 3,4·10⁻³ | 6,7·10⁻⁴ (T = 300 000) | −0,48 | T = 100 000 (5 500 000 Knoten) |
| CFR abwechselnd | 1,2·10⁻³ | 1,2·10⁻⁴ | 8,8·10⁻⁶ (T = 300 000) | −0,92 | T = 1 125 (123 750 Knoten) |
| CFR abwechselnd mit gekappten Regrets | 6,0·10⁻⁴ | 7,7·10⁻⁵ | 4,3·10⁻⁶ (T = 300 000) | −0,92 | T = 665 (73 150 Knoten) |
| CFR⁺ | 1,3·10⁻⁴ | 1,0·10⁻⁵ | 1,1·10⁻⁶ (T = 300 000) | −0,90 | T = 179 (19 690 Knoten) |
| Discounted CFR | 2,2·10⁻⁴ | 1,6·10⁻⁵ | 7,3·10⁻⁷ (T = 300 000) | −1,01 | T = 233 (25 630 Knoten) |
| Regret Matching (Normalform) | 6,2·10⁻³ | 2,8·10⁻³ | 1,5·10⁻³ (T = 30 000) | −0,49 | nicht erreicht |
| RM⁺ (Normalform) | 2,0·10⁻³ | 6,9·10⁻⁴ | 3,9·10⁻⁴ (T = 30 000) | −0,46 | T = 3 000 (10 368 000 Knoten) |

**Zerlegung des Vorsprungs von CFR⁺** (Kuhn, drei Karten; jede Stufe fügt der vorigen einen Baustein hinzu):

| Stufe | T = 1 000 | T = 10 000 | T = 300 000 | Steigung T = 1 000 bis 300 000 | Faktor zur Vorstufe bei T = 1 000 |
|---|---|---|---|---|---|
| CFR (gleichzeitig) | 7,9·10⁻³ | 3,4·10⁻³ | 6,7·10⁻⁴ | −0,48 | – |
| + Abwechslung der Aktualisierung | 1,2·10⁻³ | 1,2·10⁻⁴ | 8,8·10⁻⁶ | −0,84 | 6,8 |
| + Kappen der Regrets | 6,0·10⁻⁴ | 7,7·10⁻⁵ | 4,3·10⁻⁶ | −0,88 | 1,9 |
| + lineare Mittelung (= CFR⁺) | 1,3·10⁻⁴ | 1,0·10⁻⁵ | 1,1·10⁻⁶ | −0,83 | 4,8 |

**Letzte Iteration** (größere Lücke der zuletzt gespielten Strategie):

| Verfahren | T = 1 000 | T = 10 000 | T = 30 000 | T = 300 000 |
|---|---|---|---|---|
| CFR (beide Seiten gleichzeitig) | 2,8·10⁻¹ | 2,2·10⁻¹ | 2,8·10⁻¹ | 3,9·10⁻¹ |
| CFR abwechselnd | 6,6·10⁻² | 3,7·10⁻² | 2,4·10⁻² | 1,9·10⁻² |
| CFR abwechselnd mit gekappten Regrets | 3,1·10⁻² | 1,1·10⁻² | 1,3·10⁻² | 2,9·10⁻³ |
| CFR⁺ | 3,1·10⁻² | 1,1·10⁻² | 1,3·10⁻² | 2,9·10⁻³ |
| Discounted CFR | 2,1·10⁻² | 1,6·10⁻² | 7,4·10⁻³ | 4,3·10⁻³ |

**Zufallsstart** (zufällige Anfangsregrets, Mittel ± Standardabweichung über vier Zufalls-Seeds; Lücke des Mittels):

| Verfahren | T = 100 | T = 1 000 | T = 10 000 | gleichverteilter Start, T = 10 000 |
|---|---|---|---|---|
| CFR (beide Seiten gleichzeitig) | 3,7·10⁻² ± 6,3·10⁻³ | 1,1·10⁻² ± 1,9·10⁻³ | 3,0·10⁻³ ± 4,8·10⁻⁴ | 3,4·10⁻³ |
| CFR⁺ | 6,8·10⁻³ ± 1,7·10⁻³ | 5,9·10⁻⁴ ± 3,3·10⁻⁴ | 5,4·10⁻⁵ ± 3,4·10⁻⁵ | 1,0·10⁻⁵ |
| Discounted CFR | 2,1·10⁻³ ± 9,4·10⁻⁴ | 1,8·10⁻⁴ ± 1,1·10⁻⁴ | 1,9·10⁻⁵ ± 9,6·10⁻⁶ | 1,6·10⁻⁵ |

**Externes Sampling im Kuhn-Spiel** (vier Zufalls-Seeds):

| Iterationen | besuchte Knoten (Mittel) | Lücke Sampling | kleinster / größter Wert | Lücke CFR⁺ bei gleichem Aufwand |
|---|---|---|---|---|
| 100 | 1 271 | 1,1·10⁻¹ ± 2,2·10⁻² | 9,3·10⁻² / 1,4·10⁻¹ | 3,8·10⁻² |
| 300 | 3 805 | 6,5·10⁻² ± 2,3·10⁻² | 4,3·10⁻² / 8,8·10⁻² | 6,5·10⁻³ |
| 1 000 | 12 644 | 4,3·10⁻² ± 7,7·10⁻³ | 3,6·10⁻² / 5,2·10⁻² | 1,3·10⁻³ |
| 3 000 | 37 848 | 1,6·10⁻² ± 8,2·10⁻³ | 1,1·10⁻² / 2,8·10⁻² | 5,8·10⁻⁴ |
| 10 000 | 125 707 | 1,3·10⁻² ± 3,7·10⁻³ | 8,6·10⁻³ / 1,6·10⁻² | 1,5·10⁻⁴ |
| 30 000 | 378 754 | 6,0·10⁻³ ± 2,0·10⁻³ | 4,2·10⁻³ / 8,5·10⁻³ | 3,4·10⁻⁵ |
| 100 000 | 1 264 471 | 3,7·10⁻³ ± 2,3·10⁻³ | 1,8·10⁻³ / 7,0·10⁻³ | 1,0·10⁻⁵ |

**Leduc, volle Verfahren** (T = 2 000):

| Verfahren | T = 1 000 | T = 2 000 | Steigung T = 100 bis 2 000 | letzte Iteration, T = 2 000 | erstmals ≤ 10⁻³ |
|---|---|---|---|---|---|
| CFR (beide Seiten gleichzeitig) | 4,0·10⁻² | 3,4·10⁻² | −0,60 | 1,5·10⁰ | nicht erreicht |
| CFR⁺ | 3,6·10⁻⁴ | 1,2·10⁻⁴ | −1,71 | 5,4·10⁻³ | T = 665 (2 578 870 Knoten) |
| Discounted CFR | 2,2·10⁻⁴ | 6,6·10⁻⁵ | −1,68 | 8,4·10⁻³ | T = 394 (1 527 932 Knoten) |

**Leduc, externes Sampling** (vier Zufalls-Seeds; Lücke der vollen Verfahren beim letzten Prüfpunkt mit höchstens so vielen besuchten Knoten):

| Iterationen | besuchte Knoten (Mittel) | Lücke Sampling | kleinster / größter Wert | Lücke CFR (beide Seiten gleichzeitig) bei gleichem Aufwand | Lücke CFR⁺ bei gleichem Aufwand | Lücke Discounted CFR bei gleichem Aufwand |
|---|---|---|---|---|---|---|
| 100 | 4 476 | 2,4·10⁰ ± 2,4·10⁻¹ | 2,2·10⁰ / 2,7·10⁰ | weniger als ein Schritt | weniger als ein Schritt | weniger als ein Schritt |
| 300 | 13 167 | 1,7·10⁰ ± 1,4·10⁻¹ | 1,5·10⁰ / 1,9·10⁰ | weniger als ein Schritt | weniger als ein Schritt | weniger als ein Schritt |
| 1 000 | 44 696 | 8,4·10⁻¹ ± 1,9·10⁻¹ | 6,8·10⁻¹ / 1,1·10⁰ | 5,7·10⁻¹ | 7,9·10⁻¹ | 6,6·10⁻¹ |
| 3 000 | 136 045 | 4,1·10⁻¹ ± 7,9·10⁻² | 3,1·10⁻¹ / 5,0·10⁻¹ | 2,7·10⁻¹ | 9,6·10⁻² | 8,9·10⁻² |
| 10 000 | 447 841 | 2,0·10⁻¹ ± 2,4·10⁻² | 1,7·10⁻¹ / 2,2·10⁻¹ | 1,3·10⁻¹ | 1,6·10⁻² | 1,1·10⁻² |
| 30 000 | 1 327 166 | 8,6·10⁻² ± 1,4·10⁻² | 6,7·10⁻² / 9,8·10⁻² | 5,4·10⁻² | 3,1·10⁻³ | 1,2·10⁻³ |
| 100 000 | 4 446 854 | 5,1·10⁻² ± 7,8·10⁻³ | 4,5·10⁻² / 6,2·10⁻² | 3,4·10⁻² | 2,8·10⁻⁴ | 1,8·10⁻⁴ |

**Anmeldung und Kontrolle, Raster** (Anteil riskanter Sendungen *p* × Strafe *s*; *b* = 10, *c* = 2, *g* = 15, *r* = 6):

| Anteil riskant p | Strafe s | Regime | Lügenanteil λ | Kontrollanteil κ | Wert (Euro je Sendung) | alle Wege gleich |
|---|---|---|---|---|---|---|
| 1/50 | 5 | alle lügen | 1 | 0 | 101/10 (10,100) | ja |
| 1/50 | 10 | alle lügen | 1 | 0 | 101/10 (10,100) | ja |
| 1/50 | 20 | alle lügen | 1 | 0 | 101/10 (10,100) | ja |
| 1/50 | 40 | alle lügen | 1 | 0 | 101/10 (10,100) | ja |
| 1/50 | 80 | alle lügen | 1 | 0 | 101/10 (10,100) | ja |
| 1/20 | 5 | alle lügen | 1 | 0 | 41/4 (10,250) | ja |
| 1/20 | 10 | alle lügen | 1 | 0 | 41/4 (10,250) | ja |
| 1/20 | 20 | alle lügen | 1 | 0 | 41/4 (10,250) | ja |
| 1/20 | 40 | gemischt | 38/55 (0,691) | 9/55 (0,164) | 5561/550 (10,111) | ja |
| 1/20 | 80 | gemischt | 2/5 (0,400) | 9/95 (0,095) | 499/50 (9,980) | ja |
| 1/10 | 5 | gemischt | 9/10 (0,900) | 9/20 (0,450) | 1041/100 (10,410) | ja |
| 1/10 | 10 | gemischt | 18/25 (0,720) | 9/25 (0,360) | 1281/125 (10,248) | ja |
| 1/10 | 20 | gemischt | 18/35 (0,514) | 9/35 (0,257) | 1761/175 (10,063) | ja |
| 1/10 | 40 | gemischt | 18/55 (0,327) | 9/55 (0,164) | 2721/275 (9,895) | ja |
| 1/10 | 80 | gemischt | 18/95 (0,189) | 9/95 (0,095) | 4641/475 (9,771) | ja |
| 3/10 | 5 | gemischt | 7/30 (0,233) | 9/20 (0,450) | 943/100 (9,430) | ja |
| 3/10 | 10 | gemischt | 14/75 (0,187) | 9/25 (0,360) | 1163/125 (9,304) | ja |
| 3/10 | 20 | gemischt | 2/15 (0,133) | 9/35 (0,257) | 229/25 (9,160) | ja |
| 3/10 | 40 | gemischt | 14/165 (0,085) | 9/55 (0,164) | 2483/275 (9,029) | ja |
| 3/10 | 80 | gemischt | 14/285 (0,049) | 9/95 (0,095) | 4243/475 (8,933) | ja |
| 1/2 | 5 | gemischt | 1/10 (0,100) | 9/20 (0,450) | 169/20 (8,450) | ja |
| 1/2 | 10 | gemischt | 2/25 (0,080) | 9/25 (0,360) | 209/25 (8,360) | ja |
| 1/2 | 20 | gemischt | 2/35 (0,057) | 9/35 (0,257) | 289/35 (8,257) | ja |
| 1/2 | 40 | gemischt | 2/55 (0,036) | 9/55 (0,164) | 449/55 (8,164) | ja |
| 1/2 | 80 | gemischt | 2/95 (0,021) | 9/95 (0,095) | 769/95 (8,095) | ja |
| 9/10 | 5 | gemischt | 1/90 (0,011) | 9/20 (0,450) | 649/100 (6,490) | ja |
| 9/10 | 10 | gemischt | 2/225 (0,009) | 9/25 (0,360) | 809/125 (6,472) | ja |
| 9/10 | 20 | gemischt | 2/315 (0,006) | 9/35 (0,257) | 1129/175 (6,451) | ja |
| 9/10 | 40 | gemischt | 2/495 (0,004) | 9/55 (0,164) | 1769/275 (6,433) | ja |
| 9/10 | 80 | gemischt | 2/855 (0,002) | 9/95 (0,095) | 3049/475 (6,419) | ja |

**Wirkung der Strafe** (*p* = 3/10, sonst Voreinstellung):

| Strafe s | Lügenanteil λ | Kontrollanteil κ | Wert (Euro je Sendung) | erwartete Kontrollen je Sendung |
|---|---|---|---|---|
| 5 | 0,233 | 0,450 | 9,43 | 0,346 |
| 10 | 0,187 | 0,360 | 9,30 | 0,272 |
| 20 | 0,133 | 0,257 | 9,16 | 0,190 |
| 40 | 0,085 | 0,164 | 9,03 | 0,119 |
| 80 | 0,049 | 0,095 | 8,93 | 0,068 |
| 160 | 0,027 | 0,051 | 8,87 | 0,036 |

Weitere Befunde: Der Kontrollanteil *κ* hängt im Standardfall (*s* = 20) nicht an *p* (9/35 für *p* = 1/10 bis 9/10, jeweils im gemischten Regime), die Lügenrate *λ* schon. Der Spielwert hängt nicht von der Gebühr *f* ab (*f* = 0, 1, 3, 5 geben alle 229/25 Euro je Sendung, bei sonst den Voreinstellungen). Das Mittel fällt nicht monoton: die Lücke von CFR⁺ steigt an 14 von 48 aufeinanderfolgenden Prüfpunktpaaren der Langzeitreihe (Discounted CFR 12, abwechselndes CFR 9, mit gekappten Regrets 2).

## Ehrliche Grenzen

**Annahmen**
- Zwei Spieler, Nullsumme: was der eine gewinnt, verliert der andere. Eigennutz und Nullsumme sind Modellannahmen; Allgemeinsummenspiele und mehr als zwei Spieler sind nicht gerechnet.
- Perfektes Erinnern in allen drei Spielen; die Sequenzform setzt es voraus.
- Kuhn-Poker mit n Karten (Regeln wie in der Erklärung), Einsätze in Einheiten des Anfangseinsatzes. Leduc-Poker mit Rangabstraktion (drei Ränge, je zweimal, Einsatzgrößen 2 und 4, höchstens zwei Erhöhungen je Runde); die Regeln stammen aus dem Gedächtnis, die Quelle ist nicht eingesehen.
- Discounted CFR rechnet mit den Parametern (3/2, 0, 2), ebenfalls aus dem Gedächtnis; sie sind nicht in der Quelle geprüft.
- „Anmeldung und Kontrolle“ (Reiter 4) ist ein konstruiertes Nullsummenmodell: die Entschädigung bei einer Kontrolle ist so gewählt, dass die Auszahlungen sich zu null addieren. Es ist kein gemessenes Modell einer Zollkontrolle oder eines Verladers.

**Grenzen**
- Nur kleine Bäume und ohne Abstraktion: Kuhn bis 13 Karten (die Normalform nur bis 5 Karten aufgestellt), Leduc mit 1 939 Knoten. Ob externes Sampling bei größeren Bäumen Aufwand spart, ist nicht gemessen; in Leduc ist es nach besuchten Knoten schlechter als die vollen Verfahren.
- Keine Teilspiel-Lösung, keine Abstraktion, kein Training großer Spiele: Libratus, Pluribus und ReBeL sind nur Einordnung und nicht nachgebaut.
- Die Aussagen zu den Verfahren gelten für diese Implementierungen auf Kuhn (drei Karten) und Leduc, nicht für die Verfahren allgemein.
- Der Rechenweg der Gleichgewichtsmenge ist nur für Kuhn mit drei Karten gezeigt; andere Kartenzahlen sind nur auf ihren Spielwert geprüft.
- Zeiten sind Einmalmessungen auf dem Rechner der Messung und hängen von Plattform und Last ab.

**Bekannte Probleme und Unsicherheiten**
- Das Mittel der Regret-Verfahren fällt nicht monoton; an einzelnen Prüfpunkten kann die Lücke steigen. Steigungen sind Ausgleichsgeraden über eine Reihe von Prüfpunkten, keine Konvergenzraten.
- Alle Quellen (Kuhn 1950, Koller, Megiddo und von Stengel 1994, Zinkevich u. a. 2007, Burch u. a. 2019, Brown und Sandholm 2019, Southey u. a. 2005) sind nur nach Abstract oder Auszug eingeordnet, nicht im Volltext geprüft.
- Die Oberfläche ist im Browser nur stichprobenartig geprüft, nicht auf allen Geräten.

## Literatur

Alle Quellen sind nur nach Abstract oder Auszug eingeordnet, **nicht im Volltext geprüft**: Kuhn 1950, *A simplified two-person poker* (Sekundärauszüge: [Wikipedia](https://en.wikipedia.org/wiki/Kuhn_poker), [Dartmouth-Abschlussarbeit](https://math.dartmouth.edu/theses/undergrad/2014/Miao-thesis.pdf)); Koller, Megiddo, von Stengel, STOC 1994 (Sequenzform, LP linear in der Baumgröße; laut Sekundärauszug, [Publikationsliste](https://robotics.stanford.edu/~koller/papers/papers.html)); Burch, Moravčík, Schmid, JAIR 64 (2019), [Revisiting CFR⁺ and Alternating Updates](https://jair.org/index.php/jair/article/view/11370) (laut Abstract: korrigierter Beweis, Abwechslung nur im Titel); Brown und Sandholm, [Solving Imperfect-Information Games via Discounted Regret Minimization](https://arxiv.org/abs/1809.04040) (laut Abstract: Abzinsung früher Regrets, eine Variante schlägt CFR⁺ in allen getesteten Spielen; die Parameter 3/2, 0, 2 sind nicht bestätigt); Leduc: Southey u. a. 2005 ([AAAI05-123](https://cdn.aaai.org/AAAI/2005/AAAI05-123.pdf), nur als Fundstelle, nicht gelesen). Aus dem Gedächtnis eingeordnet: Zinkevich u. a. 2007 (CFR), Lanctot u. a. 2009 (Sampling), die Leduc-Regeln, Libratus, Pluribus und ReBeL. Die Lösungen, die geschlossene Form der Anmeldung und alle Messungen sind selbst gerechnet.

## Tests

**194 Tests**, Laufzeit rund 7 Minuten seriell auf Windows mit Python 3.14 (den größten Teil brauchen die AppTest-Dateien; die Zahl steht in der Suite fest, die Laufzeit ist einmal gemessen: 400 s). Linux-CI (Python 3.12) ist noch nicht gelaufen. Zusammensetzung:

- **Orakel (`tests/test_oracle_verdeckte_information.py`):** Spielwert für Kuhn n = 2 und 3 auf vier Wegen (Sequenzform in Brüchen, Normalform in Brüchen, HiGHS auf der vollen 64 × 64-Normalform, HiGHS auf der Sequenzform); n = 4, 5; Normalform über Realisierungspläne gegen den direkten Baumdurchlauf; reduzierte Strategien als verschiedene Zeilen und Spalten der vollen Matrix; beste Antwort gegen die Aufzählung aller reinen Strategien (Kuhn n = 2, 3 und Anmeldung, je 12 Zufallsprofile); Familie in Brüchen; Gleichgewichtsmenge; 13 Verbote gegen die eingeschränkte Normalform; Faustregeln; Raster der Anmeldung (30 Zellen) und Zusatzzeilen; Leduc-LP-Strategien mit Lücke unter 10⁻¹⁰.
- **Einheiten an Mini-Instanzen von Hand (`test_units.py`):** Kuhn mit zwei Karten (19 Knoten, 9 Sequenzen, 9 × 16 Strategien, Gleichverteilung 1/8, erste CFR-Iteration (1/8, −1/8)), Leduc-Zählung (1 116 Endknoten) und -Auszahlungen, Anmeldung (Standard 229/25), Regret-Einheiten, gesampelter Durchlauf mit festem Strom, exakter Simplex.
- **Eigenschaftstests und Zweige (`test_properties.py`):** Skalieren aller Auszahlungen, Karten umbenennen und Rangfolge umkehren, Nebenbedingungen der Realisierungspläne, Summe der Spielwerte 0, „in der Familie“ gleich „Lücke 0“ auf 300 zufälligen und strukturierten Wahlen, Unabhängigkeit vom Hash-Seed des Prozesses, jedes Verfahren weicht von jedem anderen ab, Zufallsstart ≠ gleichverteilt, Sampling je Seed, alle drei Regime der Anmeldung.
- **Randfälle (`test_edge_cases.py`):** zwei Karten, Gleichstand der besten Antwort, Schwelle *p* = μ\* inklusive, *g* = *r*, alle 64 Ecken der Anmeldungs-Regler, Formeln 4n + 1 und 3ⁿ · 4ⁿ für n = 2 bis 13.
- **Verdikte und Presets (`test_verdicts.py`, `test_presets.py`):** Schwellen und jede Zahl im Text an Handwerten; je Preset die angekündigte Wirkung und jede Zahl der Preset-Hilfen.
- **Messreihen (`test_measurements.py`):** Erzeuger-Hash, Summen in sich stimmig, Proben aus allen Auftragsarten neu gerechnet (Gleichgewichtsmenge und Verbote vollständig).
- **Claims (`test_claims.py`):** jede Zahl der README; die Tabellen werden mit denselben Zeilenbauern der App erzeugt und als Text in der README gesucht; Hypothesenzeilen H1 bis H12.
- **App (`test_app.py`, `test_layout.py`, `test_footer.py`, `test_runtime_imports.py`, `test_copies.py`):** jeder Knopf, jeder Regler an beiden Rändern, alle Minima und alle Maxima zusammen, Leduc auf Knopfdruck am Maximum, PDF, Hervorhebung des aktiven Presets, Footer, Laufzeit-Importe, Kopietest des Zufallsgenerators.

Ein Mutationstest läuft für diese Demo nicht (Entscheidung des Betreibers, 2026-10-28).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Hauptansicht, vier Reiter, Annahmen, Formeln, PDF |
| `data/tables.json` | vorgerechnete Messreihen mit Erzeuger-Hash |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; scipy rechnet das LP in Gleitkomma) |
| `tools/make_grid.py` | rechnet `data/tables.json` neu (bis zu 6 Prozesse) |
| `vdi_anmeldung.py` | Anmeldung und Kontrolle: geschlossene Form, Gleichgewichtsprofil |
| `vdi_cfr.py` | Regret Matching, CFR-Durchlauf, Kappen, Abzinsen, externes Sampling, Löser |
| `vdi_constants.py` | Regler-Grenzen, Farben, Presets |
| `vdi_evaluation.py` | Ansichten, Zeilenbauer der Tabellen, Verdikte als reine Funktionen |
| `vdi_exact.py` | exakter Simplex in Brüchen, exakte Sequenzform-LPs, Bereiche |
| `vdi_experiments.py` | Aufträge und Zusammenbau der Messreihen, Erzeuger-Hash |
| `vdi_games.py` | Kuhn, Leduc, Anmeldung als Spielbeschreibung |
| `vdi_kuhn.py` | Familie, Verbote, Faustregeln, Gleichgewichtsbereiche |
| `vdi_layout.py` | Fester Kopf (Stylesheet) |
| `vdi_normal.py` | Normalform, reduzierte Strategien, Regret Matching auf der Matrix |
| `vdi_pdf_export.py` | PDF-Export (fpdf2) |
| `vdi_presets.py` | Permalink (Begrenzen), Presets, Zufalls-Seed-Button |
| `vdi_rng.py` | wörtliche Kopie von `ab-test-demo/abt_rng.py` (SplitMix64) |
| `vdi_runs.py` | Läufe mit Prüfpunkten, Steigungen, Zufallsströme |
| `vdi_scenario.py` | Einstellungen, gebaute Spiele |
| `vdi_seqform.py` | Sequenzform: Sequenzen, Matrizen, LP, Plan ↔ Verhaltensstrategie |
| `vdi_strategy.py` | Wert eines Profils, beste Antwort, Ausnutzbarkeit |
| `vdi_texts.py` | Texte der App (Einleitung, Annahmen, Formeln) |
| `vdi_tree.py` | Spielbaum, Informationsmengen, perfektes Erinnern |
| `vdi_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Mini-Instanzen, Orakel, Einheiten, Eigenschaften, Randfälle, Verdikte, Presets, Messreihen, Claims, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Größere Bäume, Abstraktion, Teilspiel-Lösung:** ob externes Sampling bei größeren Bäumen Aufwand spart, ist nicht gemessen; Libratus, Pluribus und ReBeL sind nur Einordnung.
- **Allgemeinsummenspiele und mehr als zwei Spieler:** nicht gerechnet; die Sequenzform-Zerlegung gilt hier für Nullsumme.
- **Echte Daten:** keine; Karten, Einsätze, Kosten und die konstruierte Entschädigung in Reiter 4 sind Annahmen.
- **Kuhn-Gleichgewichtsmenge für andere Kartenzahlen als drei:** nur der Spielwert ist geprüft.
- **Quellen im Volltext:** nicht gelesen (Abschnitt „Literatur“).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Messreihen neu rechnen (nur nach Änderung an den Quelldateien des Hashes): `python tools/make_grid.py`.

Gebaut mit Streamlit, Plotly, NumPy, SciPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Regeln setzen, verhandeln, kontrollieren](https://sebastianhanisch.net/konzepte-verhandeln.html).
