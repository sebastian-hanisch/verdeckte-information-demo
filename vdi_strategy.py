"""Bewertung von Strategien auf dem Baum: Wert eines Profils, beste Antwort und Ausnutzbarkeit (Lücke zum Spielwert).

Eine Verhaltensstrategie ist `st[p][i][a]` = Wahrscheinlichkeit, in Informationsmenge i von Spieler p die Aktion a zu wählen. Alle Funktionen rechnen mit dem Zahlentyp der Strategie
(Brüche bleiben Brüche, Gleitkomma bleibt Gleitkomma). Die beste Antwort kommt aus einem Baumdurchlauf, unabhängig von jedem LP und von jedem Regret-Verfahren."""

from fractions import Fraction as Fr


def uniform_strategy(T, exact: bool = True):
    """Gleichverteilung in jeder Informationsmenge (Brüche oder Gleitkomma)."""
    one = Fr(1) if exact else 1.0
    return [[[one / n for _ in range(n)] for n in T.nact[p]] for p in (0, 1)]


def _numbers(T, st):
    """(Auszahlungen, Zufallswahrscheinlichkeiten) im Zahlentyp der Strategie: Gleitkomma-Strategien rechnen mit den Gleitkomma-Tabellen des Baums (schneller)."""
    if isinstance(st[0][0][0], float):
        return T.payf, T.probf
    return T.pay, T.prob


def profile_value(T, st):
    """Erwartete Auszahlung an Spieler 0, wenn beide Seiten die Verhaltensstrategien `st` spielen (Rückwärtsdurchlauf in Vorordnung)."""
    pay, prob = _numbers(T, st)
    val = [None] * T.n
    for h in range(T.n - 1, -1, -1):
        k = T.kind[h]
        if k == "t":
            val[h] = pay[h]
        elif k == "c":
            val[h] = sum(pr * val[c] for pr, c in zip(prob[h], T.kids[h]))
        else:
            s = st[T.player[h]][T.info[h]]
            val[h] = sum(s[a] * val[c] for a, c in enumerate(T.kids[h]))
    return val[0]


def reach_of_others(T, st, p):
    """Erreichungswahrscheinlichkeit jedes Knotens ohne die eigenen Entscheidungen von Spieler p (nur Zufall und der andere Spieler zählen)."""
    q = 1 - p
    _, prob = _numbers(T, st)
    reach = [None] * T.n
    reach[0] = 1
    for h in range(T.n):
        k = T.kind[h]
        if k == "t":
            continue
        for a, c in enumerate(T.kids[h]):
            if k == "c":
                reach[c] = reach[h] * prob[h][a]
            elif T.player[h] == q:
                reach[c] = reach[h] * st[q][T.info[h]][a]
            else:
                reach[c] = reach[h]
    return reach


def info_depths_uniform(T) -> bool:
    """Liegen alle Knoten jeder Informationsmenge in derselben Tiefe? Die beste Antwort von unten nach oben verlangt es (gilt für Kuhn, Leduc und Anmeldung)."""
    return all(len({T.depth[h] for h in nodes}) == 1 for p in (0, 1) for nodes in T.inodes[p])


def best_response(T, st, p):
    """Beste Antwort von Spieler p auf die Strategie des anderen: (Wert aus Sicht von p, Entscheidung je Informationsmenge).

    Wert in Informationsmengen: die Aktion mit dem größten kontrafaktischen Wert (Summe über die Knoten der Menge, gewichtet mit der Erreichungswahrscheinlichkeit ohne die eigene
    Entscheidung); bei Gleichstand die erste. Tiefe von unten nach oben."""
    assert info_depths_uniform(T)
    q = 1 - p
    sgn = 1 if p == 0 else -1
    pay, prob = _numbers(T, st)
    reach = reach_of_others(T, st, p)
    maxd = max(T.depth)
    bydepth = [[] for _ in range(maxd + 1)]
    for h in range(T.n):
        bydepth[T.depth[h]].append(h)
    val = [None] * T.n
    choice = [None] * T.ninfo[p]
    for d in range(maxd, -1, -1):
        done = set()
        for h in bydepth[d]:
            k = T.kind[h]
            if k == "t":
                val[h] = sgn * pay[h]
            elif k == "c":
                val[h] = sum(pr * val[c] for pr, c in zip(prob[h], T.kids[h]))
            elif T.player[h] == q:
                s = st[q][T.info[h]]
                val[h] = sum(s[a] * val[c] for a, c in enumerate(T.kids[h]))
            else:
                i = T.info[h]
                if i not in done:
                    done.add(i)
                    na = T.nact[p][i]
                    cf = [sum(reach[hh] * val[T.kids[hh][a]] for hh in T.inodes[p][i]) for a in range(na)]
                    choice[i] = max(range(na), key=lambda a: cf[a])
                val[h] = val[T.kids[h][choice[i]]]
    return val[0], choice


def exploitability(T, st, v0):
    """Lücken beider Seiten gegenüber dem Spielwert v0 (an Spieler 0): (Lücke 0, Lücke 1, Summe der besten Antworten).

    Lücke 0 = Wert der besten Antwort von Spieler 0 minus v0, Lücke 1 = Wert der besten Antwort von Spieler 1 plus v0 (beide ≥ 0 bei richtigem v0); die Summe BR0 + BR1 braucht v0 nicht."""
    b0, _ = best_response(T, st, 0)
    b1, _ = best_response(T, st, 1)
    return b0 - v0, b1 + v0, b0 + b1


def max_gap(T, st, v0):
    """Die größere der beiden Lücken (so wird die Genauigkeit eines Näherungsgleichgewichts in der Demo gemeldet)."""
    g0, g1, _ = exploitability(T, st, v0)
    return max(g0, g1)
