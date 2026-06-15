import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO
import time

st.set_page_config(page_title="Mundial 2026 — Data Hub", page_icon="🏆", layout="wide")

BASE_URL = "https://raw.githubusercontent.com/dbouzada/mundial-2026-data/main/data/processed"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0a;
    color: #f0f0f0;
}
h1,h2,h3 { font-family: 'Space Grotesk', sans-serif; }
section[data-testid="stSidebar"] { display: none; }

.metric-card {
    background: linear-gradient(135deg, #1a1a1a 0%, #141414 100%);
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 22px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #c8f24d, #4d9df2);
}
.metric-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #c8f24d;
    line-height: 1;
}
.metric-label {
    font-size: 0.72rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 8px;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 52px 0 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e1e1e;
}
.section-icon {
    font-size: 1.4rem;
}
.section-title-text {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, #c8f24d, #f0f0f0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.resultado-card {
    background: #111;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.resultado-card:hover { border-color: #333; }
.resultado-card.victoria-home { border-left: 3px solid #c8f24d; }
.resultado-card.victoria-away { border-left: 3px solid #4d9df2; }
.resultado-card.empate { border-left: 3px solid #666; }

.grupo-badge {
    background: #c8f24d22;
    color: #c8f24d;
    border: 1px solid #c8f24d44;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    white-space: nowrap;
}

.next-card {
    background: linear-gradient(135deg, #111 0%, #161616 100%);
    border: 1px solid #222;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
}
.next-time { font-size:0.72rem; color:#c8f24d; font-weight:600; margin-bottom:6px; }
.next-match { font-weight:600; font-size:0.95rem; color:#f0f0f0; }

.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #1a0a0a;
    border: 1px solid #f2784d44;
    border-radius: 20px;
    padding: 6px 16px;
    margin-top: 8px;
}
.live-dot {
    width: 8px; height: 8px;
    background: #f2784d;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}
.live-text { font-size: 0.8rem; color: #f2784d; font-weight: 600; }

.update-tag { font-size: 0.72rem; color: #444; margin-top: 4px; }

@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.8)} }
</style>
""", unsafe_allow_html=True)

def section(icon, title):
    st.markdown(f"""<div class='section-header'>
        <span class='section-icon'>{icon}</span>
        <span class='section-title-text'>{title}</span>
    </div>""", unsafe_allow_html=True)

def clean_grupo(g):
    if not g or not isinstance(g, str): return g or ''
    return g.replace('GROUP_', 'Grupo ')

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

scorers["goles"]        = pd.to_numeric(scorers["goles"],       errors="coerce").fillna(0)
scorers["asistencias"]  = pd.to_numeric(scorers["asistencias"], errors="coerce").fillna(0)
scorers["penales"]      = pd.to_numeric(scorers["penales"],     errors="coerce").fillna(0)
scorers["goles_jugada"] = scorers["goles"] - scorers["penales"]

for col in ["gf","gc","dg","puntos","promedio_gf","pj"]:
    if col in kpis.columns:
        kpis[col] = pd.to_numeric(kpis[col], errors="coerce").fillna(0)

# ── HERO ──────────────────────────────────────────────────────────────────────
col_hero, col_live = st.columns([3,1])
with col_hero:
    st.markdown("# 🏆 Mundial 2026 — Data Hub")
    st.markdown("Análisis en tiempo real · Python · GitHub Actions · Streamlit")
    st.markdown(f"<div class='update-tag'>Actualizado: {meta.get('ultima_actualizacion','—')}</div>", unsafe_allow_html=True)
with col_live:
    if not in_play.empty:
        st.markdown(f"""<div class='live-badge'>
            <div class='live-dot'></div>
            <span class='live-text'>EN VIVO — {len(in_play)} partido(s)</span>
        </div>""", unsafe_allow_html=True)

# ── MÉTRICAS con contador animado ─────────────────────────────────────────────
section("📊", "Overview")

total_goles = int(finished["total_goles"].sum())  if not finished.empty else 0
promedio    = round(finished["total_goles"].mean(), 2) if not finished.empty else 0
max_goles   = int(finished["total_goles"].max())  if not finished.empty else 0
con_pts     = len(kpis[kpis["puntos"] > 0]) if not kpis.empty else 0
n_jugados   = meta.get("partidos_terminados", len(finished))

c1,c2,c3,c4,c5 = st.columns(5)
placeholders = [c.empty() for c in [c1,c2,c3,c4,c5]]
valores = [n_jugados, total_goles, promedio, max_goles, con_pts]
labels  = ["Partidos jugados","Goles totales","Goles × partido","Máx goles partido","Equipos con puntos"]

for i, (ph, val, lbl) in enumerate(zip(placeholders, valores, labels)):
    ph.markdown(f"<div class='metric-card'><div class='metric-value'>{val}</div><div class='metric-label'>{lbl}</div></div>", unsafe_allow_html=True)

# Sparkline mini debajo de métricas
if not finished.empty:
    goles_dia = finished.groupby("fecha")["total_goles"].sum().reset_index().sort_values("fecha")
    spark_fig = go.Figure()
    spark_fig.add_trace(go.Scatter(
        x=goles_dia["fecha"].dt.strftime("%d/%m"),
        y=goles_dia["total_goles"],
        fill="tozeroy", mode="lines",
        line=dict(color="#c8f24d", width=1.5),
        fillcolor="rgba(200,242,77,0.08)"
    ))
    spark_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=4,b=0), height=60,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False
    )
    st.plotly_chart(spark_fig, use_container_width=True)

# Gauge de goles por partido
if not finished.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=promedio,
            title={"text": "Goles promedio por partido", "font": {"color": "#888", "size": 13}},
            gauge={
                "axis": {"range": [0, 6], "tickcolor": "#444", "tickfont": {"color": "#666"}},
                "bar": {"color": "#c8f24d"},
                "bgcolor": "#1a1a1a",
                "bordercolor": "#2a2a2a",
                "steps": [
                    {"range": [0,2], "color": "#111"},
                    {"range": [2,4], "color": "#151515"},
                    {"range": [4,6], "color": "#1a1a1a"},
                ],
                "threshold": {"line": {"color": "#f2784d","width":2}, "thickness":0.75, "value": 2.7}
            },
            number={"font": {"color": "#c8f24d", "size": 36, "family": "Space Grotesk"}}
        ))
        gauge.update_layout(paper_bgcolor="#0a0a0a", font_color="#f0f0f0", height=240, margin=dict(t=30,b=10,l=20,r=20))
        st.plotly_chart(gauge, use_container_width=True)

    with col2:
        conteo = finished["ganador"].value_counts() if "ganador" in finished.columns else pd.Series()
        labels_map = {"HOME_TEAM":"Local","AWAY_TEAM":"Visitante","DRAW":"Empate"}
        fig_pie = go.Figure(go.Pie(
            labels=[labels_map.get(l,l) for l in conteo.index],
            values=conteo.values, hole=0.6,
            marker_colors=["#c8f24d","#4d9df2","#555"],
            textinfo="label+percent",
            textfont=dict(size=11)
        ))
        fig_pie.update_layout(
            paper_bgcolor="#0a0a0a", font_color="#f0f0f0", height=240,
            legend=dict(bgcolor="#0a0a0a", font_size=11),
            margin=dict(t=20,b=10,l=0,r=0),
            title=dict(text="Distribución de resultados", font=dict(color="#888", size=13), x=0)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col3:
        if not kpis.empty and kpis["gf"].sum() > 0:
            top3 = kpis.nlargest(3,"puntos")[["equipo","puntos","gf"]]
            fig_top = go.Figure()
            fig_top.add_trace(go.Bar(
                x=top3["equipo"], y=top3["puntos"],
                marker=dict(
                    color=["#c8f24d","#aad43a","#8ab82e"],
                    line=dict(color="#0a0a0a", width=1)
                ),
                text=top3["puntos"], textposition="outside",
                textfont=dict(color="#c8f24d", size=14, family="Space Grotesk")
            ))
            fig_top.update_layout(
                paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", font_color="#f0f0f0",
                height=240, margin=dict(t=30,b=10,l=0,r=0),
                title=dict(text="Top 3 por puntos", font=dict(color="#888", size=13), x=0),
                yaxis=dict(visible=False), xaxis=dict(tickfont=dict(size=11))
            )
            st.plotly_chart(fig_top, use_container_width=True)

# ── PRÓXIMOS PARTIDOS ─────────────────────────────────────────────────────────
section("🗓️", "Próximos partidos")

if upcoming.empty:
    st.info("No hay próximos partidos programados.")
else:
    proximos = upcoming.sort_values("fecha").head(6)
    cols = st.columns(3)
    for i, (_, row) in enumerate(proximos.iterrows()):
        fecha_str = row["fecha"].strftime("%d/%m · %H:%M UTC") if pd.notna(row["fecha"]) else "—"
        grupo_txt = clean_grupo(str(row.get("grupo",""))) if pd.notna(row.get("grupo")) else str(row.get("etapa",""))
        with cols[i % 3]:
            st.markdown(f"""<div class='next-card'>
                <div class='next-time'>{fecha_str} · <span class='grupo-badge'>{grupo_txt}</span></div>
                <div class='next-match'>{row['home']} vs {row['away']}</div>
            </div>""", unsafe_allow_html=True)

# ── RESULTADOS ────────────────────────────────────────────────────────────────
section("⚽", "Resultados")

def resultado_card(row):
    gh = int(row["goles_home"]) if pd.notna(row["goles_home"]) else "—"
    ga = int(row["goles_away"]) if pd.notna(row["goles_away"]) else "—"
    grupo_txt = clean_grupo(str(row.get("grupo",""))) if pd.notna(row.get("grupo")) else ""
    fecha_str = row["fecha"].strftime("%d/%m") if pd.notna(row["fecha"]) else "—"
    ganador   = row.get("ganador","")
    if ganador == "HOME_TEAM":   css_class = "victoria-home"
    elif ganador == "AWAY_TEAM": css_class = "victoria-away"
    else:                         css_class = "empate"
    return f"""<div class='resultado-card {css_class}'>
        <div style='display:flex;justify-content:space-between;align-items:center'>
            <div style='flex:2;text-align:right;font-weight:600;font-size:0.95rem'>{row['home']}</div>
            <div style='flex:1.5;text-align:center'>
                <div style='font-family:Space Grotesk;font-size:1.5rem;font-weight:700;color:#c8f24d;line-height:1'>{gh} — {ga}</div>
                <div style='font-size:0.65rem;color:#555;margin-top:3px'>{fecha_str}</div>
            </div>
            <div style='flex:2;font-weight:600;font-size:0.95rem'>{row['away']}</div>
            <div><span class='grupo-badge'>{grupo_txt}</span></div>
        </div>
    </div>"""

if not finished.empty:
    ultimos = finished.sort_values("fecha", ascending=False).head(6)
    col1, col2 = st.columns(2)
    for i, (_, row) in enumerate(ultimos.iterrows()):
        target = col1 if i % 2 == 0 else col2
        target.markdown(resultado_card(row), unsafe_allow_html=True)

    with st.expander(f"📋 Ver todos los resultados ({len(finished)} partidos)"):
        grupos = ["Todos"] + sorted(finished["grupo_clean"].dropna().unique().tolist())
        grupo_sel = st.selectbox("Grupo", grupos, key="grupo_todos")
        df_show = finished if grupo_sel == "Todos" else finished[finished["grupo_clean"] == grupo_sel]
        col1, col2 = st.columns(2)
        for i, (_, row) in enumerate(df_show.sort_values("fecha", ascending=False).iterrows()):
            target = col1 if i % 2 == 0 else col2
            target.markdown(resultado_card(row), unsafe_allow_html=True)

# ── ANÁLISIS ──────────────────────────────────────────────────────────────────
if not finished.empty:
    section("📈", "Análisis del torneo")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Goles acumulados por día**")
        gd = finished.groupby("fecha")["total_goles"].sum().reset_index().sort_values("fecha")
        gd["fecha_str"] = gd["fecha"].dt.strftime("%d/%m")
        gd["acumulado"] = gd["total_goles"].cumsum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=gd["fecha_str"], y=gd["acumulado"],
            fill="tozeroy", line=dict(color="#c8f24d", width=2.5),
            fillcolor="rgba(200,242,77,0.08)", name="Acumulado"))
        fig.add_trace(go.Bar(x=gd["fecha_str"], y=gd["total_goles"],
            marker_color="#4d9df255", name="Por día", yaxis="y2"))
        fig.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", font_color="#f0f0f0",
            legend=dict(bgcolor="#0a0a0a"), height=300, margin=dict(t=20,b=0),
            yaxis=dict(title="Acumulado", gridcolor="#1a1a1a"),
            yaxis2=dict(overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Goles por grupo**")
        if "grupo_clean" in finished.columns:
            gg = finished.groupby("grupo_clean")["total_goles"].agg(["sum","mean","count"]).reset_index()
            gg.columns = ["grupo","total","promedio","partidos"]
            fig3 = px.bar(gg.sort_values("total", ascending=False),
                x="grupo", y="total", color="promedio",
                color_continuous_scale=["#1a1a1a","#c8f24d"],
                text="total", labels={"grupo":"","total":"Goles"})
            fig3.update_traces(textposition="outside", textfont=dict(color="#c8f24d", size=13))
            fig3.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", font_color="#f0f0f0",
                coloraxis_showscale=False, height=300, margin=dict(t=20,b=0),
                xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
            st.plotly_chart(fig3, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Partidos más goleadores**")
        tp = finished.nlargest(8, "total_goles").copy()
        tp["partido"] = tp.apply(lambda r: f"{r['home']} vs {r['away']}", axis=1)
        fig4 = px.bar(tp.sort_values("total_goles"),
            x="total_goles", y="partido", orientation="h",
            color="total_goles", color_continuous_scale=["#2a2a2a","#c8f24d"],
            text="total_goles", labels={"total_goles":"Goles","partido":""})
        fig4.update_traces(textposition="outside", textfont=dict(color="#c8f24d"))
        fig4.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", font_color="#f0f0f0",
            coloraxis_showscale=False, height=300, margin=dict(t=20,b=0),
            xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        st.markdown("**Goles por partido (stacked)**")
        tl = finished[finished["total_goles"].notna()].sort_values("fecha").copy().reset_index(drop=True)
        tl["goles_home"] = tl["goles_home"].fillna(0).astype(int)
        tl["goles_away"] = tl["goles_away"].fillna(0).astype(int)
        tl["label"] = tl.apply(lambda r: f"{r['home']} vs {r['away']}", axis=1)
        fig_tl = go.Figure()
        fig_tl.add_trace(go.Bar(name="Local", x=tl["label"], y=tl["goles_home"], marker_color="#c8f24d"))
        fig_tl.add_trace(go.Bar(name="Visitante", x=tl["label"], y=tl["goles_away"], marker_color="#4d9df2"))
        fig_tl.update_layout(barmode="stack", paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
            font_color="#f0f0f0", legend=dict(bgcolor="#0a0a0a"),
            height=300, margin=dict(t=20, b=100),
            xaxis=dict(tickangle=-45, gridcolor="#1a1a1a"),
            yaxis=dict(gridcolor="#1a1a1a"))
        st.plotly_chart(fig_tl, use_container_width=True)

    # Heatmap
    st.markdown("**Heatmap — goles por grupo y día**")
    if "grupo_clean" in finished.columns:
        finished["fecha_str"] = finished["fecha"].dt.strftime("%d/%m")
        hm = finished.groupby(["grupo_clean","fecha_str"])["total_goles"].sum().reset_index()
        hm_pivot = hm.pivot(index="grupo_clean", columns="fecha_str", values="total_goles").fillna(0)
        fig_hm = go.Figure(go.Heatmap(
            z=hm_pivot.values,
            x=hm_pivot.columns.tolist(),
            y=hm_pivot.index.tolist(),
            colorscale=[[0,"#0a0a0a"],[0.3,"#1a2a0a"],[0.7,"#4a7a0a"],[1,"#c8f24d"]],
            showscale=True,
            text=hm_pivot.values,
            texttemplate="%{text:.0f}",
            textfont=dict(size=12, color="#f0f0f0")
        ))
        fig_hm.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", font_color="#f0f0f0",
            height=320, margin=dict(t=20,b=0),
            xaxis=dict(title="Fecha"), yaxis=dict(title="Grupo"))
        st.plotly_chart(fig_hm, use_container_width=True)

# ── TABLA DE POSICIONES ───────────────────────────────────────────────────────
section("📋", "Tabla de posiciones")

grupos_list = sorted(standings["grupo_clean"].dropna().unique().tolist())
for row_grupos in [grupos_list[i:i+4] for i in range(0, len(grupos_list), 4)]:
    cols = st.columns(4)
    for j, grupo in enumerate(row_grupos):
        df_g = standings[standings["grupo_clean"] == grupo].sort_values("posicion")
        max_pts = df_g["puntos"].max() if len(df_g) > 0 else 1
        with cols[j]:
            st.markdown(f"**{grupo}**")
            for _, row in df_g.iterrows():
                pos = int(row["posicion"])
                pts = int(row["puntos"])
                pct = pts / max(max_pts, 1)
                color = "#c8f24d" if pos <= 2 else "#444"
                bar_color = "#c8f24d22" if pos <= 2 else "#1a1a1a"
                st.markdown(f"""<div style='background:{bar_color};border:1px solid #1e1e1e;border-radius:8px;padding:8px 12px;margin-bottom:6px;position:relative;overflow:hidden'>
                    <div style='position:absolute;left:0;top:0;bottom:0;width:{int(pct*100)}%;background:{color}11;border-radius:8px'></div>
                    <div style='display:flex;justify-content:space-between;align-items:center;position:relative'>
                        <span style='color:{color};font-weight:700;font-size:0.8rem;width:20px'>{pos}</span>
                        <span style='flex:1;font-size:0.82rem;font-weight:500;margin:0 8px'>{row["equipo"]}</span>
                        <span style='font-size:0.72rem;color:#666'>{int(row["pj"])}PJ</span>
                        <span style='font-family:Space Grotesk;font-weight:700;color:{color};margin-left:8px;min-width:24px;text-align:right'>{pts}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

# ── GOLEADORES ────────────────────────────────────────────────────────────────
section("🥅", "Goleadores")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Top goleadores**")
    top_n = st.slider("Top N", 5, max(5,len(scorers)), min(10,len(scorers)), key="top_n")
    df_top = scorers.sort_values("goles", ascending=False).head(top_n).copy()
    medals = ["🥇","🥈","🥉"] + ["" for _ in range(len(df_top)-3)]
    df_top["label"] = [f"{medals[i]} {row}" for i, row in enumerate(df_top["jugador"])]

    # Tabla con progress bars
    max_goles_top = df_top["goles"].max()
    for _, row in df_top.iterrows():
        pct = int(row["goles"] / max(max_goles_top,1) * 100)
        medal = medals[list(df_top.index).index(_)] if _ in list(df_top.index) else ""
        st.markdown(f"""<div style='background:#111;border:1px solid #1e1e1e;border-radius:10px;padding:12px 16px;margin-bottom:6px'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px'>
                <span style='font-weight:600;font-size:0.9rem'>{row["jugador"]}</span>
                <div>
                    <span style='font-family:Space Grotesk;font-size:1.2rem;font-weight:700;color:#c8f24d'>{int(row["goles"])}</span>
                    <span style='font-size:0.7rem;color:#555;margin-left:4px'>goles</span>
                    <span style='font-size:0.7rem;color:#444;margin-left:8px'>{int(row["asistencias"])} ast</span>
                </div>
            </div>
            <div style='font-size:0.72rem;color:#555;margin-bottom:6px'>{row["equipo"]}</div>
            <div style='background:#1a1a1a;border-radius:4px;height:4px'>
                <div style='background:linear-gradient(90deg,#c8f24d,#8ab82e);width:{pct}%;height:4px;border-radius:4px'></div>
            </div>
        </div>""", unsafe_allow_html=True)

with col2:
    st.markdown("**Goles de jugada vs penal**")
    df_top2 = scorers.sort_values("goles", ascending=False).head(10)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Jugada", x=df_top2["jugador"], y=df_top2["goles_jugada"], marker_color="#c8f24d"))
    fig2.add_trace(go.Bar(name="Penal",  x=df_top2["jugador"], y=df_top2["penales"],      marker_color="#f2784d"))
    fig2.update_layout(barmode="stack", paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
        font_color="#f0f0f0", legend=dict(bgcolor="#0a0a0a"), xaxis_tickangle=-35,
        height=300, margin=dict(t=20,b=80), xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Participaciones en gol**")
    df_part = scorers.copy()
    df_part["participaciones"] = df_part["goles"] + df_part["asistencias"]
    df_part = df_part[df_part["participaciones"]>0].sort_values("participaciones", ascending=False).head(10)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Goles",       x=df_part["jugador"], y=df_part["goles"],       marker_color="#c8f24d"))
    fig3.add_trace(go.Bar(name="Asistencias", x=df_part["jugador"], y=df_part["asistencias"], marker_color="#4d9df2"))
    fig3.update_layout(barmode="stack", paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
        font_color="#f0f0f0", legend=dict(bgcolor="#0a0a0a"), xaxis_tickangle=-35,
        height=280, margin=dict(t=20,b=80), xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
    st.plotly_chart(fig3, use_container_width=True)

# ── RENDIMIENTO ───────────────────────────────────────────────────────────────
if not kpis.empty:
    section("📊", "Rendimiento por equipo")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Puntos acumulados**")
        fig = px.bar(kpis.sort_values("puntos"), x="puntos", y="equipo", orientation="h",
            color="puntos", color_continuous_scale=["#1a1a1a","#c8f24d"],
            text="puntos", labels={"puntos":"","equipo":""})
        fig.update_traces(textposition="outside", textfont=dict(color="#c8f24d"))
        fig.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", font_color="#f0f0f0",
            coloraxis_showscale=False, height=max(320,len(kpis)*38), margin=dict(t=20,r=40),
            xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Ofensivo vs defensivo**")
        fig2 = px.scatter(kpis, x="gf", y="gc", text="equipo", size="pj",
            color="puntos", color_continuous_scale=["#f2784d","#c8f24d"],
            labels={"gf":"Goles a favor","gc":"Goles en contra","puntos":"Puntos"})
        fig2.update_traces(textposition="top center", textfont_size=9)
        fig2.add_hline(y=kpis["gc"].mean(), line_dash="dot", line_color="#333")
        fig2.add_vline(x=kpis["gf"].mean(), line_dash="dot", line_color="#333")
        fig2.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", font_color="#f0f0f0",
            height=max(320,len(kpis)*38), margin=dict(t=20),
            xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
        st.plotly_chart(fig2, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**GF vs GC**")
        ks = kpis.sort_values("gf", ascending=False)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="GF", x=ks["equipo"], y=ks["gf"], marker_color="#c8f24d"))
        fig3.add_trace(go.Bar(name="GC", x=ks["equipo"], y=ks["gc"], marker_color="#f2784d"))
        fig3.update_layout(barmode="group", paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
            font_color="#f0f0f0", legend=dict(bgcolor="#0a0a0a"), xaxis_tickangle=-45,
            height=380, margin=dict(t=20,b=120),
            xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.markdown("**Diferencia de goles**")
        kd = kpis.sort_values("dg", ascending=True)
        colors_dg = ["#c8f24d" if v >= 0 else "#f2784d" for v in kd["dg"]]
        fig4 = go.Figure(go.Bar(x=kd["dg"], y=kd["equipo"], orientation="h",
            marker_color=colors_dg, text=kd["dg"]))
        fig4.add_vline(x=0, line_color="#333")
        fig4.update_traces(textposition="outside")
        fig4.update_layout(paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", font_color="#f0f0f0",
            height=380, margin=dict(t=20,r=60),
            xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
        st.plotly_chart(fig4, use_container_width=True)

# ── AVANZADO ──────────────────────────────────────────────────────────────────
if not finished.empty and not kpis.empty:
    section("🔬", "Análisis avanzado")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Treemap — goles por equipo**")
        kpis_gf = kpis[kpis["gf"] > 0].copy()
        if not kpis_gf.empty:
            fig_tree = px.treemap(kpis_gf, path=["equipo"], values="gf",
                color="gf", color_continuous_scale=["#111","#c8f24d"])
            fig_tree.update_traces(textinfo="label+value", textfont_size=12,
                marker=dict(line=dict(color="#0a0a0a", width=2)))
            fig_tree.update_layout(paper_bgcolor="#0a0a0a", font_color="#f0f0f0",
                coloraxis_showscale=False, height=380, margin=dict(t=20))
            st.plotly_chart(fig_tree, use_container_width=True)

    with col2:
        st.markdown("**Radar — top 5 equipos**")
        if len(kpis) >= 3:
            top5 = kpis.nlargest(5,"puntos")
            cats = ["Puntos","GF","Prom GF×3","DG+"]
            fig_r = go.Figure()
            palette = ["#c8f24d","#4d9df2","#f2784d","#a855f7","#f59e0b"]
            for i, (_, row) in enumerate(top5.iterrows()):
                fig_r.add_trace(go.Scatterpolar(
                    r=[row["puntos"], row["gf"], row["promedio_gf"]*3, max(row["dg"],0)],
                    theta=cats, fill="toself", name=row["equipo"],
                    line=dict(color=palette[i], width=2),
                    fillcolor=palette[i].replace("#","rgba(") + ",0.1)" if "#" in palette[i] else palette[i],
                    opacity=0.8
                ))
            fig_r.update_layout(
                polar=dict(bgcolor="#111",
                    radialaxis=dict(visible=True, color="#333", gridcolor="#222"),
                    angularaxis=dict(color="#555", gridcolor="#222")),
                paper_bgcolor="#0a0a0a", font_color="#f0f0f0",
                legend=dict(bgcolor="#0a0a0a", font_size=11),
                height=380, margin=dict(t=20))
            st.plotly_chart(fig_r, use_container_width=True)

# ── ARGENTINA ─────────────────────────────────────────────────────────────────
section("🇦🇷", "Argentina")

arg    = finished[(finished["home"]=="Argentina")|(finished["away"]=="Argentina")].copy()
arg_up = upcoming[(upcoming["home"]=="Argentina")|(upcoming["away"]=="Argentina")].copy()

if arg.empty and arg_up.empty:
    st.info("Argentina todavía no tiene partidos registrados.")
else:
    if not arg_up.empty:
        prox = arg_up.sort_values("fecha").iloc[0]
        fecha_str = prox["fecha"].strftime("%d/%m · %H:%M UTC") if pd.notna(prox["fecha"]) else "—"
        rival = prox["away"] if prox["home"]=="Argentina" else prox["home"]
        st.markdown(f"""<div style='background:linear-gradient(135deg,#111,#161616);border:1px solid #c8f24d22;border-radius:12px;padding:16px 20px;margin-bottom:20px'>
            <div style='font-size:0.75rem;color:#c8f24d;font-weight:600;margin-bottom:6px'>⏳ Próximo partido · {fecha_str}</div>
            <div style='font-size:1.1rem;font-weight:600'>🇦🇷 Argentina vs {rival}</div>
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
            ["Partidos","Goles a favor","En contra","Diferencia","Puntos"]):
            with col:
                color = "#f2784d" if lbl=="Diferencia" and val<0 else "#c8f24d"
                st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:{color}'>{val}</div><div class='metric-label'>{lbl}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Partidos**")
            for _, row in arg.sort_values("fecha").iterrows():
                es_local = row["home"]=="Argentina"
                rival    = row["away"] if es_local else row["home"]
                ga = int(row["goles_home"]) if es_local else int(row["goles_away"])
                gr = int(row["goles_away"]) if es_local else int(row["goles_home"])
                res = "✅ Victoria" if ga>gr else ("🤝 Empate" if ga==gr else "❌ Derrota")
                color_border = "#c8f24d" if ga>gr else ("#555" if ga==gr else "#f2784d")
                fecha_str = row["fecha"].strftime("%d/%m") if pd.notna(row["fecha"]) else "—"
                st.markdown(f"""<div style='background:#111;border:1px solid #1e1e1e;border-left:3px solid {color_border};border-radius:10px;padding:14px 16px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between'>
                    <div>
                        <div style='font-weight:600;font-size:0.9rem'>🇦🇷 Argentina vs {rival}</div>
                        <div style='font-size:0.72rem;color:#555;margin-top:2px'>{'Local' if es_local else 'Visitante'} · {fecha_str}</div>
                    </div>
                    <div style='text-align:right'>
                        <div style='font-family:Space Grotesk;font-size:1.4rem;font-weight:700;color:#c8f24d'>{ga} — {gr}</div>
                        <div style='font-size:0.72rem;color:#666'>{res}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown("**Argentina vs rivales**")
            rival_data=[]
            for _, row in arg.iterrows():
                es_local = row["home"]=="Argentina"
                rival    = row["away"] if es_local else row["home"]
                ga = int(row["goles_home"]) if es_local else int(row["goles_away"])
                gr = int(row["goles_away"]) if es_local else int(row["goles_home"])
                rival_data.append({"rival":rival,"Argentina":ga,"Rival":gr})
            df_riv = pd.DataFrame(rival_data)
            fig_a = go.Figure()
            fig_a.add_trace(go.Bar(name="Argentina", x=df_riv["rival"], y=df_riv["Argentina"], marker_color="#c8f24d"))
            fig_a.add_trace(go.Bar(name="Rival",     x=df_riv["rival"], y=df_riv["Rival"],     marker_color="#f2784d"))
            fig_a.update_layout(barmode="group", paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
                font_color="#f0f0f0", legend=dict(bgcolor="#0a0a0a"), height=300, margin=dict(t=20),
                xaxis=dict(gridcolor="#1a1a1a"), yaxis=dict(gridcolor="#1a1a1a"))
            st.plotly_chart(fig_a, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<div style='border-top:1px solid #1a1a1a;padding:24px 0;text-align:center;color:#333;font-size:0.8rem'>
    Construido por <strong style='color:#555'>Diego Bouzada</strong> · 
    Python · GitHub Actions · football-data.org · 
    <a href='https://github.com/dbouzada/mundial-2026-data' style='color:#c8f24d44;text-decoration:none'>GitHub ↗</a> · 
    <a href='https://linkedin.com/in/bouzadadiego' style='color:#c8f24d44;text-decoration:none'>LinkedIn ↗</a>
</div>""", unsafe_allow_html=True)
