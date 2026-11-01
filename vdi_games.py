"""Die Spiele: Kuhn-Poker mit n Karten, Leduc-Poker (Rangabstraktion) und das Modell „Anmeldung und Kontrolle“.

Gemeinsame Schnittstelle (reine Beschreibung, kein Zustand): `root()`, `kind(s)` (c = Zufall, p = Spieler am Zug, t = Ende), `chance(s)` (Liste aus Bezeichnung,
Wahrscheinlichkeit, Folgezustand), `player(s)`, `actions(s)`, `child(s, a)`, `infokey(s, p)` (was Spieler p im Zustand s weiß) und `payoff0(s)`.
Alle Auszahlungen stehen aus Sicht von Spieler 0 (Spieler 1 bekommt das Negative): Zwei-Personen-Nullsummenspiel. Wahrscheinlichkeiten und Auszahlungen sind Brüche."""

from fractions import Fraction as Fr

KUHN_TERMINALS = ("pp", "bp", "bb", "pbp", "pbb")


def card_names(n: int) -> list[str]:
    """Namen der Karten von der niedrigsten zur höchsten: bei zwei und drei Karten Bube, Dame, König, sonst die Rangzahlen."""
    if n == 2:
        return ["Bube", "König"]
    if n == 3:
        return ["Bube", "Dame", "König"]
    return [str(i + 1) for i in range(n)]


class Kuhn:
    """Kuhn-Poker mit n Karten (n = 3 ist das Spiel von Kuhn): Anfangseinsatz 1 je Spieler, jeder bekommt eine andere Karte, gleichverteilt.

    Erster Spieler: Passen (0) oder Setzen (1). Nach Passen darf der zweite passen (Vergleich der Karten, Einsatz 1) oder setzen; nach einem Setzen des zweiten darf der erste
    aufgeben (0) oder mitgehen (1). Nach einem Setzen des ersten darf der zweite aufgeben (0) oder mitgehen (1). Wer setzt und mitgegangen wird, spielt um 2."""

    def __init__(self, n: int = 3):
        self.n = n

    def root(self):
        return (None, "")

    def kind(self, s) -> str:
        cards, h = s
        if cards is None:
            return "c"
        return "t" if h in KUHN_TERMINALS else "p"

    def chance(self, s):
        n = self.n
        pr = Fr(1, n * (n - 1))
        return [((a, b), pr, ((a, b), "")) for a in range(n) for b in range(n) if a != b]

    def player(self, s) -> int:
        return len(s[1]) % 2

    def actions(self, s):
        return ("p", "b")

    def child(self, s, a):
        return (s[0], s[1] + a)

    def infokey(self, s, p):
        return (p, s[0][p], s[1])

    def payoff0(self, s):
        (c0, c1), h = s
        hi = 1 if c0 > c1 else -1
        if h == "pp":
            return Fr(hi)
        if h == "bp":
            return Fr(1)
        if h == "pbp":
            return Fr(-1)
        return Fr(2 * hi)  # bb, pbb


class Anmeldung:
    """Anmeldung und Kontrolle (konstruiertes Nullsummenmodell): Eine Sendung ist in Ordnung (1 − p) oder riskant (p). Der Verlader weiß es und meldet sie als „sauber“ (S) oder
    „riskant“ (R); die Meldung R kostet die Gebühr f. Der Kontrolleur sieht nur die Meldung und kontrolliert (K) oder lässt durch (P).

    Auszahlung an den Verlader (Euro je Sendung): in Ordnung b, minus f bei Meldung R, plus c bei Kontrolle (der Kontrolleur entschädigt die unbegründete Verzögerung; diese
    Konstruktion macht das Spiel zur Nullsumme). Riskant und als sauber gemeldet: g beim Durchlassen, −s bei Kontrolle (Strafe). Riskant und als riskant gemeldet: r, plus c bei Kontrolle."""

    def __init__(self, b=10, c=2, f=1, g=15, s=20, r=6, p=Fr(3, 10)):
        self.par = dict(b=Fr(b), c=Fr(c), f=Fr(f), g=Fr(g), s=Fr(s), r=Fr(r), p=Fr(p))

    def root(self):
        return (None, None, None)

    def kind(self, s) -> str:
        if s[0] is None:
            return "c"
        return "t" if s[2] is not None else "p"

    def chance(self, s):
        p = self.par["p"]
        return [("ok", 1 - p, ("ok", None, None)), ("riskant", p, ("riskant", None, None))]

    def player(self, s) -> int:
        return 0 if s[1] is None else 1

    def actions(self, s):
        return ("S", "R") if s[1] is None else ("K", "P")

    def child(self, s, a):
        return (s[0], a, None) if s[1] is None else (s[0], s[1], a)

    def infokey(self, s, p):
        return (p, s[0]) if p == 0 else (p, s[1])

    def payoff0(self, s):
        P = self.par
        typ, meld, antw = s
        if typ == "ok":
            return P["b"] - (P["f"] if meld == "R" else 0) + (P["c"] if antw == "K" else 0)
        if meld == "S":
            return -P["s"] if antw == "K" else P["g"]
        return P["r"] + (P["c"] if antw == "K" else 0)


