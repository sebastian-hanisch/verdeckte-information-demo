"""Texte der App: Einleitung, Erklärtexte, Annahmen und Formeln. Befundzahlen stehen hier nicht (sie kommen aus der Rechnung oder stehen in tests/test_claims.py)."""

INTRO = """
**Stück der Linie „Regeln setzen, verhandeln, kontrollieren“.** Wie spielt man, wenn man den **Zustand des anderen nicht sieht** und die **Züge nacheinander** kommen? Das Lehrspiel ist **Kuhn-Poker**: zwei Spieler,
drei Karten (Bube, Dame, König), jeder zahlt 1 ein und sieht nur die eigene Karte. Es ist ausdrücklich **kein Logistikspiel**, sondern das kleinste Spiel, an dem sich das Problem zeigen lässt. Die Demo rechnet,
wie man es **ohne die ausgeschriebene Normalform** löst (Sequenzform: ein lineares Programm, das mit dem Baum wächst), wie das Gleichgewicht aussieht (eine ganze Familie, und Bluffen ist für die beiden Spieler nicht gleich nötig),
und wie schnell die Regret-Verfahren (CFR, CFR⁺, Discounted CFR, Sampling) es auf dem Baum finden. Sie setzt dort an, wo `nullsummenspiel-demo` seine Grenze nennt: dort ziehen beide gleichzeitig und kennen die Matrix;
`minimax-demo` sucht in Bäumen mit vollständiger Information. Reiter 4 ist ein **konstruiertes** Nullsummenmodell mit Logistikbezug (Anmeldung und Kontrolle). Karten, Regeln, Einsätze, Kosten und Eigennutz sind
**Modellannahmen**, keine Aussagen über echte Spieler oder Betriebe. Unten stehen Erklärtabelle, die Annahmen („🚧 Wo die Annahmen enden“) und die Formeln („📐“).
"""

EXPLAINER = """
1. Jeder Spieler zahlt 1 ein und bekommt eine **andere** Karte, gleichverteilt. Der erste Spieler passt oder setzt (1 mehr). Nach einem Pass darf der zweite passen (Vergleich der Karten, höhere Karte gewinnt 1) oder setzen;
   setzt er, entscheidet der erste zwischen Aufgeben (verliert 1) und Mitgehen. Nach einem Setzen des ersten gibt der zweite auf (der erste gewinnt 1) oder geht mit (höhere Karte gewinnt 2).
2. Was ein Spieler weiß, ist seine Karte und der bisherige Verlauf: das ist seine **Informationsmenge**. Knoten, die er nicht unterscheiden kann (die andere Karte ist unbekannt), liegen in derselben Menge. Bei drei Karten
   hat jede Menge zwei Knoten; bei **zwei** Karten verrät die eigene Karte die des anderen, jede Menge hat nur einen Knoten.
3. Eine **Verhaltensstrategie** sagt für jede Informationsmenge, mit welcher Wahrscheinlichkeit welche Aktion gespielt wird. Die **Ausnutzbarkeit** (hier „Lücke“) misst, wie viel ein Gegner mit der besten Antwort mehr bekommt als im Gleichgewicht;
   sie wird durch einen Durchlauf des Baums berechnet, unabhängig von jedem Lösungsverfahren.
4. Die **Normalform** (alle reinen Strategien gegeneinander) wächst mit der Kartenzahl exponentiell. Die **Sequenzform** beschreibt eine Strategie durch die Wahrscheinlichkeit jeder Folge eigener Entscheidungen
   (**Realisierungsplan**); Spielwert und Gleichgewicht sind dort ein lineares Programm, dessen Größe mit dem Baum wächst.
5. **CFR** (Counterfactual Regret Minimization) bewertet in jeder Informationsmenge, wie viel besser eine Aktion gewesen wäre (kontrafaktischer Wert, gewichtet mit der Wahrscheinlichkeit, dass der Gegner und der Zufall sie dorthin führen),
   und spielt künftig die Aktionen im Verhältnis ihrer positiven Regrets. Das **Mittel** über alle Schritte nähert sich dem Gleichgewicht, die **letzte Iteration** nicht unbedingt.

Jede Zahl der Anzeige kommt aus dieser Rechnung. Das Mini-Spiel mit zwei Karten ist von Hand gerechnet und in den Tests nachgeprüft.
"""

