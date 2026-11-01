"""Counterfactual Regret Minimization (CFR) und Verwandte auf dem Spielbaum, in kleinen Einheiten.

Einheiten: `regret_matching_probs` (Strategie aus Regrets), `cfr_pass` (ein Durchlauf des Baums, aktualisiert Regrets und Strategiesumme eines oder beider Spieler),
`clip_regrets` (Regret Matching⁺), `apply_discount` (Discounted CFR), `external_sampling_pass` (Monte-Carlo-CFR mit externem Sampling). Die Verfahren sind Zusammensetzungen dieser Einheiten
in `CFRSolver.step`. Alles in Gleitkomma auf `T.probf` und `T.payf`. Auszahlungen aus Sicht von Spieler 0; Spieler 1 maximiert das Negative.
Zufall nur über einen übergebenen SplitMix64-Strom."""

VARIANTS = {
    "cfr": "CFR (beide Seiten gleichzeitig)",
    "cfr_alt": "CFR abwechselnd",
    "cfr_clip": "CFR abwechselnd mit gekappten Regrets",
    "cfrplus": "CFR⁺",
    "dcfr": "Discounted CFR",
}
DCFR_PARAMS = (1.5, 0.0, 2.0)   # (α, β, γ), aus dem Gedächtnis, nicht in der Quelle geprüft


def regret_matching_probs(regrets) -> list[float]:
    """Regret Matching: Wahrscheinlichkeiten proportional zu den positiven Regrets; sind alle nicht positiv, gleichverteilt."""
    pos = [x if x > 0 else 0.0 for x in regrets]
    s = sum(pos)
    if s > 0:
        return [x / s for x in pos]
    return [1.0 / len(regrets)] * len(regrets)


def current_profile(T, reg):
    """Die aktuelle Strategie beider Spieler aus den Regrets (die „letzte Iteration“)."""
    return [[regret_matching_probs(reg[p][i]) for i in range(T.ninfo[p])] for p in (0, 1)]


def average_profile(T, avg):
    """Die Durchschnittsstrategie aus den Strategiesummen (gleichverteilt, wo nie besucht)."""
    out = []
    for p in (0, 1):
        rows = []
        for i in range(T.ninfo[p]):
            s = avg[p][i]
            tot = sum(s)
            rows.append([x / tot for x in s] if tot > 0 else [1.0 / len(s)] * len(s))
        out.append(rows)
    return out


def zero_tables(T):
    """Leere Regret- und Strategiesummen-Tabellen je Informationsmenge."""
    return ([[[0.0] * n for n in T.nact[p]] for p in (0, 1)], [[[0.0] * n for n in T.nact[p]] for p in (0, 1)])


def cfr_pass(T, sigma, reg, avg, update, weight):
    """Ein Durchlauf des Baums mit der Strategie `sigma`. Aktualisiert die Regrets und die Strategiesumme (Gewicht `weight`) von Spieler `update` (None: beide).

    Regret einer Aktion = Erreichungswahrscheinlichkeit des Gegners und des Zufalls × (Wert der Aktion − Wert der Informationsmenge), aus Sicht des Spielers am Zug."""
    kind, kids, probf, payf, player, info = T.kind, T.kids, T.probf, T.payf, T.player, T.info

    def trav(h, pi0, pi1, pc):
        k = kind[h]
        if k == "t":
            return payf[h]
        if k == "c":
            v = 0.0
            for c, pr in zip(kids[h], probf[h]):
                v += pr * trav(c, pi0, pi1, pc * pr)
            return v
        p = player[h]
        i = info[h]
        s = sigma[p][i]
        kd = kids[h]
        n = len(kd)
        us = [0.0] * n
        v = 0.0
        for a in range(n):
            u = trav(kd[a], pi0 * s[a], pi1, pc) if p == 0 else trav(kd[a], pi0, pi1 * s[a], pc)
            us[a] = u
            v += s[a] * u
        if update is None or update == p:
            if p == 0:
                cf, own, sign = pi1 * pc, pi0, 1.0
            else:
                cf, own, sign = pi0 * pc, pi1, -1.0
            r = reg[p][i]
            m = avg[p][i]
            for a in range(n):
                r[a] += sign * cf * (us[a] - v)
                m[a] += weight * own * s[a]
        return v

    trav(0, 1.0, 1.0, 1.0)


def clip_regrets(reg_p):
    """Regret Matching⁺: negative Regrets auf 0 setzen (in place, die Tabelle eines Spielers)."""
    for r in reg_p:
        for k in range(len(r)):
            if r[k] < 0:
                r[k] = 0.0


def apply_discount(reg_p, avg_p, t: int, params=DCFR_PARAMS):
    """Discounted CFR: positive Regrets mit t^α/(t^α+1), negative mit t^β/(t^β+1), die Strategiesumme mit ((t−1)/t)^γ abzinsen (in place, die Tabellen eines Spielers)."""
    a, b, g = params
    fp = t ** a / (t ** a + 1.0)
    fn = t ** b / (t ** b + 1.0)
    fm = ((t - 1.0) / t) ** g if t > 1 else 1.0
    for r in reg_p:
        for k in range(len(r)):
            r[k] *= fp if r[k] > 0 else fn
    for m in avg_p:
        for k in range(len(m)):
            m[k] *= fm


