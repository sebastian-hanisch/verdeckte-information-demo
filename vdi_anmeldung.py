"""Anmeldung und Kontrolle: das Gleichgewicht in geschlossener Form (Indifferenzbedingungen) und das passende Strategieprofil.

Selbst hergeleitet, nicht aus der Literatur. Verlader: Sendung in Ordnung (1 − p) oder riskant (p); er meldet „sauber“ (S) oder „riskant“ (R). Der Kontrolleur sieht nur die Meldung.
Ist g ≤ r, lohnt sich Ehrlichkeit (Regime „ehrlich“: Wert (1 − p)·b + p·r, nie kontrolliert). Sonst, mit der Schwelle μ* = c/(c + g + s):
  p ≤ μ*: alle riskanten Sendungen melden „sauber“, der Kontrolleur kontrolliert nie („alle lügen“, Wert (1 − p)·b + p·g);
  p > μ*: riskante Sendungen melden „sauber“ mit λ = c(1 − p)/(p(g + s)), der Kontrolleur kontrolliert nach „sauber“ mit κ = (g − r)/(g + s) und nach „riskant“ nie
          („gemischt“, Wert (1 − p)(b + c·κ) + p·r)."""

from fractions import Fraction as Fr

REGIMES = ("ehrlich", "alle lügen", "gemischt")


def threshold(par) -> Fr:
    """Schwelle μ* = c/(c + g + s) des Anteils riskanter Sendungen."""
    return par["c"] / (par["c"] + par["g"] + par["s"])


def closed_form(par):
    """Gleichgewicht nach den Indifferenzbedingungen: (λ, κ, Wert an den Verlader, Regime). λ = Anteil der riskanten Sendungen, die „sauber“ melden;
    κ = Kontrollanteil nach der Meldung „sauber“. `par` ist das Wörterbuch `Anmeldung(...).par` (Brüche)."""
    b, c, f, g, s, r, p = (par[k] for k in "bcfgsrp")
    if g <= r:
        return Fr(0), Fr(0), (1 - p) * b + p * r, "ehrlich"
    if p <= threshold(par):
        return Fr(1), Fr(0), (1 - p) * b + p * g, "alle lügen"
    lam = c * (1 - p) / (p * (g + s))
    kap = (g - r) / (g + s)
    return lam, kap, (1 - p) * (b + c * kap) + p * r, "gemischt"


def equilibrium_profile(T, lam, kap):
    """Verhaltensstrategie zu (λ, κ): in Ordnung → „sauber“; riskant → „sauber“ mit λ, sonst „riskant“; nach „sauber“ kontrollieren mit κ; nach „riskant“ durchlassen."""
    st = [[None] * T.ninfo[0], [None] * T.ninfo[1]]
    st[0][T.ikeys[0][(0, "ok")]] = [Fr(1), Fr(0)]
    st[0][T.ikeys[0][(0, "riskant")]] = [Fr(lam), 1 - Fr(lam)]
    st[1][T.ikeys[1][(1, "S")]] = [Fr(kap), 1 - Fr(kap)]
    st[1][T.ikeys[1][(1, "R")]] = [Fr(0), Fr(1)]
    return st


def lying_share(par, lam) -> Fr:
    """Anteil der tatsächlich riskanten Sendungen an allen als „sauber“ gemeldeten: p·λ/(p·λ + 1 − p)."""
    p = par["p"]
    return p * lam / (p * lam + 1 - p)


def expected_controls(par, lam, kap) -> Fr:
    """Erwartete Kontrollen je Sendung: κ · (Anteil der Meldungen „sauber“ = 1 − p + p·λ)."""
    p = par["p"]
    return kap * (1 - p + p * lam)
