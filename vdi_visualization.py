"""Plotly-Figuren der Demo. Alle Achsen sind fest (fixedrange), damit Touch-Scrollen nicht am Diagramm hängen bleibt; Beschriftungen sind Annotationen, keine Text-Spuren."""

import plotly.graph_objects as go

import vdi_constants as C
import vdi_evaluation as V
import vdi_games as G

LAYOUT = dict(margin=dict(l=60, r=20, t=40, b=60), legend=dict(orientation="h", yanchor="top", y=-0.22, x=0), font=dict(size=13))


def _base(fig: go.Figure, title: str, height: int = 380) -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=15)), height=height, **LAYOUT)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _floor(values, lo=1e-12):
    return [max(float(v), lo) for v in values]


# --- Reiter 1 ----------------------------------------------------------------------------------------------------------------------------------------
def build_strategy(view: V.StrategyView) -> go.Figure:
    """Wahrscheinlichkeit der zweiten Aktion (Setzen bzw. Mitgehen) in jeder der zwölf Informationsmengen des Kuhn-Spiels mit drei Karten."""
    labels, probs, colors = [], [], []
    for r in view.rows:
        who = "1. Spieler" if r["player"] == 0 else "2. Spieler"
        labels.append(f"{who}: {G.card_names(3)[r['card']]}, {V.situation_name(r['player'], r['hist'])}: {V.action_name(r['player'], r['hist'])}")
        probs.append(float(r["prob"]))
        colors.append(C.COLOR_FIRST if r["player"] == 0 else C.COLOR_SECOND)
    fig = go.Figure(go.Bar(x=probs, y=labels, orientation="h", marker_color=colors, text=[V.de(p, 2) for p in probs], textposition="outside", cliponaxis=False))
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=11))
    fig.update_xaxes(range=[0, 1.12], title="Wahrscheinlichkeit")
    return _base(fig, "Strategie in allen zwölf Informationsmengen", 440)


def build_loss_curves(curves: dict) -> go.Figure:
    """Lücke der abweichenden Seite (Einsätze je Hand), wenn eine Entscheidung von 0 bis 1 läuft."""
    fig = go.Figure()
    palette = ["#e8a838", "#c97b84", "#4c78a8", "#8c6bb1", "#2F6B65"]
    for (name, (xs, gaps, side)), color in zip(curves.items(), palette):
        fig.add_trace(go.Scatter(x=[x / C.TWELFTHS for x in xs], y=[float(g) for g in gaps], mode="lines+markers", name=name, line=dict(color=color, dash="solid" if side == 2 else "dash")))
    fig.update_xaxes(title="Wahrscheinlichkeit der Handlung", range=[-0.03, 1.03])
    fig.update_yaxes(title="Lücke (Einsätze je Hand)", rangemode="tozero")
    return _base(fig, "Was eine Abweichung kostet: Lücke gegen die beste Antwort", 420)


def build_tree(T, n: int) -> go.Figure:
    """Der Spielbaum des Kuhn-Spiels (Wurzel oben): Zufallsknoten grau, erster Spieler blau, zweiter orange, Endknoten mit Auszahlung an den ersten Spieler.
    Gestrichelt verbunden: Knoten derselben Informationsmenge, die der Spieler nicht unterscheiden kann."""
    xs = [0.0] * T.n
    nleaf = [0]

    def place(h):
        if not T.kids[h]:
            xs[h] = float(nleaf[0])
            nleaf[0] += 1
        else:
            for c in T.kids[h]:
                place(c)
            xs[h] = sum(xs[c] for c in T.kids[h]) / len(T.kids[h])

    place(0)
    ys = [-float(T.depth[h]) for h in range(T.n)]
    fig = go.Figure()
    ex, ey = [], []
    for h in range(T.n):
        for c in T.kids[h]:
            ex += [xs[h], xs[c], None]
            ey += [ys[h], ys[c], None]
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="rgba(120,120,120,0.6)", width=1), hoverinfo="skip", showlegend=False))
    for p in (0, 1):
        dx, dy = [], []
        for nodes in T.inodes[p]:
            if len(nodes) > 1:
                dx += [xs[nodes[0]], xs[nodes[-1]], None]
                dy += [ys[nodes[0]] + 0.12 * (1 if p == 0 else -1), ys[nodes[-1]] + 0.12 * (1 if p == 0 else -1), None]
        if dx:
            fig.add_trace(go.Scatter(x=dx, y=dy, mode="lines", line=dict(color=C.COLOR_FIRST if p == 0 else C.COLOR_SECOND, width=2, dash="dot"), hoverinfo="skip",
                                     name=f"Informationsmenge Spieler {p + 1}"))
    for kind, color, symbol, name in (("c", "#999999", "diamond", "Zufall (Austeilung)"), ("p0", C.COLOR_FIRST, "circle", "erster Spieler am Zug"), ("p1", C.COLOR_SECOND, "circle", "zweiter Spieler am Zug"),
                                      ("t", "#333333", "square", "Ende")):
        hs = [h for h in range(T.n) if (T.kind[h] == kind or (T.kind[h] == "p" and f"p{T.player[h]}" == kind))]
        fig.add_trace(go.Scatter(x=[xs[h] for h in hs], y=[ys[h] for h in hs], mode="markers", marker=dict(size=9, color=color, symbol=symbol), name=name,
                                 hovertext=[_hover(T, h, n) for h in hs], hoverinfo="text"))
    for h in range(T.n):
        for a, c in zip(T.acts[h] or [], T.kids[h]):
            if T.kind[h] == "p":
                fig.add_annotation(x=(xs[h] + xs[c]) / 2, y=(ys[h] + ys[c]) / 2, text=a, showarrow=False, font=dict(size=9, color="#222222"), bgcolor="rgba(255,255,255,0.85)")
        if T.kind[h] == "t":
            fig.add_annotation(x=xs[h], y=ys[h] - 0.25, text=V.de(T.pay[h], 0).replace("+", ""), showarrow=False, font=dict(size=9))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _base(fig, f"Spielbaum des Kuhn-Spiels mit {n} Karten ({T.n} Knoten, {T.nterm} Enden)", 520)