class CFRSolver:
    """Regret-Verfahren auf dem vollen Baum. `variant`: siehe VARIANTS. `init_regrets`: optionale Anfangsregrets (Zufallsstart), Form wie `zero_tables(T)[0]`.

    * cfr: beide Seiten im selben Durchlauf, Gewicht 1.
    * cfr_alt: erst Spieler 0, dann Spieler 1 (der zweite sieht die schon aktualisierte Strategie des ersten), Gewicht 1.
    * cfr_clip: wie cfr_alt, Regrets nach jeder Aktualisierung auf ≥ 0 gekappt, gleichmäßige Mittelung.
    * cfrplus: wie cfr_clip, aber lineare Mittelung (Gewicht t).
    * dcfr: abwechselnd, vor der Aktualisierung abzinsen (α, β, γ), Gewicht 1."""

    def __init__(self, T, variant: str = "cfr", init_regrets=None, dcfr_params=DCFR_PARAMS):
        if variant not in VARIANTS:
            raise ValueError(variant)
        self.T, self.variant, self.dcfr_params = T, variant, dcfr_params
        self.t = 0
        self.nodes = 0
        self.reg, self.avg = zero_tables(T)
        if init_regrets is not None:
            for p in (0, 1):
                for i in range(T.ninfo[p]):
                    self.reg[p][i] = [float(x) for x in init_regrets[p][i]]

    def current(self):
        return current_profile(self.T, self.reg)

    def average(self):
        return average_profile(self.T, self.avg)

    def step(self):
        self.t += 1
        t, T, v = self.t, self.T, self.variant
        if v == "cfr":
            cfr_pass(T, self.current(), self.reg, self.avg, None, 1.0)
            self.nodes += T.n
            return
        for p in (0, 1):
            if v == "dcfr":
                apply_discount(self.reg[p], self.avg[p], t, self.dcfr_params)
            cfr_pass(T, self.current(), self.reg, self.avg, p, float(t) if v == "cfrplus" else 1.0)
            if v in ("cfr_clip", "cfrplus"):
                clip_regrets(self.reg[p])
            self.nodes += T.n


def random_regrets(T, rng):
    """Zufallsstart: unabhängig gleichverteilte Anfangsregrets in [0, 1) (SplitMix64-Strom `rng`), Form wie `zero_tables(T)[0]`."""
    return [[[rng.uniform() for _ in range(n)] for n in T.nact[p]] for p in (0, 1)]


def external_sampling_pass(T, reg, avg, rng, p):
    """Ein Durchlauf von Monte-Carlo-CFR mit externem Sampling für Spieler p: alle Aktionen von p, eine gezogene Aktion beim Gegner und beim Zufall.

    Aktualisiert die Regrets von p (Aktionswert − Wert der Informationsmenge, ohne Gewichtung) und die Strategiesumme am gegnerischen Knoten (Gewicht 1). Rückgabe: Wert für p und Zahl besuchter Knoten."""
    kind, kids, probf, payf, player, info = T.kind, T.kids, T.probf, T.payf, T.player, T.info
    count = [0]

    def pick(weights):
        u = rng.uniform()
        acc = 0.0
        for a, w in enumerate(weights):
            acc += w
            if u < acc:
                return a
        return len(weights) - 1

    def trav(h):
        count[0] += 1
        k = kind[h]
        if k == "t":
            return payf[h] if p == 0 else -payf[h]
        if k == "c":
            return trav(kids[h][pick(probf[h])])
        q = player[h]
        i = info[h]
        s = regret_matching_probs(reg[q][i])
        kd = kids[h]
        if q == p:
            us = [trav(c) for c in kd]
            v = sum(si * ui for si, ui in zip(s, us))
            r = reg[p][i]
            for a in range(len(kd)):
                r[a] += us[a] - v
            return v
        m = avg[q][i]
        for a in range(len(kd)):
            m[a] += s[a]
        return trav(kd[pick(s)])

    v = trav(0)
    return v, count[0]


class SamplingSolver:
    """Externes Sampling (MCCFR): je Iteration ein gesampelter Durchlauf für jeden Spieler. Zufall nur aus dem übergebenen SplitMix64-Strom."""

    def __init__(self, T, rng):
        self.T, self.rng = T, rng
        self.t = 0
        self.nodes = 0
        self.reg, self.avg = zero_tables(T)

    def step(self):
        self.t += 1
        for p in (0, 1):
            _, cnt = external_sampling_pass(self.T, self.reg, self.avg, self.rng, p)
            self.nodes += cnt

    def average(self):
        return average_profile(self.T, self.avg)

    def current(self):
        return current_profile(self.T, self.reg)
