import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from io import StringIO

st.set_page_config(page_title="Mundial 2026 — Data Hub", page_icon="🏆", layout="wide")

BASE_URL = "https://raw.githubusercontent.com/dbouzada/mundial-2026-data/main/data/processed"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #080810;
    color: #e8e8f0;
}
h1,h2,h3,h4 { font-family: 'Space Grotesk', sans-serif; }
section[data-testid="stSidebar"] { display: none; }
.block-container { padding: 2rem 3rem; max-width: 1400px; }

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
    color: #c8f24d;
    margin: 0;
}
.hero-sub {
    font-size: 0.9rem;
    color: #888899;
    margin-top: 8px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.update-tag { font-size: 0.7rem; color: #666677; margin-top: 6px; }

.kpi-card {
    background: linear-gradient(145deg, #0d0d1a 0%, #111122 100%);
    border: 1px solid #1e1e35;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
}
.kpi-card:hover { border-color: #c8f24d33; }
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #c8f24d, transparent);
    opacity: 0.5;
}
.kpi-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem;
    font-weight: 700;
    color: #c8f24d;
    line-height: 1;
    letter-spacing: -0.03em;
}
.kpi-label {
    font-size: 0.68rem;
    color: #666677;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-top: 10px;
    font-weight: 500;
}

.section-divider {
    margin: 56px 0 28px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.section-divider-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, #1e1e35, transparent);
}
.section-divider-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    color: #666677;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    white-space: nowrap;
}

.match-card {
    background: #0d0d1a;
    border: 1px solid #1a1a2e;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
    animation: fadeSlideIn 0.4s ease forwards;
}
.match-card.home-win  { border-left: 3px solid #c8f24d; }
.match-card.away-win  { border-left: 3px solid #4d9df2; }
.match-card.draw      { border-left: 3px solid #44445a; }
.match-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 80px; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(200,242,77,0.02));
    pointer-events: none;
}
.match-score {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #c8f24d;
    letter-spacing: -0.02em;
}
.match-team { font-weight: 500; font-size: 0.92rem; }
.match-meta { font-size: 0.65rem; color: #666677; margin-top: 4px; }
.match-badge {
    font-size: 0.6rem;
    font-weight: 600;
    color: #c8f24d;
    background: rgba(200,242,77,0.08);
    border: 1px solid rgba(200,242,77,0.15);
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.next-card {
    background: #0d0d1a;
    border: 1px solid #1a1a2e;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 10px;
}
.next-card-time { font-size: 0.68rem; color: #6db8f5; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; }
.next-card-match { font-weight: 500; font-size: 0.95rem; color: #c8c8d8; }

.standings-row {
    background: #0d0d1a;
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 10px;
    position: relative;
    overflow: hidden;
}
.standings-row.qualified { border-left: 3px solid #c8f24d; }
.standings-row.bubble    { border-left: 3px solid #4d9df2; }
.standings-pos { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.85rem; color: #44445a; width: 18px; flex-shrink: 0; }
.standings-team { flex: 1; font-size: 0.82rem; font-weight: 500; }
.standings-pts { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1rem; color: #c8f24d; min-width: 28px; text-align: right; }
.standings-bar-wrap { position: absolute; bottom: 0; left: 0; right: 0; height: 2px; background: #1a1a2e; }
.standings-bar { height: 2px; background: linear-gradient(90deg, #c8f24d, #4d9df2); border-radius: 2px; transition: width 0.8s ease; }

.scorer-card {
    background: #0d0d1a;
    border: 1px solid #1a1a2e;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.scorer-name { font-weight: 600; font-size: 0.9rem; }
.scorer-team { font-size: 0.7rem; color: #44445a; margin-top: 2px; }
.scorer-goals { font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; font-weight: 700; color: #c8f24d; }
.scorer-bar-wrap { margin-top: 8px; height: 3px; background: #1a1a2e; border-radius: 3px; }
.scorer-bar { height: 3px; border-radius: 3px; }

.live-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(242,120,77,0.08);
    border: 1px solid rgba(242,120,77,0.2);
    border-radius: 20px;
    padding: 6px 14px;
}
.live-dot {
    width: 7px; height: 7px;
    background: #f2784d;
    border-radius: 50%;
    animation: livepulse 1.4s infinite;
}
.live-text { font-size: 0.75rem; color: #f2784d; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }

@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes livepulse {
    0%,100% { opacity: 1; box-shadow: 0 0 0 0 rgba(242,120,77,0.4); }
    50%      { opacity: 0.6; box-shadow: 0 0 0 6px rgba(242,120,77,0); }
}
</style>
""", unsafe_allow_html=True)

# ── THEME ─────────────────────────────────────────────────────────────────────
BG      = "#080810"
BG2     = "#0d0d1a"
ACCENT  = "#c8f24d"
BLUE    = "#4d9df2"
RED     = "#f2784d"
MUTED   = "#44445a"
GRID    = "#1a1a2e"
FONT    = "Space Grotesk, Inter, sans-serif"

def theme(height=360, margin=None, show_legend=True):
    m = margin or dict(t=24, b=24, l=8, r=8)
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color="#888899", size=11),
        height=height,
        margin=m,
        showlegend=show_legend,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#666677", size=11),
            bordercolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(
            gridcolor=GRID, zeroline=False,
            tickfont=dict(color=MUTED, size=10),
            linecolor=GRID
        ),
        yaxis=dict(
            gridcolor=GRID, zeroline=False,
            tickfont=dict(color=MUTED, size=10),
            linecolor=GRID
        ),
        hoverlabel=dict(
            bgcolor="#111122",
            bordercolor="#2a2a4a",
            font=dict(family=FONT, color="#e8e8f0", size=12)
        )
    )

def clean_grupo(g):
    if not g or not isinstance(g, str): return g or ''
    return g.replace('GROUP_', 'Grupo ')

# ── CARGA ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    def get_csv(f):
        r = requests.get(f"{BASE_URL}/{f}")
        return pd.read_csv(StringIO(r.text))
    matches   = get_csv("matches.csv")
    standings = get_csv("standings.csv")
    scorers   = get_csv("scorers.csv")
    kpis      = get_csv("kpis_equipos.csv")
    try:    meta = requests.get(f"{BASE_URL}/meta.json").json()
    except: meta = {}
    return matches, standings, scorers, kpis, meta

matches, standings, scorers, kpis, meta = load_data()

matches["goles_home"]  = pd.to_numeric(matches["goles_home"],  errors="coerce")
matches["goles_away"]  = pd.to_numeric(matches["goles_away"],  errors="coerce")
matches["total_goles"] = matches["goles_home"] + matches["goles_away"]
matches["fecha"]       = pd.to_datetime(matches["fecha"], errors="coerce")
matches["grupo_clean"] = matches["grupo"].apply(clean_grupo)

finished = matches[matches["estado"] == "FINISHED"].copy()
upcoming = matches[matches["estado"].isin(["TIMED","SCHEDULED"])].copy()
in_play  = matches[matches["estado"] == "IN_PLAY"].copy()

standings["grupo_clean"] = standings["grupo"].apply(clean_grupo)
for col in ["pj","ganados","empatados","perdidos","gf","gc","dg","puntos"]:
    if col in standings.columns:
        standings[col] = pd.to_numeric(standings[col], errors="coerce").fillna(0).astype(int)

scorers["goles"]        = pd.to_numeric(scorers["goles"],       errors="coerce").fillna(0)
scorers["asistencias"]  = pd.to_numeric(scorers["asistencias"], errors="coerce").fillna(0)
scorers["penales"]      = pd.to_numeric(scorers["penales"],     errors="coerce").fillna(0)
scorers["goles_jugada"] = scorers["goles"] - scorers["penales"]

for col in ["gf","gc","dg","puntos","promedio_gf","pj"]:
    if col in kpis.columns:
        kpis[col] = pd.to_numeric(kpis[col], errors="coerce").fillna(0)

total_goles = int(finished["total_goles"].sum())  if not finished.empty else 0
promedio    = round(finished["total_goles"].mean(), 2) if not finished.empty else 0
max_goles   = int(finished["total_goles"].max())  if not finished.empty else 0
n_jugados   = meta.get("partidos_terminados", len(finished))

# ── HERO ──────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("<p class='hero-title'>Mundial 2026</p>", unsafe_allow_html=True)
    st.markdown("<p class='hero-sub'>Data Hub · Analytics en tiempo real</p>", unsafe_allow_html=True)
    ultima_utc = meta.get('ultima_actualizacion', '')
try:
    from datetime import datetime, timedelta
    dt_utc = datetime.strptime(ultima_utc, "%Y-%m-%d %H:%M UTC")
    dt_arg = dt_utc - timedelta(hours=3)
    ultima_arg = dt_arg.strftime("%d/%m/%Y %H:%M") + " ARG"
except:
    ultima_arg = ultima_utc
st.markdown(f"<p class='update-tag'>Actualizado {ultima_arg}</p>", unsafe_allow_html=True)
with col2:
    if not in_play.empty:
        st.markdown(f"""<div class='live-pill'>
            <div class='live-dot'></div>
            <span class='live-text'>En vivo</span>
        </div>""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Resumen del torneo</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

c1,c2,c3,c4,c5 = st.columns(5)
for col,val,lbl in zip([c1,c2,c3,c4,c5],
    [n_jugados, total_goles, promedio, max_goles, 104],
    ["Partidos jugados","Goles totales","Goles × partido","Récord en un partido","Partidos totales"]):
    with col:
        st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{val}</div><div class='kpi-label'>{lbl}</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── OVERVIEW CHARTS ───────────────────────────────────────────────────────────
if not finished.empty:
    col1, col2, col3 = st.columns([2, 1.5, 1.5])

    with col1:
        gd = finished.groupby("fecha")["total_goles"].sum().reset_index().sort_values("fecha")
        gd["fecha_str"] = gd["fecha"].dt.strftime("%d/%m")
        gd["acumulado"] = gd["total_goles"].cumsum()

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=gd["fecha_str"], y=gd["total_goles"],
            name="Por día",
            marker=dict(color=BLUE, opacity=0.35, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>Goles: %{y}<extra></extra>"
        ), secondary_y=True)
        fig.add_trace(go.Scatter(
            x=gd["fecha_str"], y=gd["acumulado"],
            name="Acumulado",
            mode="lines+markers",
            line=dict(color=ACCENT, width=2.5, shape="spline", smoothing=1.3),
            marker=dict(color=ACCENT, size=6, line=dict(color=BG2, width=2)),
            fill="tozeroy",
            fillcolor="rgba(200,242,77,0.04)",
            hovertemplate="<b>%{x}</b><br>Acumulado: %{y}<extra></extra>"
        ), secondary_y=False)
        fig.update_layout(**theme(height=280, show_legend=False))
        fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED, size=10), secondary_y=False)
        fig.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(color=MUTED, size=10), secondary_y=True)
        st.markdown("**Goles acumulados**")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "ganador" in finished.columns:
            conteo = finished["ganador"].value_counts()
            labels_map = {"HOME_TEAM":"Local","AWAY_TEAM":"Visitante","DRAW":"Empate"}
            labels = [labels_map.get(l,l) for l in conteo.index]
            colors = [ACCENT, BLUE, MUTED]
            fig2 = go.Figure(go.Pie(
                labels=labels, values=conteo.values,
                hole=0.65,
                marker=dict(
                    colors=colors,
                    line=dict(color=BG, width=3)
                ),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{value} partidos (%{percent})<extra></extra>"
            ))
            fig2.add_annotation(
                text=f"<b>{len(finished)}</b><br><span style='font-size:10px'>partidos</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=18, color="#e8e8f0", family=FONT)
            )
            fig2.update_layout(**theme(height=280, show_legend=True))
            fig2.update_layout(legend=dict(
                orientation="v", x=1.05, y=0.5,
                font=dict(size=11, color="#666677")
            ))
            st.markdown("**Resultados**")
            st.plotly_chart(fig2, use_container_width=True)

    with col3:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=promedio,
            delta=dict(reference=2.7, valueformat=".1f",
                increasing=dict(color=ACCENT), decreasing=dict(color=RED)),
            number=dict(font=dict(size=42, color=ACCENT, family=FONT), valueformat=".1f"),
            gauge=dict(
                axis=dict(range=[0,6], tickfont=dict(color=MUTED, size=9), tickcolor=MUTED),
                bar=dict(color=ACCENT, thickness=0.25),
                bgcolor="rgba(0,0,0,0)",
                bordercolor=GRID, borderwidth=1,
                steps=[
                    dict(range=[0,2],   color="#0d0d1a"),
                    dict(range=[2,3.5], color="#111122"),
                    dict(range=[3.5,6], color="#141428"),
                ],
                threshold=dict(
                    line=dict(color=BLUE, width=2),
                    thickness=0.75, value=2.7
                )
            ),
            title=dict(text="Goles × partido", font=dict(color=MUTED, size=12, family=FONT))
        ))
        gauge.update_layout(**theme(height=280, show_legend=False))
        gauge.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.markdown("**Promedio**")
        st.plotly_chart(gauge, use_container_width=True)

# ── PRÓXIMOS ──────────────────────────────────────────────────────────────────
st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Próximos partidos</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

if upcoming.empty:
    st.markdown("<p style='color:#33334a;font-size:0.85rem'>No hay próximos partidos programados.</p>", unsafe_allow_html=True)
else:
    proximos = upcoming.sort_values("fecha").head(6)
    cols = st.columns(3)
    for i, (_, row) in enumerate(proximos.iterrows()):
        fecha_str = row["fecha"].strftime("%d %b · %H:%M UTC") if pd.notna(row["fecha"]) else "—"
        grupo_txt = clean_grupo(str(row.get("grupo",""))) if pd.notna(row.get("grupo")) else str(row.get("etapa",""))
        with cols[i % 3]:
            st.markdown(f"""<div class='next-card'>
                <div class='next-card-time'>{fecha_str} · {grupo_txt}</div>
                <div class='next-card-match'>{row['home']} vs {row['away']}</div>
            </div>""", unsafe_allow_html=True)

# ── RESULTADOS ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Resultados</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

def match_card(row):
    gh = int(row["goles_home"]) if pd.notna(row["goles_home"]) else "—"
    ga = int(row["goles_away"]) if pd.notna(row["goles_away"]) else "—"
    grupo_txt = clean_grupo(str(row.get("grupo",""))) if pd.notna(row.get("grupo")) else ""
    fecha_str = row["fecha"].strftime("%d %b") if pd.notna(row["fecha"]) else "—"
    ganador = row.get("ganador","")
    css = "home-win" if ganador=="HOME_TEAM" else ("away-win" if ganador=="AWAY_TEAM" else "draw")
    return f"""<div class='match-card {css}'>
        <div style='display:flex;justify-content:space-between;align-items:center'>
            <div style='flex:2;text-align:right'>
                <div class='match-team'>{row['home']}</div>
            </div>
            <div style='flex:1.5;text-align:center;padding:0 12px'>
                <div class='match-score'>{gh} — {ga}</div>
                <div class='match-meta'>{fecha_str}</div>
            </div>
            <div style='flex:2'>
                <div class='match-team'>{row['away']}</div>
            </div>
            <div style='margin-left:12px'><span class='match-badge'>{grupo_txt}</span></div>
        </div>
    </div>"""

if not finished.empty:
    ultimos = finished.sort_values("fecha", ascending=False).head(6)
    col1, col2 = st.columns(2)
    for i, (_, row) in enumerate(ultimos.iterrows()):
        (col1 if i%2==0 else col2).markdown(match_card(row), unsafe_allow_html=True)

    with st.expander(f"Ver todos los resultados — {len(finished)} partidos"):
        grupos = ["Todos"] + sorted(finished["grupo_clean"].dropna().unique().tolist())
        gs = st.selectbox("Grupo", grupos, key="g_res")
        df_show = finished if gs=="Todos" else finished[finished["grupo_clean"]==gs]
        col1, col2 = st.columns(2)
        for i, (_, row) in enumerate(df_show.sort_values("fecha", ascending=False).iterrows()):
            (col1 if i%2==0 else col2).markdown(match_card(row), unsafe_allow_html=True)

# ── ANÁLISIS ──────────────────────────────────────────────────────────────────
if not finished.empty:
    st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Análisis del torneo</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if "grupo_clean" in finished.columns:
            gg = finished.groupby("grupo_clean")["total_goles"].agg(["sum","mean","count"]).reset_index()
            gg.columns = ["grupo","total","promedio","partidos"]
            gg = gg.sort_values("total", ascending=False)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=gg["grupo"], y=gg["total"],
                marker=dict(
                    color=gg["total"],
                    colorscale=[[0,"#1a1a35"],[0.5,"#4d9df2"],[1,"#c8f24d"]],
                    line=dict(width=0)
                ),
                text=gg["total"],
                textposition="outside",
                textfont=dict(color=ACCENT, size=13, family=FONT),
                hovertemplate="<b>%{x}</b><br>Goles: %{y}<br>Promedio: %{customdata:.1f}<extra></extra>",
                customdata=gg["promedio"]
            ))
            fig.update_layout(**theme(height=300, show_legend=False))
            st.markdown("**Goles por grupo**")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        tp = finished.nlargest(8,"total_goles").copy()
        tp["partido"] = tp.apply(lambda r: f"{r['home']} vs {r['away']}", axis=1)
        tp = tp.sort_values("total_goles")
        fig2 = go.Figure(go.Bar(
            x=tp["total_goles"], y=tp["partido"],
            orientation="h",
            marker=dict(
                color=tp["total_goles"],
                colorscale=[[0,"#1a1a35"],[0.5,"#4d9df2"],[1,"#c8f24d"]],
                line=dict(width=0)
            ),
            text=tp["total_goles"],
            textposition="outside",
            textfont=dict(color=ACCENT, size=12, family=FONT),
            hovertemplate="<b>%{y}</b><br>Goles: %{x}<extra></extra>"
        ))
        fig2.update_layout(**theme(height=300, show_legend=False))
        st.markdown("**Partidos más goleadores**")
        st.plotly_chart(fig2, use_container_width=True)

    # Goles por partido stacked
    tl = finished[finished["total_goles"].notna()].sort_values("fecha").copy().reset_index(drop=True)
    tl["goles_home"] = tl["goles_home"].fillna(0).astype(int)
    tl["goles_away"] = tl["goles_away"].fillna(0).astype(int)
    tl["label"] = tl.apply(lambda r: f"{r['home']} vs {r['away']}", axis=1)

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="Local", x=tl["label"], y=tl["goles_home"],
        marker=dict(color=ACCENT, opacity=0.9, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Local: %{y}<extra></extra>"
    ))
    fig3.add_trace(go.Bar(
        name="Visitante", x=tl["label"], y=tl["goles_away"],
        marker=dict(color=BLUE, opacity=0.9, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Visitante: %{y}<extra></extra>"
    ))
    fig3.update_layout(**theme(height=320), barmode="stack")
    fig3.update_layout(margin=dict(t=24, b=120, l=8, r=8))
    fig3.update_xaxes(tickangle=-45, tickfont=dict(size=9, color=MUTED))
    st.markdown("**Goles por partido**")
    st.plotly_chart(fig3, use_container_width=True)

    # Heatmap
    if "grupo_clean" in finished.columns:
        finished["fecha_str"] = finished["fecha"].dt.strftime("%d/%m")
        hm = finished.groupby(["grupo_clean","fecha_str"])["total_goles"].sum().reset_index()
        hm_pivot = hm.pivot(index="grupo_clean", columns="fecha_str", values="total_goles").fillna(0)
        fig_hm = go.Figure(go.Heatmap(
            z=hm_pivot.values,
            x=hm_pivot.columns.tolist(),
            y=hm_pivot.index.tolist(),
            colorscale=[[0,"#080810"],[0.2,"#0d1a0d"],[0.5,"#1a3a1a"],[0.8,"#4a8a1a"],[1,"#c8f24d"]],
            showscale=True,
            text=hm_pivot.values.astype(int),
            texttemplate="%{text}",
            textfont=dict(size=12, color="#e8e8f0", family=FONT),
            hoverongaps=False,
            colorbar=dict(
                bgcolor="rgba(0,0,0,0)",
                tickfont=dict(color=MUTED, size=10),
                outlinecolor=GRID, outlinewidth=1
            )
        ))
        fig_hm.update_layout(**theme(height=340, show_legend=False))
        st.markdown("**Heatmap — goles por grupo y fecha**")
        st.plotly_chart(fig_hm, use_container_width=True)

# ── TABLA DE POSICIONES ───────────────────────────────────────────────────────
st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Tabla de posiciones</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

grupos_list = sorted(standings["grupo_clean"].dropna().unique().tolist())
for row_grupos in [grupos_list[i:i+4] for i in range(0, len(grupos_list), 4)]:
    cols = st.columns(4)
    for j, grupo in enumerate(row_grupos):
        df_g = standings[standings["grupo_clean"]==grupo].sort_values("posicion")
        max_pts = max(df_g["puntos"].max(), 1)
        with cols[j]:
            st.markdown(f"<div style='font-size:0.7rem;font-weight:600;color:#44445a;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:10px'>{grupo}</div>", unsafe_allow_html=True)
            for _, row in df_g.iterrows():
                pos = int(row["posicion"])
                pts = int(row["puntos"])
                pct = int(pts / max_pts * 100)
                css_class = "qualified" if pos <= 2 else ""
                pos_color = ACCENT if pos<=2 else MUTED
                st.markdown(f"""<div class='standings-row {css_class}'>
                    <div class='standings-pos' style='color:{pos_color}'>{pos}</div>
                    <div class='standings-team'>{row["equipo"]}</div>
                    <div style='font-size:0.7rem;color:#33334a;margin-right:4px'>{int(row["pj"])}PJ</div>
                    <div class='standings-pts'>{pts}</div>
                    <div class='standings-bar-wrap'>
                        <div class='standings-bar' style='width:{pct}%'></div>
                    </div>
                </div>""", unsafe_allow_html=True)

# ── GOLEADORES ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Goleadores</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    top_n = st.slider("Top N jugadores", 5, max(5,len(scorers)), min(10,len(scorers)), key="topn")
    df_top = scorers.sort_values("goles", ascending=False).head(top_n).copy()
    max_g = df_top["goles"].max()
    medals = ["🥇","🥈","🥉"] + [""]*max(0,len(df_top)-3)
    for i, (_, row) in enumerate(df_top.iterrows()):
        pct = int(row["goles"]/max(max_g,1)*100)
        bar_color = f"linear-gradient(90deg, {ACCENT}, {BLUE})" if i==0 else (f"linear-gradient(90deg, {ACCENT}cc, {ACCENT}88)" if i<3 else f"linear-gradient(90deg, {BLUE}88, {BLUE}44)")
        st.markdown(f"""<div class='scorer-card'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                <div>
                    <div class='scorer-name'>{medals[i]} {row["jugador"]}</div>
                    <div class='scorer-team'>{row["equipo"]}</div>
                </div>
                <div style='text-align:right'>
                    <div class='scorer-goals'>{int(row["goles"])}</div>
                    <div style='font-size:0.65rem;color:#33334a'>{int(row["asistencias"])} ast · {int(row["penales"])} pen</div>
                </div>
            </div>
            <div class='scorer-bar-wrap'>
                <div class='scorer-bar' style='width:{pct}%;background:{bar_color}'></div>
            </div>
        </div>""", unsafe_allow_html=True)

with col2:
    st.markdown("**Goles de jugada vs penal**")
    df_t2 = scorers.sort_values("goles", ascending=False).head(10)
    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(
        name="Jugada", x=df_t2["jugador"], y=df_t2["goles_jugada"],
        marker=dict(color=ACCENT, opacity=0.9, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Jugada: %{y}<extra></extra>"
    ))
    fig_s.add_trace(go.Bar(
        name="Penal", x=df_t2["jugador"], y=df_t2["penales"],
        marker=dict(color=RED, opacity=0.9, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Penal: %{y}<extra></extra>"
    ))
    fig_s.update_layout(**theme(height=280), barmode="stack")
    fig_s.update_layout(margin=dict(t=24,b=100,l=8,r=8))
    fig_s.update_xaxes(tickangle=-35, tickfont=dict(size=9,color=MUTED))
    st.plotly_chart(fig_s, use_container_width=True)

    st.markdown("**Participaciones en gol**")
    df_p = scorers.copy()
    df_p["participaciones"] = df_p["goles"] + df_p["asistencias"]
    df_p = df_p[df_p["participaciones"]>0].sort_values("participaciones", ascending=True).tail(10)
    fig_p = go.Figure()
    fig_p.add_trace(go.Bar(
        name="Goles", y=df_p["jugador"], x=df_p["goles"],
        orientation="h",
        marker=dict(color=ACCENT, opacity=0.9, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Goles: %{x}<extra></extra>"
    ))
    fig_p.add_trace(go.Bar(
        name="Asistencias", y=df_p["jugador"], x=df_p["asistencias"],
        orientation="h",
        marker=dict(color=BLUE, opacity=0.9, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Asistencias: %{x}<extra></extra>"
    ))
    fig_p.update_layout(**theme(height=300), barmode="stack")
    st.plotly_chart(fig_p, use_container_width=True)

# ── RENDIMIENTO ───────────────────────────────────────────────────────────────
if not kpis.empty:
    st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Rendimiento por equipo</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        ks = kpis.sort_values("puntos", ascending=True)
        fig = go.Figure(go.Bar(
            x=ks["puntos"], y=ks["equipo"],
            orientation="h",
            marker=dict(
                color=ks["puntos"],
                colorscale=[[0,"#1a1a2e"],[0.5,"#4d9df2"],[1,"#c8f24d"]],
                line=dict(width=0)
            ),
            text=ks["puntos"],
            textposition="outside",
            textfont=dict(color=ACCENT, size=11, family=FONT),
            hovertemplate="<b>%{y}</b><br>Puntos: %{x}<extra></extra>"
        ))
        fig.update_layout(**theme(height=max(320,len(kpis)*42), show_legend=False))
        fig.update_layout(margin=dict(t=24,b=24,l=8,r=40))
        st.markdown("**Puntos acumulados**")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.scatter(kpis, x="gf", y="gc", text="equipo",
            size="pj", color="puntos",
            color_continuous_scale=[[0,"#f2784d"],[0.5,"#4d9df2"],[1,"#c8f24d"]],
            labels={"gf":"Goles a favor","gc":"Goles en contra","puntos":"Puntos","pj":"PJ"},
            size_max=30
        )
        fig2.update_traces(
            textposition="top center",
            textfont=dict(size=9, color="#888899", family=FONT),
            hovertemplate="<b>%{text}</b><br>GF: %{x} · GC: %{y}<extra></extra>"
        )
        fig2.add_hline(y=kpis["gc"].mean(), line_dash="dot", line_color=GRID, line_width=1)
        fig2.add_vline(x=kpis["gf"].mean(), line_dash="dot", line_color=GRID, line_width=1)
        fig2.update_layout(**theme(height=max(320,len(kpis)*42)))
        fig2.update_coloraxes(showscale=False)
        st.markdown("**Ofensivo vs defensivo**")
        st.plotly_chart(fig2, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        kd = kpis.sort_values("dg", ascending=True)
        colors_dg = [ACCENT if v>=0 else RED for v in kd["dg"]]
        fig3 = go.Figure(go.Bar(
            x=kd["dg"], y=kd["equipo"],
            orientation="h",
            marker=dict(color=colors_dg, opacity=0.85, line=dict(width=0)),
            text=[f"+{v}" if v>0 else str(v) for v in kd["dg"].astype(int)],
            textposition="outside",
            textfont=dict(size=10, family=FONT),
            hovertemplate="<b>%{y}</b><br>DG: %{x}<extra></extra>"
        ))
        fig3.add_vline(x=0, line_color=MUTED, line_width=1)
        fig3.update_layout(**theme(height=max(320,len(kpis)*42), show_legend=False))
        fig3.update_layout(margin=dict(t=24,b=24,l=8,r=50))
        st.markdown("**Diferencia de goles**")
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        if len(kpis) >= 3:
            top5 = kpis.nlargest(5,"puntos")
            cats = ["Puntos","GF","Prom×3","DG+"]
            pal = [ACCENT, BLUE, RED, "#a855f7", "#f59e0b"]
            fills = ["rgba(200,242,77,0.08)","rgba(77,157,242,0.08)",
                     "rgba(242,120,77,0.08)","rgba(168,85,247,0.08)","rgba(245,158,11,0.08)"]
            fig4 = go.Figure()
            for i, (_, row) in enumerate(top5.iterrows()):
                fig4.add_trace(go.Scatterpolar(
                    r=[row["puntos"], row["gf"], row["promedio_gf"]*3, max(row["dg"],0)],
                    theta=cats, fill="toself", name=row["equipo"],
                    line=dict(color=pal[i], width=2),
                    fillcolor=fills[i], opacity=0.9,
                    hovertemplate=f"<b>{row['equipo']}</b><br>%{{theta}}: %{{r:.1f}}<extra></extra>"
                ))
            fig4.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, color=GRID, gridcolor=GRID,
                        tickfont=dict(color=MUTED, size=8)),
                    angularaxis=dict(color=MUTED, gridcolor=GRID,
                        tickfont=dict(color=MUTED, size=10))
                ),
                **theme(height=max(320,len(kpis)*42))
            )
            fig4.update_layout(legend=dict(x=1.1, y=0.5, font=dict(size=10, color="#666677")))
            st.markdown("**Radar — top 5**")
            st.plotly_chart(fig4, use_container_width=True)

# ── AVANZADO ──────────────────────────────────────────────────────────────────
if not finished.empty and not kpis.empty and kpis["gf"].sum()>0:
    st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Análisis avanzado</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        kpis_gf = kpis[kpis["gf"]>0].copy()
        fig_tree = px.treemap(kpis_gf, path=["equipo"], values="gf",
            color="puntos",
            color_continuous_scale=[[0,"#0d0d1a"],[0.4,"#1a2a4a"],[0.7,"#4d9df2"],[1,"#c8f24d"]],
            hover_data={"gf":True,"puntos":True}
        )
        fig_tree.update_traces(
            textinfo="label+value",
            textfont=dict(size=12, family=FONT, color="#e8e8f0"),
            marker=dict(line=dict(color=BG, width=3)),
            hovertemplate="<b>%{label}</b><br>Goles: %{value}<br>Puntos: %{customdata[1]}<extra></extra>"
        )
        fig_tree.update_layout(**theme(height=400, show_legend=False))
        fig_tree.update_coloraxes(showscale=False)
        st.markdown("**Treemap — goles por equipo**")
        st.plotly_chart(fig_tree, use_container_width=True)

    with col2:
        fig_b = go.Figure()
        ks2 = kpis.sort_values("gf", ascending=False).head(12)
        fig_b.add_trace(go.Bar(
            name="GF", x=ks2["equipo"], y=ks2["gf"],
            marker=dict(color=ACCENT, opacity=0.85, line=dict(width=0))
        ))
        fig_b.add_trace(go.Bar(
            name="GC", x=ks2["equipo"], y=ks2["gc"],
            marker=dict(color=RED, opacity=0.85, line=dict(width=0))
        ))
        fig_b.add_trace(go.Scatter(
            name="DG", x=ks2["equipo"], y=ks2["dg"],
            mode="lines+markers",
            line=dict(color=BLUE, width=2, dash="dot"),
            marker=dict(color=BLUE, size=7, line=dict(color=BG2, width=2)),
            yaxis="y2"
        ))
        fig_b.update_layout(**theme(height=400), barmode="group")
        fig_b.update_layout(
            yaxis2=dict(overlaying="y", side="right", showgrid=False,
                tickfont=dict(color=MUTED, size=9), zeroline=False),
            margin=dict(t=24,b=100,l=8,r=40)
        )
        fig_b.update_xaxes(tickangle=-45, tickfont=dict(size=9, color=MUTED))
        st.markdown("**GF · GC · Diferencia**")
        st.plotly_chart(fig_b, use_container_width=True)

# ── ARGENTINA ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-divider'><div class='section-divider-line'></div><div class='section-divider-title'>Argentina</div><div class='section-divider-line' style='background:linear-gradient(90deg,transparent,#1e1e35)'></div></div>", unsafe_allow_html=True)

arg    = finished[(finished["home"]=="Argentina")|(finished["away"]=="Argentina")].copy()
arg_up = upcoming[(upcoming["home"]=="Argentina")|(upcoming["away"]=="Argentina")].copy()

if arg.empty and arg_up.empty:
    st.markdown("<p style='color:#33334a;font-size:0.85rem'>Argentina todavía no tiene partidos.</p>", unsafe_allow_html=True)
else:
    if not arg_up.empty:
        prox = arg_up.sort_values("fecha").iloc[0]
        fecha_str = prox["fecha"].strftime("%d %b · %H:%M UTC") if pd.notna(prox["fecha"]) else "—"
        rival = prox["away"] if prox["home"]=="Argentina" else prox["home"]
        st.markdown(f"""<div style='background:#0d0d1a;border:1px solid rgba(200,242,77,0.12);border-radius:14px;padding:20px 24px;margin-bottom:24px'>
            <div style='font-size:0.68rem;font-weight:600;color:#4d9df2;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px'>Próximo partido · {fecha_str}</div>
            <div style='font-size:1.2rem;font-weight:500'>Argentina vs {rival}</div>
        </div>""", unsafe_allow_html=True)

    if not arg.empty:
        arg_gf=arg_gc=arg_pts=0
        for _, row in arg.iterrows():
            if row["home"]=="Argentina":
                arg_gf+=row["goles_home"]; arg_gc+=row["goles_away"]
                if row["goles_home"]>row["goles_away"]: arg_pts+=3
                elif row["goles_home"]==row["goles_away"]: arg_pts+=1
            else:
                arg_gf+=row["goles_away"]; arg_gc+=row["goles_home"]
                if row["goles_away"]>row["goles_home"]: arg_pts+=3
                elif row["goles_away"]==row["goles_home"]: arg_pts+=1

        c1,c2,c3,c4,c5 = st.columns(5)
        for col,val,lbl in zip([c1,c2,c3,c4,c5],
            [len(arg),int(arg_gf),int(arg_gc),int(arg_gf-arg_gc),arg_pts],
            ["Partidos","GF","GC","DG","Puntos"]):
            with col:
                color = RED if lbl=="DG" and val<0 else ACCENT
                st.markdown(f"<div class='kpi-card'><div class='kpi-value' style='color:{color}'>{val}</div><div class='kpi-label'>{lbl}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            for _, row in arg.sort_values("fecha").iterrows():
                es_local = row["home"]=="Argentina"
                rival = row["away"] if es_local else row["home"]
                ga = int(row["goles_home"]) if es_local else int(row["goles_away"])
                gr = int(row["goles_away"]) if es_local else int(row["goles_home"])
                res = "Victoria" if ga>gr else ("Empate" if ga==gr else "Derrota")
                border = ACCENT if ga>gr else (MUTED if ga==gr else RED)
                res_color = ACCENT if ga>gr else (MUTED if ga==gr else RED)
                fecha_str = row["fecha"].strftime("%d %b") if pd.notna(row["fecha"]) else "—"
                st.markdown(f"""<div style='background:#0d0d1a;border:1px solid #1a1a2e;border-left:3px solid {border};border-radius:12px;padding:16px 20px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center'>
                    <div>
                        <div style='font-weight:500;font-size:0.9rem'>Argentina vs {rival}</div>
                        <div style='font-size:0.68rem;color:#33334a;margin-top:4px'>{'Local' if es_local else 'Visitante'} · {fecha_str}</div>
                    </div>
                    <div style='text-align:right'>
                        <div style='font-family:Space Grotesk;font-size:1.5rem;font-weight:700;color:{ACCENT}'>{ga} — {gr}</div>
                        <div style='font-size:0.68rem;color:{res_color};font-weight:600'>{res}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

        with col2:
            rival_data=[]
            for _, row in arg.iterrows():
                es_local = row["home"]=="Argentina"
                rival = row["away"] if es_local else row["home"]
                ga = int(row["goles_home"]) if es_local else int(row["goles_away"])
                gr = int(row["goles_away"]) if es_local else int(row["goles_home"])
                rival_data.append({"rival":rival,"Argentina":ga,"Rival":gr})
            df_riv = pd.DataFrame(rival_data)
            fig_a = go.Figure()
            fig_a.add_trace(go.Bar(name="Argentina", x=df_riv["rival"], y=df_riv["Argentina"],
                marker=dict(color=ACCENT, opacity=0.9, line=dict(width=0)),
                hovertemplate="Argentina: %{y}<extra></extra>"))
            fig_a.add_trace(go.Bar(name="Rival", x=df_riv["rival"], y=df_riv["Rival"],
                marker=dict(color=RED, opacity=0.9, line=dict(width=0)),
                hovertemplate="Rival: %{y}<extra></extra>"))
            fig_a.update_layout(**theme(height=300), barmode="group")
            st.plotly_chart(fig_a, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""<div style='border-top:1px solid #1a1a2e;padding:32px 0;display:flex;justify-content:space-between;align-items:center'>
    <div style='font-size:0.75rem;color:#22223a;font-family:Space Grotesk,sans-serif;font-weight:600;letter-spacing:0.1em'>
        MUNDIAL 2026 · DATA HUB
    </div>
    <div style='font-size:0.72rem;color:#22223a'>
        Diego Bouzada · Python · GitHub Actions · football-data.org
    </div>
    <div style='display:flex;gap:20px'>
        <a href='https://github.com/dbouzada/mundial-2026-data' style='font-size:0.72rem;color:#33334a;text-decoration:none;letter-spacing:0.05em'>GitHub</a>
        <a href='https://linkedin.com/in/bouzadadiego' style='font-size:0.72rem;color:#33334a;text-decoration:none;letter-spacing:0.05em'>LinkedIn</a>
    </div>
</div>""", unsafe_allow_html=True)