CONTROLS_TABLE = """
| Begriff / Regler | Bedeutung |
|---|---|
| **Informationsmenge** | Alle Knoten, die ein Spieler nicht unterscheiden kann (gleiche eigene Karte, gleicher sichtbarer Verlauf). Er muss in allen dieselbe Entscheidung treffen. |
| **Perfektes Erinnern** | Ein Spieler vergisst nichts: alle Knoten einer Informationsmenge haben dieselben eigenen Entscheidungen hinter sich. Die Sequenzform setzt es voraus (der Test prüft es für alle drei Spiele). |
| **Verhaltensstrategie** | Je Informationsmenge eine Wahrscheinlichkeit für jede Aktion. |
| **Sequenz, Realisierungsplan** | Folge eigener Entscheidungen; der Plan gibt jeder Sequenz die Wahrscheinlichkeit, mit der sie gespielt wird, wenn die anderen mitspielen. |
| **Kontrafaktischer Wert, Regret** | Wert einer Aktion in einer Informationsmenge, gewichtet mit der Wahrscheinlichkeit, dass Gegner und Zufall dorthin führen; Regret = Wert der Aktion minus Wert der Menge, über die Schritte summiert. |
| **Ausnutzbarkeit (Lücke)** | Was die beste Antwort des Gegners über den Spielwert hinaus gewinnt (Einsätze je Hand). Beim Gleichgewicht 0. |
| **Mittel / letzte Iteration** | Durchschnitt aller bisherigen Strategien (konvergiert) gegen die zuletzt gespielte Strategie (schwankt, bei CFR ohne Konvergenz). |
| **Strategieregler (Zwölftel)** | Reiter 1, Kuhn mit drei Karten. Erster Spieler: Setzen mit dem Buben, Setzen mit dem König im ersten Zug, Mitgehen mit der Dame nach Pass und Setzen. Zweiter Spieler: Setzen mit dem Buben nach einem Pass (Bluff), Mitgehen mit der Dame gegen ein Setzen. Die übrigen Entscheidungen sind fest wie in der Gleichgewichtsfamilie. |
| **Karten n** | Reiter 2: Kartenzahl des Kuhn-Spiels (2 bis 13). Reiter 3 hat eine eigene Kartenzahl (2 bis 6). |
| **Schritte, Start, Zufalls-Seed** | Reiter 3: Zahl der Durchläufe; gleichverteilter Start oder zufällige Anfangsregrets (Zufalls-Seed). Leduc und Sampling laufen auf Knopfdruck. |
| **b, c, g, s, r, p** | Reiter 4: Wert einer Sendung in Ordnung, Entschädigung bei Kontrolle, Gewinn einer unbemerkten riskanten Sendung, Strafe, Nutzen der ehrlichen Meldung, Anteil riskanter Sendungen. |
"""

ASSUMPTIONS_MARKDOWN = """
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
"""