class Leduc:
    """Leduc-Poker (Rangabstraktion, Regeln aus dem Gedächtnis, Quelle nicht eingesehen): drei Ränge (Bube, Dame, König) je zweimal, Anfangseinsatz 1 je Spieler, private Karte,
    Runde 1 (Einsatzgröße 2), öffentliche Karte, Runde 2 (Einsatzgröße 4), höchstens zwei Erhöhungen je Runde. Ein Paar mit der öffentlichen Karte schlägt alles, sonst gewinnt der
    höhere Rang, bei Gleichstand wird geteilt. Farben ändern nichts; der Zufallsknoten trägt die richtigen Häufigkeiten.

    Zustand: (private Ränge, öffentliche Karte, Runde, Verlauf der Runde, Einsatz 0, Einsatz 1, Verlauf der Runde 1); f aufgeben, c mitgehen/schieben, r erhöhen."""

    SIZE = {1: 2, 2: 4}

    def root(self):
        return ((), None, 1, "", 1, 1, "")

    @staticmethod
    def _rest(priv, pub):
        cnt = [2, 2, 2]
        for c in priv:
            cnt[c] -= 1
        if pub is not None:
            cnt[pub] -= 1
        return cnt

    @staticmethod
    def _round_over(h: str) -> bool:
        return h.endswith("cc") or (len(h) >= 2 and h[-1] == "c" and h[-2] == "r")

    def kind(self, s) -> str:
        priv, pub, rnd, h, i0, i1, h1 = s
        if len(priv) < 2:
            return "c"
        if h.endswith("f"):
            return "t"
        if self._round_over(h):
            return "c" if rnd == 1 else "t"
        return "p"

    def chance(self, s):
        priv, pub, rnd, h, i0, i1, h1 = s
        cnt = self._rest(priv, pub)
        tot = sum(cnt)
        out = []
        if len(priv) < 2:
            for c in range(3):
                if cnt[c] > 0:
                    out.append((c, Fr(cnt[c], tot), (priv + (c,), pub, rnd, h, i0, i1, h1)))
            return out
        for c in range(3):
            if cnt[c] > 0:
                out.append((c, Fr(cnt[c], tot), (priv, c, 2, "", i0, i1, h)))
        return out

    def player(self, s) -> int:
        return len(s[3]) % 2

    def actions(self, s):
        h = s[3]
        if h and h[-1] == "r":
            return ("f", "c", "r") if h.count("r") < 2 else ("f", "c")
        return ("c", "r")

    def child(self, s, a):
        priv, pub, rnd, h, i0, i1, h1 = s
        p = len(h) % 2
        mine, other = (i0, i1) if p == 0 else (i1, i0)
        if a == "c":
            mine = other if (h and h[-1] == "r") else mine
        elif a == "r":
            mine = other + self.SIZE[rnd]
        if p == 0:
            i0, i1 = mine, other
        else:
            i1, i0 = mine, other
        return (priv, pub, rnd, h + a, i0, i1, h1)

    def infokey(self, s, p):
        priv, pub, rnd, h, i0, i1, h1 = s
        return (p, priv[p], pub, h1, h)

    def payoff0(self, s):
        priv, pub, rnd, h, i0, i1, h1 = s
        if h.endswith("f"):
            folder = (len(h) - 1) % 2
            return Fr(-i0) if folder == 0 else Fr(i1)
        st0 = (priv[0] == pub, priv[0])
        st1 = (priv[1] == pub, priv[1])
        if st0 == st1:
            return Fr(0)
        return Fr(i1) if st0 > st1 else Fr(-i0)
