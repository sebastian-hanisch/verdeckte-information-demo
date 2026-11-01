"""Spielbaum mit Informationsmengen: aus einer Spielbeschreibung (vdi_games) den Baum in Vorordnung bauen und perfektes Erinnern prüfen.

Knoten sind ganze Zahlen 0 .. n−1; jedes Kind hat einen größeren Index als sein Elternknoten (Vorordnung), die Wurzel ist 0. Je Spieler werden die
Informationsmengen nummeriert; zwei Knoten gehören zur selben Informationsmenge, wenn der Spieler sie nicht unterscheiden kann (gleicher `infokey`)."""

from fractions import Fraction as Fr


class Tree:
    """Flacher Spielbaum: kind[h] in {c, p, t}, player[h], acts[h] (Bezeichnungen), kids[h], prob[h] (Brüche am Zufallsknoten), info[h] (Informationsmenge des Spielers am Zug),
    pay[h] (Bruch am Endknoten, Sicht von Spieler 0), depth[h], parent[h]; je Spieler ikeys (Schlüssel → Nummer), iacts, inodes (Knoten der Menge), ilist (Schlüssel)."""

    def __init__(self):
        self.kind, self.player, self.acts, self.kids, self.prob = [], [], [], [], []
        self.info, self.pay, self.depth, self.parent = [], [], [], []
        self.ikeys = [{}, {}]
        self.iacts = [[], []]
        self.inodes = [[], []]
        self.ilist = [[], []]

    def finish(self):
        self.n = len(self.kind)
        self.nterm = sum(1 for k in self.kind if k == "t")
        self.ninfo = [len(self.iacts[0]), len(self.iacts[1])]
        self.nact = [[len(a) for a in self.iacts[0]], [len(a) for a in self.iacts[1]]]
        self.probf = [[float(x) for x in pr] if pr else None for pr in self.prob]
        self.payf = [float(x) if x is not None else None for x in self.pay]


def build(game) -> Tree:
    """Baum der Spielbeschreibung. Hält die Aktionen jeder Informationsmenge für gleich (sonst AssertionError: die Menge wäre keine)."""
    T = Tree()

    def rec(s, d, par):
        h = len(T.kind)
        k = game.kind(s)
        T.kind.append(k)
        T.player.append(-1)
        T.acts.append(None)
        T.kids.append([])
        T.prob.append(None)
        T.info.append(-1)
        T.pay.append(None)
        T.depth.append(d)
        T.parent.append(par)
        if k == "t":
            T.pay[h] = Fr(game.payoff0(s))
        elif k == "c":
            outs = game.chance(s)
            T.acts[h] = [o[0] for o in outs]
            T.prob[h] = [o[1] for o in outs]
            assert sum(T.prob[h]) == 1
            for _, _, ns in outs:
                T.kids[h].append(rec(ns, d + 1, h))
        else:
            p = game.player(s)
            T.player[h] = p
            acts = list(game.actions(s))
            key = game.infokey(s, p)
            if key not in T.ikeys[p]:
                T.ikeys[p][key] = len(T.iacts[p])
                T.iacts[p].append(acts)
                T.inodes[p].append([])
                T.ilist[p].append(key)
            i = T.ikeys[p][key]
            assert T.iacts[p][i] == acts, (key, acts)
            T.info[h] = i
            T.inodes[p][i].append(h)
            T.acts[h] = acts
            for a in acts:
                T.kids[h].append(rec(game.child(s, a), d + 1, h))
        return h

    rec(game.root(), 0, -1)
    T.finish()
    return T


def own_history(T: Tree, h: int, p: int) -> tuple:
    """Die Folge (Informationsmenge, Aktionsnummer) der Entscheidungen von Spieler p auf dem Weg zur Wurzel bis zum Knoten h (was p selbst getan hat)."""
    hist = []
    c = h
    while T.parent[c] != -1:
        q = T.parent[c]
        if T.kind[q] == "p" and T.player[q] == p:
            hist.append((T.info[q], T.kids[q].index(c)))
        c = q
    return tuple(reversed(hist))


def perfect_recall(T: Tree) -> bool:
    """Perfektes Erinnern: alle Knoten einer Informationsmenge haben dieselbe eigene Vorgeschichte (dieselben eigenen Entscheidungen, in derselben Reihenfolge)."""
    for p in (0, 1):
        for nodes in T.inodes[p]:
            first = own_history(T, nodes[0], p)
            if any(own_history(T, h, p) != first for h in nodes[1:]):
                return False
    return True
