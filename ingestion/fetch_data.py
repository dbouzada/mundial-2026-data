"""
Mundial 2026 — Script de ingesta y transformación
Fuentes:
  - football-data.org → partidos, standings, goleadores, equipos
Autor: Diego Bouzada
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent
RAW_DIR       = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

FD_API_KEY     = os.getenv("FD_API_KEY", "")
FD_BASE        = "https://api.football-data.org/v4"
FD_HEADERS     = {"X-Auth-Token": FD_API_KEY}
WC_COMPETITION = "WC"


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def safe_get(url: str, headers: dict = {}, params: dict = None) -> dict | None:
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ⚠️  Error en {url}: {e}")
        return None


def save_raw(data, filename: str):
    path = RAW_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Raw guardado: {filename}")


# ─── FOOTBALL-DATA.ORG ────────────────────────────────────────────────────────
def fetch_matches() -> pd.DataFrame:
    """Todos los partidos del torneo."""
    print("📥 Fetching matches...")
    data = safe_get(f"{FD_BASE}/competitions/{WC_COMPETITION}/matches", FD_HEADERS)
    if not data:
        return pd.DataFrame()
    save_raw(data, "matches.json")

    rows = []
    for m in data.get("matches", []):
        home  = m.get("homeTeam", {})
        away  = m.get("awayTeam", {})
        score = m.get("score", {})
        ft    = score.get("fullTime", {})
        rows.append({
            "match_id":   m.get("id"),
            "fecha":      m.get("utcDate", "")[:10],
            "estado":     m.get("status"),
            "etapa":      m.get("stage"),
            "grupo":      m.get("group"),
            "estadio":    m.get("venue"),
            "home":       home.get("name"),
            "home_id":    home.get("id"),
            "away":       away.get("name"),
            "away_id":    away.get("id"),
            "goles_home": ft.get("home"),
            "goles_away": ft.get("away"),
            "ganador":    score.get("winner"),
        })

    df = pd.DataFrame(rows)
    terminados = df[df["estado"] == "FINISHED"]
    df.to_csv(PROCESSED_DIR / "matches.csv", index=False)
    print(f"  ✅ Matches: {len(df)} partidos ({len(terminados)} terminados)")
    return df


def fetch_standings() -> pd.DataFrame:
    """Tabla de posiciones por grupo."""
    print("📥 Fetching standings...")
    data = safe_get(f"{FD_BASE}/competitions/{WC_COMPETITION}/standings", FD_HEADERS)
    if not data:
        return pd.DataFrame()
    save_raw(data, "standings.json")

    rows = []
    for group in data.get("standings", []):
        group_name = group.get("group", "")
        for entry in group.get("table", []):
            team = entry.get("team", {})
            rows.append({
                "grupo":     group_name,
                "posicion":  entry.get("position"),
                "equipo":    team.get("name"),
                "equipo_id": team.get("id"),
                "pj":        entry.get("playedGames"),
                "ganados":   entry.get("won"),
                "empatados": entry.get("draw"),
                "perdidos":  entry.get("lost"),
                "gf":        entry.get("goalsFor"),
                "gc":        entry.get("goalsAgainst"),
                "dg":        entry.get("goalDifference"),
                "puntos":    entry.get("points"),
            })

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "standings.csv", index=False)
    print(f"  ✅ Standings: {len(df)} equipos")
    return df


def fetch_scorers() -> pd.DataFrame:
    """Tabla de goleadores."""
    print("📥 Fetching scorers...")
    data = safe_get(f"{FD_BASE}/competitions/{WC_COMPETITION}/scorers?limit=50", FD_HEADERS)
    if not data:
        return pd.DataFrame()
    save_raw(data, "scorers.json")

    rows = []
    for s in data.get("scorers", []):
        player = s.get("player", {})
        team   = s.get("team", {})
        rows.append({
            "jugador":     player.get("name"),
            "jugador_id":  player.get("id"),
            "equipo":      team.get("name"),
            "goles":       s.get("goals"),
            "asistencias": s.get("assists"),
            "penales":     s.get("penalties"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "scorers.csv", index=False)
    print(f"  ✅ Scorers: {len(df)} jugadores")
    return df


def fetch_teams() -> pd.DataFrame:
    """Equipos del torneo."""
    print("📥 Fetching teams...")
    data = safe_get(f"{FD_BASE}/competitions/{WC_COMPETITION}/teams", FD_HEADERS)
    if not data:
        return pd.DataFrame()
    save_raw(data, "teams.json")

    rows = []
    for t in data.get("teams", []):
        rows.append({
            "equipo_id":  t.get("id"),
            "equipo":     t.get("name"),
            "codigo":     t.get("tla"),
            "pais":       t.get("area", {}).get("name"),
            "escudo_url": t.get("crest"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "teams.csv", index=False)
    print(f"  ✅ Teams: {len(df)} equipos")
    return df


# ─── KPIs POR EQUIPO ──────────────────────────────────────────────────────────
def calculate_team_kpis(matches_df: pd.DataFrame) -> pd.DataFrame:
    """KPIs acumulados por equipo desde partidos terminados."""
    print("⚙️  Calculando KPIs por equipo...")

    if matches_df.empty or "estado" not in matches_df.columns:
        print("  ⚠️  Sin datos suficientes")
        return pd.DataFrame()

    finished = matches_df[matches_df["estado"] == "FINISHED"].copy()
    finished["goles_home"] = pd.to_numeric(finished["goles_home"], errors="coerce").fillna(0)
    finished["goles_away"] = pd.to_numeric(finished["goles_away"], errors="coerce").fillna(0)

    if finished.empty:
        print("  ⚠️  Sin partidos terminados todavía")
        return pd.DataFrame()

    equipos = pd.concat([finished["home"], finished["away"]]).unique()
    rows = []

    for equipo in equipos:
        como_home = finished[finished["home"] == equipo]
        como_away = finished[finished["away"] == equipo]

        pj = len(como_home) + len(como_away)
        gf = como_home["goles_home"].sum() + como_away["goles_away"].sum()
        gc = como_home["goles_away"].sum() + como_away["goles_home"].sum()

        # Puntos
        pts = 0
        for _, row in como_home.iterrows():
            if row["goles_home"] > row["goles_away"]:    pts += 3
            elif row["goles_home"] == row["goles_away"]: pts += 1
        for _, row in como_away.iterrows():
            if row["goles_away"] > row["goles_home"]:    pts += 3
            elif row["goles_away"] == row["goles_home"]: pts += 1

        rows.append({
            "equipo":        equipo,
            "pj":            pj,
            "gf":            int(gf),
            "gc":            int(gc),
            "dg":            int(gf - gc),
            "puntos":        pts,
            "promedio_gf":   round(gf / pj, 2) if pj > 0 else 0,
            "promedio_gc":   round(gc / pj, 2) if pj > 0 else 0,
        })

    df = pd.DataFrame(rows).sort_values("puntos", ascending=False)
    df.to_csv(PROCESSED_DIR / "kpis_equipos.csv", index=False)
    print(f"  ✅ KPIs calculados: {len(df)} equipos")
    return df


# ─── METADATA ─────────────────────────────────────────────────────────────────
def save_metadata(matches_df: pd.DataFrame):
    terminados = 0
    if not matches_df.empty and "estado" in matches_df.columns:
        terminados = int((matches_df["estado"] == "FINISHED").sum())
    meta = {
        "ultima_actualizacion": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "partidos_totales":     len(matches_df),
        "partidos_terminados":  terminados,
        "fuentes":              ["football-data.org"],
    }
    with open(PROCESSED_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  ✅ Metadata guardada ({terminados} partidos terminados)")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("\n🏆 Mundial 2026 — Ingesta iniciada")
    print(f"   {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

    matches   = fetch_matches()
    standings = fetch_standings()
    scorers   = fetch_scorers()
    teams     = fetch_teams()
    kpis      = calculate_team_kpis(matches)

    save_metadata(matches)

    print("\n✅ Ingesta completada")
    print(f"   Matches:    {len(matches)} partidos")
    print(f"   Standings:  {len(standings)} equipos")
    print(f"   Scorers:    {len(scorers)} jugadores")
    print(f"   Teams:      {len(teams)} equipos")
    print(f"   KPIs:       {len(kpis)} equipos")


if __name__ == "__main__":
    main()
