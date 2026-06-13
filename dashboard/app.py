import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

st.set_page_config(
    page_title="Mundial 2026 — Data Hub",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_URL = "https://raw.githubusercontent.com/dbouzada/mundial-2026-data/main/data/processed"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0e0e0e; color: #f0f0f0; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; }
.metric-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 20px 24px; text-align: center; }
.metric-value { font-family: 'Space Grotesk', sans-serif; font-size: 2.4rem; font-weight: 700; color: #c8f24d; line-height: 1; }
.metric-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 6px; }
.resultado-card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; padding: 14px 20px; margin-bottom: 8px; }
.grupo-badge { background: #c8f24d; color: #0e0e0e; font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; }
.update-tag { font-size: 0.72rem; color: #555; padding: 4px 0; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=180)
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
finished = matches[matches["estado"] == "FINISHED"].copy()
finished["goles_home"]  = pd.to_numeric(finished["goles_home"],  errors="coerce")
finished["goles_away"]  = pd.to_numeric(finished["goles_away"],  errors="coerce")
finished["total_goles"] = finished["goles_home"] + finished["goles_away"]

with st.sidebar:
    st.markdown("## 🏆 Mundial 2026")
    st.markdown("**Data Hub** — Diego Bouzada")
    st.divider()
    seccion = st.radio("Sección", ["📊 Overview","⚽ Resultados","📋 Tabla","🥅 Goleadores","📈 Equipos","🇦🇷 Argentina"])
    st.divider()
    st.markdown(f"<div class='update-tag'>Actualizado: {meta.get('ultima_actualizacion','—')}</div>", unsafe_allow_html=True)

# ── OVERVIEW ──────────────────────────────────────────────────────────────────
if seccion == "📊 Overview":
    st.markdown("# Mundial 2026 — Data Hub")
    st.markdown("Análisis de datos en tiempo real. Pipeline: Python · GitHub Actions · Streamlit")
    st.divider()
    c1,c2,c3,c4 = st.columns(4)
    total_goles = int(finished["total_goles"].sum()) if not finished.empty else 0
    promedio    = round(finished["total_goles"].mean(), 2) if not finished.empty else 0
    for col, val, lbl in zip([c1,c2,c3,c4],
        [meta.get("partidos_terminados", len(finished)), total_goles, promedio, 104],
        ["Partidos jugados","Goles totales","Goles x partido","Partidos totales"]):
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{val}</div><div class='metric-label'>{lbl}</div></div>", unsafe_allow_html=True)

    if not finished.empty:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Goles por partido")
            fig = px.bar(finished.sort_values("fecha"),
                x=finished.sort_values("fecha").apply(lambda r: f"{r['home']} vs {r['away']}", axis=1),
                y="total_goles", color="total_goles",
                color_continuous_scale=["#1a1a1a","#c8f24d"],
                labels={"x":"","total_goles":"Goles"})
            fig.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
                coloraxis_showscale=False, xaxis_tickangle=-45, height=320, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown("### Resultados")
            if "ganador" in finished.columns:
                conteo = finished["ganador"].value_counts()
                labels_map = {"HOME_TEAM":"Local","AWAY_TEAM":"Visitante","DRAW":"Empate"}
                fig2 = go.Figure(go.Pie(
                    labels=[labels_map.get(l,l) for l in conteo.index],
                    values=conteo.values, hole=0.6,
                    marker_colors=["#c8f24d","#4d9df2","#f2784d"]))
                fig2.update_layout(paper_bgcolor="#0e0e0e", font_color="#f0f0f0", height=320,
                    legend=dict(bgcolor="#0e0e0e"))
                st.plotly_chart(fig2, use_container_width=True)

# ── RESULTADOS ────────────────────────────────────────────────────────────────
elif seccion == "⚽ Resultados":
    st.markdown("# Resultados")
    grupos = ["Todos"] + sorted(finished["grupo"].dropna().unique().tolist()) if not finished.empty else ["Todos"]
    grupo_sel = st.selectbox("Filtrar por grupo", grupos)
    df_show = finished if grupo_sel == "Todos" else finished[finished["grupo"] == grupo_sel]
    if df_show.empty:
        st.info("No hay partidos terminados todavía.")
    else:
        for _, row in df_show.sort_values("fecha").iterrows():
            grupo_txt = f"Grupo {row['grupo']}" if pd.notna(row.get("grupo")) else str(row.get("etapa",""))
            st.markdown(f"""<div class='resultado-card' style='display:flex;justify-content:space-between;align-items:center'>
                <div style='flex:1;text-align:right;font-weight:600'>{row['home']}</div>
                <div style='margin:0 20px;text-align:center'>
                    <span style='font-family:Space Grotesk;font-size:1.6rem;font-weight:700;color:#c8f24d'>
                        {int(row['goles_home'])} — {int(row['goles_away'])}
                    </span><br>
                    <span style='font-size:0.7rem;color:#666'>{row['fecha']}</span>
                </div>
                <div style='flex:1;font-weight:600'>{row['away']}</div>
                <span class='grupo-badge'>{grupo_txt}</span>
            </div>""", unsafe_allow_html=True)

# ── TABLA ─────────────────────────────────────────────────────────────────────
elif seccion == "📋 Tabla":
    st.markdown("# Tabla de posiciones")
    grupos = sorted(standings["grupo"].dropna().unique().tolist())
    grupo_sel = st.selectbox("Grupo", grupos)
    df_g = standings[standings["grupo"] == grupo_sel].sort_values("posicion")
    fig = go.Figure(data=[go.Table(
        header=dict(values=["Pos","Equipo","PJ","G","E","P","GF","GC","DG","PTS"],
            fill_color="#1a1a1a", font=dict(color="#c8f24d",size=13,family="Space Grotesk"),
            align="center", height=36),
        cells=dict(values=[df_g["posicion"],df_g["equipo"],df_g["pj"],df_g["ganados"],
            df_g["empatados"],df_g["perdidos"],df_g["gf"],df_g["gc"],df_g["dg"],df_g["puntos"]],
            fill_color=[["#161616" if i%2==0 else "#1a1a1a" for i in range(len(df_g))]],
            font=dict(color="#f0f0f0",size=13), align="center", height=34)
    )])
    fig.update_layout(paper_bgcolor="#0e0e0e", margin=dict(l=0,r=0,t=0,b=0), height=280)
    st.plotly_chart(fig, use_container_width=True)

# ── GOLEADORES ────────────────────────────────────────────────────────────────
elif seccion == "🥅 Goleadores":
    st.markdown("# Goleadores")
    top_n = st.slider("Top N jugadores", 5, len(scorers), min(10, len(scorers)))
    df_top = scorers.sort_values("goles", ascending=False).head(top_n)
    fig = px.bar(df_top, x="goles", y="jugador", orientation="h", color="goles",
        color_continuous_scale=["#1a1a1a","#c8f24d"], text="goles",
        hover_data=["equipo","asistencias"], labels={"goles":"Goles","jugador":""})
    fig.update_traces(textposition="outside")
    fig.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
        coloraxis_showscale=False, yaxis=dict(autorange="reversed"), height=max(300, top_n*42))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_top[["jugador","equipo","goles","asistencias","penales"]], use_container_width=True, hide_index=True)