MATH_MARKDOWN = r"""
**Lesehilfe.** Gegeben: ein Spielbaum mit Zufallsknoten, zwei Spielern und Informationsmengen. Gesucht: Strategien, die gegen die beste Antwort des Gegners so wenig wie möglich verlieren (Spielwert und Gleichgewicht eines
Zwei-Personen-Nullsummenspiels).

| Symbol | Bedeutung |
|---|---|
| *σ*(*I*, *a*) | Wahrscheinlichkeit der Aktion *a* in der Informationsmenge *I* (Verhaltensstrategie) |
| *x*, *y* | Realisierungspläne des ersten und zweiten Spielers (eine Zahl je Sequenz) |
| *E*, *F*, *e*, *f* | Nebenbedingungen der Pläne: *Ex* = *e*, *Fy* = *f* |
| *A* | Auszahlungsmatrix der Sequenzen (Zeilen: erster Spieler) |
| *v* | Spielwert an den ersten Spieler |
| *R*ᵀ(*I*, *a*) | aufsummierter Regret der Aktion *a* in *I* nach *T* Schritten |
| *π*₋ᵢ | Erreichungswahrscheinlichkeit durch Gegner und Zufall |

Realisierungsplan: die Wahrscheinlichkeit einer Sequenz ist das Produkt der eigenen Aktionswahrscheinlichkeiten; umgekehrt ist die Verhaltensstrategie der Quotient.

$$x(I,a)=x(\mathrm{par}(I))\cdot\sigma(I,a),\qquad \sigma(I,a)=\frac{x(I,a)}{x(\mathrm{par}(I))},\qquad Ex=e$$

Spielwert als lineares Programm (Sequenzform): die Dualvariable *q* drückt den besten Wert des Gegners aus, *q*₀ ist der garantierte Wert.

$$v=\max_{x\ge 0,\ q}\ q_0\quad\text{unter}\quad Ex=e,\qquad F^{\top}q\ \le\ A^{\top}x$$

Größe: das Programm hat so viele Variablen wie Sequenzen und Informationsmengen, die Normalform so viele Einträge wie das Produkt der reinen Strategien. Für Kuhn mit *n* Karten gilt

$$\#\text{Sequenzen}=4n+1\ \text{je Spieler},\qquad \#\text{reine Strategien}=3^{n}\ \text{und}\ 4^{n},\qquad \#\text{Einträge der Normalform}=12^{n}$$

Ausnutzbarkeit eines Profils (σ₁, σ₂): Wert der besten Antwort beider Seiten gegen den Spielwert *v* (an den ersten Spieler); ε₁ ist die Lücke der Strategie des ersten Spielers, ε₂ die des zweiten.

$$\varepsilon_1=\mathrm{BR}_2+v,\qquad \varepsilon_2=\mathrm{BR}_1-v,\qquad \mathrm{BR}_1=\max_{\sigma_1'}u(\sigma_1',\sigma_2),\quad \mathrm{BR}_2=\max_{\sigma_2'}\big(-u(\sigma_1,\sigma_2')\big),\qquad \varepsilon_1+\varepsilon_2=\mathrm{BR}_1+\mathrm{BR}_2$$

Kontrafaktischer Wert und Regret in der Informationsmenge *I* des Spielers *i* (Wert *u*ᵢ aus Sicht des Spielers, *π*₋ᵢ Erreichungswahrscheinlichkeit durch Gegner und Zufall):

$$v_i(I,a)=\sum_{h\in I}\pi_{-i}(h)\,u_i(h\cdot a),\qquad R^{T}(I,a)=\sum_{t=1}^{T}\big(v_i^{t}(I,a)-v_i^{t}(I)\big)$$

Regret Matching: die Strategie des nächsten Schritts ist proportional zu den positiven Regrets (gleichverteilt, wenn keiner positiv ist). CFR⁺ kappt zusätzlich die Regrets bei 0, aktualisiert die Spieler abwechselnd und mittelt linear:

$$\sigma^{T+1}(I,a)=\frac{\max(R^{T}(I,a),0)}{\sum_{b}\max(R^{T}(I,b),0)},\qquad R^{T+1}_{+}(I,a)=\max\big(R^{T}_{+}(I,a)+r^{T+1}(I,a),\,0\big),\qquad \bar\sigma=\frac{\sum_t t\,\pi_i^{t}\sigma^{t}}{\sum_t t\,\pi_i^{t}}$$

Discounted CFR zinst positive Regrets mit *t*^α/(*t*^α + 1), negative mit *t*^β/(*t*^β + 1) und die Strategiesumme mit ((*t* − 1)/*t*)^γ ab (hier (α, β, γ) = (3/2, 0, 2), aus dem Gedächtnis):

$$R^{t}(I,a)\leftarrow R^{t}(I,a)\cdot\begin{cases}\dfrac{t^{\alpha}}{t^{\alpha}+1}&R^{t}(I,a)>0\\[2mm]\dfrac{t^{\beta}}{t^{\beta}+1}&\text{sonst}\end{cases},\qquad \bar S^{t}\leftarrow \bar S^{t}\cdot\Big(\frac{t-1}{t}\Big)^{\gamma}$$

Anmeldung und Kontrolle (konstruiertes Nullsummenmodell): Schwelle und Gleichgewicht in geschlossener Form (Indifferenzbedingungen, nachgerechnet gegen das LP in Brüchen); *λ* ist der Anteil riskanter Sendungen, die „sauber“ melden, *κ* der Kontrollanteil nach „sauber“.

$$\mu^{*}=\frac{c}{c+g+s},\qquad p>\mu^{*},\ g>r:\quad \lambda=\frac{c\,(1-p)}{p\,(g+s)},\quad \kappa=\frac{g-r}{g+s},\quad v=(1-p)(b+c\kappa)+p\,r$$

**Quellen** (laut Abstract oder Auszug eingeordnet, nicht im Volltext geprüft): Kuhn 1950, *A simplified two-person poker* (Sekundärauszüge: Wikipedia, Dartmouth-Abschlussarbeit); Koller, Megiddo, von Stengel, STOC 1994 (Sequenzform; laut Sekundärauszug);
Burch, Moravčík, Schmid, *Revisiting CFR⁺ and Alternating Updates*, JAIR 64 (2019); Brown und Sandholm, *Solving Imperfect-Information Games via Discounted Regret Minimization*, arXiv 1809.04040; Southey u. a. 2005 (Leduc, nur als Fundstelle).
Zinkevich u. a. 2007 (CFR) und Lanctot u. a. 2009 (Sampling) sind aus dem Gedächtnis eingeordnet. Die Befunde der Demo (Gleichgewichtsmenge, Verbote, Zerlegung des Vorsprungs von CFR⁺, Sampling in Leduc, Anmeldung) sind selbst gerechnet und gemessen, nicht als Zitate übernommen.
"""
