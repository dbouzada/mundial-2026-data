import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO
from datetime import datetime, timezone

st.set_page_config(page_title="Mundial 2026 — Data Hub", page_icon="🏆", layout="wide")

BASE_URL = "https://raw.githubusercontent.com/dbouzada/mundial-2026-data/main/data/processed"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0e0e0e; color: #f0f0f0; }
h1,h2,h3 { font-family: 'Space Grotesk', sans-serif; }
section[data-testid="stSidebar"] { display: none; }
.metric-card { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:12px; padding:20px 24px; text-align:center; }
.metric-value { font-family:'Space Grotesk',sans-serif; font-size:2.4rem; font-weight:700; color:#c8f24d; line-height:1; }
.metric-label { font-size:0.75rem; color:#888; text-transform:uppercase; letter-spacing:0.1em; margin-top:6px; }
.resultado-card { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:10px; padding:14px 20px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; }
.grupo-badge { background:#c8f24d; color:#0e0e0e; font-size:0.7rem; font-weight:700; padding:3px 8px; border-radius:4px; white-space:nowrap; margin-left:8px; }
.section-title { font-family:'Space Grotesk',sans-serif; font-size:1.5rem; font-weight:700; margin:48px 0 16px; padding-top:24px; border-top:1px solid #2a2a2a; }
.update-tag { font-size:0.72rem; color:#555; margin-top:4px; }
.next-card { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:10px; padding:16px 20px; margin-bottom:8px; }
.next-time { font-size:0.75rem; color:#c8f24d; font-weight:600; margin-bottom:4px; }
.next-match { font-weight:600; font-size:1rem; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
</style>
""", unsafe_allow_html=True)

# ── BANDERAS ──────────────────────────────────────────────────────────────────
FLAGS = {
    'Argentina':'🇦🇷','Brazil':'🇧🇷','France':'🇫🇷','Germany':'🇩🇪','Spain':'🇪🇸',
    'Portugal':'🇵🇹','Netherlands':'🇳🇱','Belgium':'🇧🇪','Italy':'🇮🇹','Uruguay':'🇺🇾',
    'Mexico':'🇲🇽','United States':'🇺🇸','Canada':'🇨🇦','Japan':'🇯🇵','South Korea':'🇰🇷',
    'Australia':'🇦🇺','Morocco':'🇲🇦','Senegal':'🇸🇳','Nigeria':'🇳🇬','Egypt':'🇪🇬',
    'South Africa':'🇿🇦','Colombia':'🇨🇴','Chile':'🇨🇱','Ecuador':'🇪🇨','Peru':'🇵🇪',
    'Paraguay':'🇵🇾','Bolivia':'🇧🇴','Switzerland':'🇨🇭','Croatia':'🇭🇷','Serbia':'🇷🇸',
    'Denmark':'🇩🇰','Poland':'🇵🇱','Sweden':'🇸🇪','Austria':'🇦🇹','Czech Republic':'🇨🇿',
    'Czechia':'🇨🇿','Hungary':'🇭🇺','Scotland':'🏴󠁧󠁢󠁳󠁣󠁴󠁿','Wales':'🏴󠁧󠁢󠁷󠁬󠁳󠁿','Turkey':'🇹🇷',
    'Ukraine':'🇺🇦','Slovakia':'🇸🇰','Romania':'🇷🇴','Greece':'🇬🇷','Saudi Arabia':'🇸🇦',
    'Iran':'🇮🇷','Qatar':'🇶🇦','China':'🇨🇳','Indonesia':'🇮🇩','New Zealand':'🇳🇿',
    'Jamaica':'🇯🇲','Haiti':'🇭🇹','Honduras':'🇭🇳','Costa Rica':'🇨🇷','Panama':'🇵🇦',
    'Bosnia and Herzegovina':'🇧🇦','Algeria':'🇩🇿','Ivory Coast':'🇨🇮','Mali':'🇲🇱',
    'Cape Verde':'🇨🇻','Tunisia':'🇹🇳','Cameroon':'🇨🇲','Ghana':'🇬🇭','Venezuela':'🇻🇪',
    'El Salvador':'🇸🇻','Guatemala':'🇬🇹','Cuba':'🇨🇺','Curaçao':'🇨🇼','Curacao':'🇨🇼',
    'DR Congo':'🇨🇩','Congo DR':'🇨🇩','Morocco':'🇲🇦','Iraq':'🇮🇶','Norway':'🇳🇴',
    'Finland':'🇫🇮','Ireland':'🇮🇪','Israel':'🇮🇱','Georgia':'🇬🇪',
}

def flag(team):
    if not team or not isinstance(team, str): return ''
    for key, emoji in FLAGS.items():
        if key.lower() == team.lower() or team.lower() in key.lower() or key.lower() in team.lower():
            return emoji
    return ''

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

# Procesar
matches["goles_home"]  = pd.to_numeric(matches["goles_home"],  errors="coerce")
matches["goles_away"]  = pd.to_numeric(matches["goles_away"],  errors="coerce")
matches["total_goles"] = matches["goles_home"] + matches["goles_away"]
matches["fecha"]       = pd.to_datetime(matches["fecha"], errors="coerce")
matches["grupo_clean"] = matches["grupo"].apply(clean_grupo)

finished = matches[matches["estado"] == "FINISHED"].copy()
upcoming = matches[matches["estado"].isin(["TIMED","SCHEDULED"])].copy()

standings["grupo_clean"] = standings["grupo"].apply(clean_grupo)

scorers["goles"]        = pd.to_numeric(scorers["goles"],        errors="coerce").fillna(0)
scorers["asistencias"]  = pd.to_numeric(scorers["asistencias"],  errors="coerce").fillna(0)
scorers["penales"]      = pd.to_numeric(scorers["penales"],      errors="coerce").fillna(0)
scorers["goles_jugada"] = scorers["goles"] - scorers["penales"]

kpis["gf"]           = pd.to_numeric(kpis.get("gf",           pd.Series()), errors="coerce").fillna(0)
kpis["gc"]           = pd.to_numeric(kpis.get("gc",           pd.Series()), errors="coerce").fillna(0)
kpis["dg"]           = pd.to_numeric(kpis.get("dg",           pd.Series()), errors="coerce").fillna(0)
kpis["puntos"]       = pd.to_numeric(kpis.get("puntos",       pd.Series()), errors="coerce").fillna(0)
kpis["promedio_gf"]  = pd.to_numeric(kpis.get("promedio_gf",  pd.Series()), errors="coerce").fillna(0)
kpis["pj"]           = pd.to_numeric(kpis.get("pj",           pd.Series()), errors="coerce").fillna(1)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("# 🏆 Mundial 2026 — Data Hub")
st.markdown("Análisis de datos en tiempo real · Python · GitHub Actions · Streamlit")
st.markdown(f"<div class='update-tag'>Última actualización: {meta.get('ultima_actualizacion','—')}</div>", unsafe_allow_html=True)

hay_en_curso = not matches[matches["estado"] == "IN_PLAY"].empty
if hay_en_curso:
    st.markdown("""<div style='display:inline-flex;align-items:center;gap:8px;background:#1a1a1a;border:1px solid #c8f24d33;border-radius:20px;padding:6px 14px;margin-top:8px'>
        <span style='width:8px;height:8px;background:#c8f24d;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite'></span>
        <span style='font-size:0.8rem;color:#c8f24d;font-weight:600'>PARTIDO EN CURSO</span>
    </div>""", unsafe_allow_html=True)

# ── MÉTRICAS ──────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📊 Overview</div>", unsafe_allow_html=True)
total_goles  = int(finished["total_goles"].sum())  if not finished.empty else 0
promedio     = round(finished["total_goles"].mean(), 2) if not finished.empty else 0
max_goles    = int(finished["total_goles"].max())  if not finished.empty else 0
con_pts      = len(kpis[kpis["puntos"] > 0]) if not kpis.empty else 0

c1,c2,c3,c4,c5 = st.columns(5)
for col,val,lbl in zip([c1,c2,c3,c4,c5],
    [meta.get("partidos_terminados", len(finished)), total_goles, promedio, max_goles, con_pts],
    ["Partidos jugados","Goles totales","Goles x partido","Máx goles partido","Equipos con puntos"]):
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{val}</div><div class='metric-label'>{lbl}</div></div>", unsafe_allow_html=True)

# ── PRÓXIMOS PARTIDOS ─────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🗓️ Próximos partidos</div>", unsafe_allow_html=True)
if upcoming.empty:
    st.info("No hay próximos partidos programados.")
else:
    proximos = upcoming.sort_values("fecha").head(6)
    cols = st.columns(3)
    for i, (_, row) in enumerate(proximos.iterrows()):
        fecha_str = row["fecha"].strftime("%d/%m %H:%M") if pd.notna(row["fecha"]) else "—"
        grupo_txt = clean_grupo(str(row.get("grupo",""))) if pd.notna(row.get("grupo")) else str(row.get("etapa",""))
        fh, fa = flag(row["home"]), flag(row["away"])
        with cols[i % 3]:
            st.markdown(f"""<div class='next-card'>
                <div class='next-time'>{fecha_str} UTC · {grupo_txt}</div>
                <div class='next-match'>{fh} {row['home']} vs {fa} {row['away']}</div>
            </div>""", unsafe_allow_html=True)

# ── RESULTADOS ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>⚽ Resultados</div>", unsafe_allow_html=True)

def render_resultado(row):
    gh = int(row['goles_home']) if pd.notna(row['goles_home']) else '—'
    ga = int(row['goles_away']) if pd.notna(row['goles_away']) else '—'
    grupo_txt = clean_grupo(str(row.get("grupo",""))) if pd.notna(row.get("grupo")) else str(row.get("etapa",""))
    fecha_str = row["fecha"].strftime("%d/%m") if pd.notna(row["fecha"]) else "—"
    fh, fa = flag(row["home"]), flag(row["away"])
    return f"""<div class='resultado-card'>
        <div style='flex:1;text-align:right;font-weight:600'>{fh} {row['home']}</div>
        <div style='margin:0 16px;text-align:center'>
            <span style='font-family:Space Grotesk;font-size:1.4rem;font-weight:700;color:#c8f24d'>{gh} — {ga}</span>
            <br><span style='font-size:0.7rem;color:#666'>{fecha_str}</span>
        </div>
        <div style='flex:1;font-weight:600'>{fa} {row['away']}</div>
        <span class='grupo-badge'>{grupo_txt}</span>
    </div>"""

if not finished.empty:
    ultimos = finished.sort_values("fecha", ascending=False).head(6)
    col1, col2 = st.columns(2)
    for i, (_, row) in enumerate(ultimos.iterrows()):
        if i % 2 == 0: col1.markdown(render_resultado(row), unsafe_allow_html=True)
        else:           col2.markdown(render_resultado(row), unsafe_allow_html=True)

    with st.expander(f"Ver todos los resultados ({len(finished)} partidos)"):
        grupos = ["Todos"] + sorted(finished["grupo_clean"].dropna().unique().tolist())
        grupo_sel = st.selectbox("Filtrar por grupo", grupos, key="grupo_todos")
        df_show = finished if grupo_sel == "Todos" else finished[finished["grupo_clean"] == grupo_sel]
        col1, col2 = st.columns(2)
        for i, (_, row) in enumerate(df_show.sort_values("fecha", ascending=False).iterrows()):
            if i % 2 == 0: col1.markdown(render_resultado(row), unsafe_allow_html=True)
            else:           col2.markdown(render_resultado(row), unsafe_allow_html=True)

# ── ANÁLISIS DEL TORNEO ───────────────────────────────────────────────────────
if not finished.empty:
    st.markdown("<div class='section-title'>📈 Análisis del torneo</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Goles acumulados por día**")
        goles_dia = finished.groupby("fecha")["total_goles"].sum().reset_index()
        goles_dia = goles_dia.sort_values("fecha")
        goles_dia["fecha_str"] = goles_dia["fecha"].dt.strftime("%d/%m")
        goles_dia["acumulado"] = goles_dia["total_goles"].cumsum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=goles_dia["fecha_str"], y=goles_dia["acumulado"],
            fill="tozeroy", line=dict(color="#c8f24d", width=2),
            fillcolor="rgba(200,242,77,0.1)", name="Acumulado"))
        fig.add_trace(go.Bar(x=goles_dia["fecha_str"], y=goles_dia["total_goles"],
            marker_color="#4d9df2", opacity=0.6, name="Por día", yaxis="y2"))
        fig.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
            legend=dict(bgcolor="#0e0e0e"), height=320, margin=dict(t=20),
            yaxis=dict(title="Acumulado"), yaxis2=dict(title="Por día", overlaying="y", side="right"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Distribución de resultados**")
        if "ganador" in finished.columns:
            conteo = finished["ganador"].value_counts()
            labels_map = {"HOME_TEAM":"Local","AWAY_TEAM":"Visitante","DRAW":"Empate"}
            fig2 = go.Figure(go.Pie(
                labels=[labels_map.get(l,l) for l in conteo.index],
                values=conteo.values, hole=0.55,
                marker_colors=["#c8f24d","#4d9df2","#f2784d"], textinfo="label+percent"))
            fig2.update_layout(paper_bgcolor="#0e0e0e", font_color="#f0f0f0", height=320,
                legend=dict(bgcolor="#0e0e0e"), margin=dict(t=20))
            st.plotly_chart(fig2, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Goles por grupo**")
        if "grupo_clean" in finished.columns:
            goles_grupo = finished.groupby("grupo_clean")["total_goles"].agg(["sum","mean","count"]).reset_index()
            goles_grupo.columns = ["grupo","total","promedio","partidos"]
            fig3 = px.bar(goles_grupo.sort_values("total", ascending=False),
                x="grupo", y="total", color="promedio",
                color_continuous_scale=["#2a2a2a","#c8f24d"], text="total",
                labels={"grupo":"Grupo","total":"Goles","promedio":"Prom/partido"},
                hover_data=["partidos","promedio"])
            fig3.update_traces(textposition="outside")
            fig3.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
                coloraxis_showscale=False, height=320, margin=dict(t=20))
            st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.markdown("**Partidos más goleadores**")
        top_partidos = finished.nlargest(8, "total_goles").copy()
        top_partidos["partido"] = top_partidos.apply(lambda r: f"{flag(r['home'])} {r['home']} vs {flag(r['away'])} {r['away']}", axis=1)
        fig4 = px.bar(top_partidos.sort_values("total_goles"),
            x="total_goles", y="partido", orientation="h",
            color="total_goles", color_continuous_scale=["#2a2a2a","#c8f24d"],
            text="total_goles", labels={"total_goles":"Goles","partido":""})
        fig4.update_traces(textposition="outside")
        fig4.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
            coloraxis_showscale=False, height=320, margin=dict(t=20))
        st.plotly_chart(fig4, use_container_width=True)

    # Timeline
    st.markdown("**Timeline de goles por partido**")
    tl = finished.sort_values("fecha").copy()
    tl["partido"] = tl.apply(lambda r: f"{flag(r['home'])} {r['home']} vs {flag(r['away'])} {r['away']}", axis=1)
    tl["fecha_str"] = tl["fecha"].dt.strftime("%d/%m")
    fig_tl = go.Figure()
    fig_tl.add_trace(go.Scatter(x=tl["fecha_str"], y=tl["goles_home"], name="Goles local",
        mode="lines+markers", line=dict(color="#c8f24d", width=2), marker=dict(size=8), hovertext=tl["partido"]))
    fig_tl.add_trace(go.Scatter(x=tl["fecha_str"], y=tl["goles_away"], name="Goles visitante",
        mode="lines+markers", line=dict(color="#4d9df2", width=2), marker=dict(size=8), hovertext=tl["partido"]))
    fig_tl.add_trace(go.Scatter(x=tl["fecha_str"], y=tl["total_goles"], name="Total",
        mode="lines+markers", line=dict(color="#f2784d", width=2, dash="dot"), marker=dict(size=6), hovertext=tl["partido"]))
    fig_tl.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
        legend=dict(bgcolor="#0e0e0e"), height=300, margin=dict(t=20), hovermode="x unified")
    st.plotly_chart(fig_tl, use_container_width=True)

# ── TABLA DE POSICIONES ───────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📋 Tabla de posiciones</div>", unsafe_allow_html=True)

def get_row_colors(df_g):
    colors = []
    for i in range(len(df_g)):
        if i == 0:   colors.append("#1a3a1a")
        elif i == 1: colors.append("#162a16")
        else:        colors.append("#161616" if i%2==0 else "#1a1a1a")
    return colors

grupos_list = sorted(standings["grupo_clean"].dropna().unique().tolist())
n_cols = 4
for row_grupos in [grupos_list[i:i+n_cols] for i in range(0, len(grupos_list), n_cols)]:
    cols = st.columns(n_cols)
    for j, grupo in enumerate(row_grupos):
        df_g = standings[standings["grupo_clean"] == grupo].sort_values("posicion")
        with cols[j]:
            st.markdown(f"**{grupo}**")
            equipos_con_flag = [f"{flag(e)} {e}" for e in df_g["equipo"]]
            fig = go.Figure(data=[go.Table(
                header=dict(values=["","Equipo","PJ","G","E","P","PTS"],
                    fill_color="#1a1a1a", font=dict(color="#c8f24d",size=11,family="Space Grotesk"),
                    align=["center","left","center","center","center","center","center"], height=28),
                cells=dict(values=[df_g["posicion"], equipos_con_flag, df_g["pj"],
                    df_g["ganados"], df_g["empatados"], df_g["perdidos"], df_g["puntos"]],
                    fill_color=[get_row_colors(df_g)],
                    font=dict(color="#f0f0f0",size=11),
                    align=["center","left","center","center","center","center","center"], height=26)
            )])
            fig.update_layout(paper_bgcolor="#0e0e0e", margin=dict(l=0,r=0,t=0,b=0),
                height=28 + len(df_g)*26 + 16)
            st.plotly_chart(fig, use_container_width=True)

# ── GOLEADORES ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🥅 Goleadores</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Top goleadores**")
    top_n = st.slider("Top N", 5, max(5, len(scorers)), min(10, len(scorers)), key="top_n")
    df_top = scorers.sort_values("goles", ascending=False).head(top_n).copy()
    medals = ["🥇","🥈","🥉"] + ["" for _ in range(len(df_top)-3)]
    df_top["jugador_label"] = [f"{medals[i]} {row}" for i, row in enumerate(df_top["jugador"])]
    fig = px.bar(df_top, x="goles", y="jugador_label", orientation="h", color="goles",
        color_continuous_scale=["#2a2a2a","#c8f24d"], text="goles",
        hover_data=["equipo","asistencias"], labels={"goles":"Goles","jugador_label":""})
    fig.update_traces(textposition="outside")
    fig.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
        coloraxis_showscale=False, yaxis=dict(autorange="reversed"),
        height=max(300, top_n*42), margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("**Goles de jugada vs penal**")
    df_top2 = scorers.sort_values("goles", ascending=False).head(10)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Jugada", x=df_top2["jugador"], y=df_top2["goles_jugada"], marker_color="#c8f24d"))
    fig2.add_trace(go.Bar(name="Penal",  x=df_top2["jugador"], y=df_top2["penales"],      marker_color="#f2784d"))
    fig2.update_layout(barmode="stack", paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e",
        font_color="#f0f0f0", legend=dict(bgcolor="#0e0e0e"), xaxis_tickangle=-35,
        height=300, margin=dict(t=20))
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Participaciones en gol (G + A)**")
    df_part = scorers.copy()
    df_part["participaciones"] = df_part["goles"] + df_part["asistencias"]
    df_part = df_part[df_part["participaciones"] > 0].sort_values("participaciones", ascending=False).head(10)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Goles",      x=df_part["jugador"], y=df_part["goles"],      marker_color="#c8f24d"))
    fig3.add_trace(go.Bar(name="Asistencias",x=df_part["jugador"], y=df_part["asistencias"],marker_color="#4d9df2"))
    fig3.update_layout(barmode="stack", paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e",
        font_color="#f0f0f0", legend=dict(bgcolor="#0e0e0e"), xaxis_tickangle=-35,
        height=300, margin=dict(t=20))
    st.plotly_chart(fig3, use_container_width=True)

# ── RENDIMIENTO EQUIPOS ───────────────────────────────────────────────────────
if not kpis.empty:
    st.markdown("<div class='section-title'>📊 Rendimiento por equipo</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Puntos acumulados**")
        fig = px.bar(kpis.sort_values("puntos"), x="puntos", y="equipo", orientation="h",
            color="puntos", color_continuous_scale=["#2a2a2a","#c8f24d"],
            text="puntos", labels={"puntos":"Puntos","equipo":""})
        fig.update_traces(textposition="outside")
        fig.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
            coloraxis_showscale=False, height=max(320, len(kpis)*38), margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Posicionamiento ofensivo vs defensivo**")
        fig2 = px.scatter(kpis, x="gf", y="gc", text="equipo", size="pj",
            color="puntos", color_continuous_scale=["#f2784d","#c8f24d"],
            labels={"gf":"Goles a favor","gc":"Goles en contra","puntos":"Puntos"})
        fig2.update_traces(textposition="top center", textfont_size=9)
        fig2.add_hline(y=kpis["gc"].mean(), line_dash="dot", line_color="#444")
        fig2.add_vline(x=kpis["gf"].mean(), line_dash="dot", line_color="#444")
        fig2.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
            height=max(320, len(kpis)*38), margin=dict(t=20))
        st.plotly_chart(fig2, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Goles a favor vs en contra**")
        kpis_s = kpis.sort_values("gf", ascending=False)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="GF", x=kpis_s["equipo"], y=kpis_s["gf"], marker_color="#c8f24d"))
        fig3.add_trace(go.Bar(name="GC", x=kpis_s["equipo"], y=kpis_s["gc"], marker_color="#f2784d"))
        fig3.update_layout(barmode="group", paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e",
            font_color="#f0f0f0", legend=dict(bgcolor="#0e0e0e"), xaxis_tickangle=-45,
            height=420, margin=dict(t=20, b=140))
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.markdown("**Diferencia de goles**")
        kpis_dg = kpis.sort_values("dg", ascending=True)
        colors_dg = ["#c8f24d" if v >= 0 else "#f2784d" for v in kpis_dg["dg"]]
        fig4 = go.Figure(go.Bar(x=kpis_dg["dg"], y=kpis_dg["equipo"],
            orientation="h", marker_color=colors_dg, text=kpis_dg["dg"]))
        fig4.add_vline(x=0, line_color="#444")
        fig4.update_traces(textposition="outside")
        fig4.update_layout(paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e", font_color="#f0f0f0",
            height=420, margin=dict(t=20, r=60))
        st.plotly_chart(fig4, use_container_width=True)

# ── GRÁFICOS AVANZADOS ────────────────────────────────────────────────────────
if not finished.empty and not kpis.empty:
    st.markdown("<div class='section-title'>🔬 Análisis avanzado</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Treemap — goles por equipo**")
        kpis_gf = kpis[kpis["gf"] > 0].copy()
        if not kpis_gf.empty:
            fig_tree = px.treemap(kpis_gf, path=["equipo"], values="gf",
                color="gf", color_continuous_scale=["#1a1a1a","#c8f24d"],
                labels={"gf":"Goles a favor"})
            fig_tree.update_traces(textinfo="label+value", textfont_size=13)
            fig_tree.update_layout(paper_bgcolor="#0e0e0e", font_color="#f0f0f0",
                coloraxis_showscale=False, height=380, margin=dict(t=20))
            st.plotly_chart(fig_tree, use_container_width=True)

    with col2:
        st.markdown("**Radar — top 5 equipos**")
        if len(kpis) >= 3:
            top5 = kpis.nlargest(5, "puntos")
            categories = ["Puntos","GF","Prom GF x3","DG positivo"]
            fig_radar = go.Figure()
            for _, row in top5.iterrows():
                fig_radar.add_trace(go.Scatterpolar(
                    r=[row["puntos"], row["gf"], row["promedio_gf"]*3, max(row["dg"],0)],
                    theta=categories, fill="toself", name=row["equipo"], opacity=0.7))
            fig_radar.update_layout(
                polar=dict(bgcolor="#1a1a1a",
                    radialaxis=dict(visible=True, color="#444"),
                    angularaxis=dict(color="#888")),
                paper_bgcolor="#0e0e0e", font_color="#f0f0f0",
                legend=dict(bgcolor="#0e0e0e", font_size=11),
                height=380, margin=dict(t=20))
            st.plotly_chart(fig_radar, use_container_width=True)

# ── ARGENTINA ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🇦🇷 Argentina</div>", unsafe_allow_html=True)

arg = finished[(finished["home"]=="Argentina")|(finished["away"]=="Argentina")].copy()
arg_up = upcoming[(upcoming["home"]=="Argentina")|(upcoming["away"]=="Argentina")].copy()

if arg.empty and arg_up.empty:
    st.info("Argentina todavía no tiene partidos registrados.")
else:
    if not arg_up.empty:
        prox = arg_up.sort_values("fecha").iloc[0]
        fecha_str = prox["fecha"].strftime("%d/%m %H:%M UTC") if pd.notna(prox["fecha"]) else "—"
        rival = prox["away"] if prox["home"]=="Argentina" else prox["home"]
        st.markdown(f"""<div class='next-card' style='border-color:#c8f24d33;margin-bottom:24px'>
            <div class='next-time'>⏳ Próximo partido — {fecha_str}</div>
            <div class='next-match' style='font-size:1.2rem'>🇦🇷 Argentina vs {flag(rival)} {rival}</div>
        </div>""", unsafe_allow_html=True)

    if not arg.empty:
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

        c1,c2,c3,c4,c5 = st.columns(5)
        for col,val,lbl in zip([c1,c2,c3,c4,c5],
            [len(arg), int(arg_gf), int(arg_gc), int(arg_gf-arg_gc), arg_pts],
            ["Partidos","Goles a favor","Goles en contra","Diferencia","Puntos"]):
            with col:
                color = "#f2784d" if lbl=="Diferencia" and val<0 else "#c8f24d"
                st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:{color}'>{val}</div><div class='metric-label'>{lbl}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Partidos**")
            for _, row in arg.sort_values("fecha").iterrows():
                es_local = row["home"] == "Argentina"
                rival = row["away"] if es_local else row["home"]
                ga = int(row["goles_home"]) if es_local else int(row["goles_away"])
                gr = int(row["goles_away"]) if es_local else int(row["goles_home"])
                res = "✅" if ga > gr else ("🤝" if ga == gr else "❌")
                fecha_str = row["fecha"].strftime("%d/%m") if pd.notna(row["fecha"]) else "—"
                st.markdown(f"""<div class='resultado-card'>
                    <div style='font-size:1.2rem'>{res}</div>
                    <div style='flex:1;margin:0 12px'>
                        <div style='font-weight:600'>🇦🇷 Argentina vs {flag(rival)} {rival}</div>
                        <div style='font-size:0.75rem;color:#666'>{'Local' if es_local else 'Visitante'} · {fecha_str}</div>
                    </div>
                    <div style='font-family:Space Grotesk;font-size:1.4rem;font-weight:700;color:#c8f24d'>{ga} — {gr}</div>
                </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown("**Argentina vs rivales**")
            rival_data = []
            for _, row in arg.iterrows():
                es_local = row["home"] == "Argentina"
                rival = row["away"] if es_local else row["home"]
                ga = int(row["goles_home"]) if es_local else int(row["goles_away"])
                gr = int(row["goles_away"]) if es_local else int(row["goles_home"])
                rival_data.append({"rival": f"{flag(rival)} {rival}", "Argentina": ga, "Rival": gr})
            df_riv = pd.DataFrame(rival_data)
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Argentina", x=df_riv["rival"], y=df_riv["Argentina"], marker_color="#c8f24d"))
            fig.add_trace(go.Bar(name="Rival",     x=df_riv["rival"], y=df_riv["Rival"],     marker_color="#f2784d"))
            fig.update_layout(barmode="group", paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e",
                font_color="#f0f0f0", legend=dict(bgcolor="#0e0e0e"), height=300, margin=dict(t=20))
            st.plotly_chart(fig, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center;color:#444;font-size:0.8rem;padding:20px 0'>
    Construido por <strong style='color:#666'>Diego Bouzada</strong> · 
    Python + GitHub Actions · football-data.org · 
    <a href='https://github.com/dbouzada/mundial-2026-data' style='color:#c8f24d;text-decoration:none'>GitHub ↗</a> · 
    <a href='https://linkedin.com/in/bouzadadiego' style='color:#c8f24d;text-decoration:none'>LinkedIn ↗</a>
</div>
""", unsafe_allow_html=True)