def _hover(T, h: int, n: int) -> str:
    names = G.card_names(n)
    if T.kind[h] == "c":
        return "Austeilung"
    if T.kind[h] == "t":
        return f"Auszahlung an den ersten Spieler: {V.de(T.pay[h], 0)}"
    key = T.ilist[T.player[h]][T.info[h]]
    return f"Spieler {T.player[h] + 1} mit {names[key[1]]}, Verlauf „{key[2] or '–'}“"


# --- Reiter 2 ----------------------------------------------------------------------------------------------------------------------------------------
def build_sizes(n_marker: int) -> go.Figure:
    """Einträge der Normalform (12ⁿ) gegen Sequenzen je Spieler (4n + 1) über der Kartenzahl, logarithmisch."""
    ns = list(range(C.N_MIN, C.N_MAX + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[12 ** n for n in ns], mode="lines+markers", name="Einträge der Normalform (3ⁿ·4ⁿ)", line=dict(color=C.COLOR_LOSS)))
    fig.add_trace(go.Scatter(x=ns, y=[4 * n + 1 for n in ns], mode="lines+markers", name="Sequenzen je Spieler (4n + 1)", line=dict(color=C.COLOR_GOOD)))
    fig.add_vline(x=n_marker, line_dash="dot", line_color="rgba(120,120,120,0.8)")
    fig.update_xaxes(title="Karten n", dtick=1)
    fig.update_yaxes(title="Größe", type="log")
    return _base(fig, "Größe der Normalform gegen die der Sequenzform", 380)


# --- Reiter 3 ----------------------------------------------------------------------------------------------------------------------------------------
def build_convergence(runs: dict, x: str = "t", last: bool = True, title: str = "Lücke gegen Schritte", extra: dict | None = None) -> go.Figure:
    """Lücke der Durchschnittsstrategie (durchgezogen) und der letzten Iteration (gepunktet) je Verfahren, doppelt logarithmisch. `x`: "t" (Schritte) oder "nodes" (besuchte Knoten)."""
    fig = go.Figure()
    for key, run in {**runs, **(extra or {})}.items():
        color = C.VARIANT_COLORS.get(key, "#555555")
        fig.add_trace(go.Scatter(x=run[x], y=_floor(run["avg"]), mode="lines", name=V.variant_label(key), line=dict(color=color), legendgroup=key))
        if last and "last" in run and key in ("cfr", "cfrplus"):
            fig.add_trace(go.Scatter(x=run[x], y=_floor(run["last"]), mode="lines", name=f"{V.variant_label(key)}, letzte Iteration", line=dict(color=color, dash="dot"), legendgroup=key))
    fig.update_xaxes(title="Schritte T" if x == "t" else "besuchte Knoten", type="log")
    fig.update_yaxes(title="größere Lücke (Einsätze je Hand)", type="log")
    return _base(fig, title, 420)


def build_mean_table_figure(table_runs: dict, title: str) -> go.Figure:
    """Vorgerechnete Langzeitreihe (Durchschnitt) je Verfahren."""
    return build_convergence(table_runs, "t", last=False, title=title)


# --- Reiter 4 ----------------------------------------------------------------------------------------------------------------------------------------
def build_anmeldung(curves: dict, axis: str, marker) -> go.Figure:
    """Lügenanteil λ und Kontrollanteil κ über dem Anteil riskanter Sendungen p (Prozent) oder der Strafe s (Euro)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curves["x"], y=curves["lam"], mode="lines", name="Anteil der riskanten Sendungen, die „sauber“ melden (λ)", line=dict(color=C.COLOR_LOSS)))
    fig.add_trace(go.Scatter(x=curves["x"], y=curves["kap"], mode="lines", name="Kontrollanteil nach „sauber“ (κ)", line=dict(color=C.COLOR_GOOD)))
    fig.add_vline(x=marker, line_dash="dot", line_color="rgba(120,120,120,0.8)")
    fig.update_xaxes(title="Anteil riskanter Sendungen p (%)" if axis == "p" else "Strafe s (Euro je Sendung)")
    fig.update_yaxes(title="Anteil", range=[-0.02, 1.05])
    return _base(fig, "Lügen und Kontrolle (Gleichgewicht)", 380)


def build_anmeldung_value(curves: dict, axis: str, marker) -> go.Figure:
    fig = go.Figure(go.Scatter(x=curves["x"], y=curves["value"], mode="lines", line=dict(color=C.COLOR_FIRST), name="Wert für den Verlader"))
    fig.add_vline(x=marker, line_dash="dot", line_color="rgba(120,120,120,0.8)")
    fig.update_xaxes(title="Anteil riskanter Sendungen p (%)" if axis == "p" else "Strafe s (Euro je Sendung)")
    fig.update_yaxes(title="Euro je Sendung")
    return _base(fig, "Wert des Spiels für den Verlader", 380)