# ── EQUIPOS ───────────────────────────────────────────────────────────────────
elif seccion == "📈 Equipos":
    st.markdown("# Rendimiento por equipo")
    if kpis.empty:
        st.info("Todavía no hay partidos terminados.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Puntos acumulados")
            fig = px.bar(kpis.sort_values("puntos"), x="puntos", y="equipo", orientation="h",
                color="puntos", color_continuous_scale=["#1a1a1a","#c8f24d"],
                labels={"puntos":"Puntos","equipo":""})
            fig.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
                coloraxis_showscale=False, height=max(300, len(kpis)*38))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown("### GF vs GC")
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="GF", x=kpis["equipo"], y=kpis["gf"], marker_color="#c8f24d"))
            fig2.add_trace(go.Bar(name="GC", x=kpis["equipo"], y=kpis["gc"], marker_color="#f2784d"))
            fig2.update_layout(barmode="group", paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e",
                font_color="#f0f0f0", legend=dict(bgcolor="#0e0e0e"), xaxis_tickangle=-45,
                height=max(300, len(kpis)*38))
            st.plotly_chart(fig2, use_container_width=True)

# ── ARGENTINA ─────────────────────────────────────────────────────────────────
elif seccion == "🇦🇷 Argentina":
    st.markdown("# 🇦🇷 Argentina")
    arg = finished[(finished["home"]=="Argentina")|(finished["away"]=="Argentina")].copy()
    if arg.empty:
        st.info("Argentina todavía no jugó ningún partido.")
    else:
        arg_gf = arg_gc = arg_pts = 0
        for _, row in arg.iterrows():
            if row["home"] == "Argentina":
                arg_gf += row["goles_home"]; arg_gc += row["goles_away"]
                if row["goles_home"] > row["goles_away"]: arg_pts += 3
                elif row["goles_home"] == row["goles_away"]: arg_pts += 1
            else:
                arg_gf += row["goles_away"]; arg_gc += row["goles_home"]
                if row["goles_away"] > row["goles_home"]: arg_pts += 3
                elif row["goles_away"] == row["goles_home"]: arg_pts += 1

        c1,c2,c3,c4 = st.columns(4)
        for col,val,lbl in zip([c1,c2,c3,c4],[len(arg),int(arg_gf),int(arg_gc),arg_pts],
            ["Partidos","Goles a favor","Goles en contra","Puntos"]):
            with col:
                st.markdown(f"<div class='metric-card'><div class='metric-value'>{val}</div><div class='metric-label'>{lbl}</div></div>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### Partidos")
        for _, row in arg.iterrows():
            es_local = row["home"] == "Argentina"
            rival = row["away"] if es_local else row["home"]
            ga = int(row["goles_home"]) if es_local else int(row["goles_away"])
            gr = int(row["goles_away"]) if es_local else int(row["goles_home"])
            res = "✅ Victoria" if ga > gr else ("🤝 Empate" if ga == gr else "❌ Derrota")
            st.markdown(f"""<div class='resultado-card' style='display:flex;justify-content:space-between;align-items:center'>
                <div style='flex:1;font-weight:600'>Argentina <span style='color:#888;font-size:0.8rem'>{'Local' if es_local else 'Visitante'}</span></div>
                <div style='margin:0 20px;text-align:center'>
                    <span style='font-family:Space Grotesk;font-size:1.6rem;font-weight:700;color:#c8f24d'>{ga} — {gr}</span>
                    <br><span style='font-size:0.7rem;color:#666'>{row['fecha']}</span>
                </div>
                <div style='flex:1;text-align:right;font-weight:600'>{rival}</div>
                <div style='margin-left:16px'>{res}</div>
            </div>""", unsafe_allow_html=True)
