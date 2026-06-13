"""
Mundial 2026 — Script de ingesta y transformación
Fuentes:
  - worldcup26.ir     → partidos, goles, resultados (sin auth)
  - football-data.org → standings y goleadores
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

FD_API_KEY  = os.getenv("FD_API_KEY", "")
FD_BASE     = "https://api.football-data.org/v4"
FD_HEADERS  = {"X-Auth-Token": FD_API_KEY}
WC26_BASE   = "https://worldcup26.ir/get"
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


# ─── WORLDCUP26.IR ────────────────────────────────────────────────────────────
def fetch_games() -> pd.DataFrame:
    """Partidos del Mundial desde worldcup26.ir"""
    print("📥 Fetching games (worldcup26.ir)...")
    data = safe_get(f"{WC26_BASE}/games")
    if not data:
        return pd.DataFrame()
    save_raw(data, "games_wc26.json")

    games = data.get("games", [])
    df = pd.DataFrame(games)

    # Limpieza y tipado
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
    df["finished"]   = df["finished"].str.upper() == "TRUE"
    df["total_goles"] = df["home_score"] + df["away_score"]

    # Columnas útiles
    df = df[[
        "id", "local_date", "group", "matchday", "type",
        "home_team_name_en", "away_team_name_en",
        "home_score", "away_score", "total_goles",
        "finished", "home_scorers", "away_scorers",
        "stadium_id"
    ]]

    df.to_csv(PROCESSED_DIR / "games.csv", index=False)
    print(f"  ✅ Games procesados: {len(df)} partidos ({df['finished'].sum()} terminados)")
    return df


def fetch_teams() -> pd.DataFrame:
    """Equipos del Mundial desde worldcup26.ir"""
    print("📥 Fetching teams (worldcup26.ir)...")
    data = safe_get(f"{WC26_BASE}/teams")
    if not data:
        return pd.DataFrame()
    save_raw(data, "teams_wc26.json")

    teams = data.get("teams", [])
    df = pd.DataFrame(teams)[[
        "id", "name_en", "group", "fifa_code", "continent"
    ]]

    df.to_csv(PROCESSED_DIR / "teams.csv", index=False)
    print(f"  ✅ Teams procesados: {len(df)} equipos")
    return df


def fetch_stadiums() -> pd.DataFrame:
    """Estadios del Mundial desde worldcup26.ir"""
    print("📥 Fetching stadiums (worldcup26.ir)...")
    data = safe_get(f"{WC26_BASE}/stadiums")
    if not data:
        return pd.DataFrame()
    save_raw(data, "stadiums_wc26.json")

    stadiums = data.get("stadiums", [])
    df = pd.DataFrame(stadiums)

    df.to_csv(PROCESSED_DIR / "stadiums.csv", index=False)
    print(f"  ✅ Stadiums procesados: {len(df)} estadios")
    return df


# ─── FOOTBALL-DATA.ORG ────────────────────────────────────────────────────────
def fetch_standings() -> pd.DataFrame:
    """Tabla de posiciones desde football-data.org"""
    print("📥 Fetching standings (football-data.org)...")
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
                "grupo":    group_name,
                "posicion": entry.get("position"),
                "equipo":   team.get("name"),
                "pj":       entry.get("playedGames"),
                "ganados":  entry.get("won"),
                "empatados":entry.get("draw"),
                "perdidos": entry.get("lost"),
                "gf":       entry.get("goalsFor"),
                "gc":       entry.get("goalsAgainst"),
                "dg":       entry.get("goalDifference"),
                "puntos":   entry.get("points"),
            })

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "standings.csv", index=False)
    print(f"  ✅ Standings procesados: {len(df)} equipos")
    return df


def fetch_scorers() -> pd.DataFrame:
    """Goleadores desde football-data.org"""
    print("📥 Fetching scorers (football-data.org)...")
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
            "equipo":      team.get("name"),
            "goles":       s.get("goals"),
            "asistencias": s.get("assists"),
            "penales":     s.get("penalties"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "scorers.csv", index=False)
    print(f"  ✅ Scorers procesados: {len(df)} jugadores")
    return df


# ─── KPIs POR EQUIPO ──────────────────────────────────────────────────────────
def calculate_team_kpis(games_df: pd.DataFrame) -> pd.DataFrame:
    """KPIs acumulados por equipo desde los partidos terminados."""
    print("⚙️  Calculando KPIs por equipo...")

    finished = games_df[games_df["finished"] == True].copy()
    if finished.empty:
        print("  ⚠️  Sin partidos terminados todavía")
        return pd.DataFrame()

    equipos = pd.concat([
        finished["home_team_name_en"],
        finished["away_team_name_en"]
    ]).unique()

    rows = []
    for equipo in equipos:
        como_home = finished[finished["home_team_name_en"] == equipo]
        como_away = finished[finished["away_team_name_en"] == equipo]

        pj    = len(como_home) + len(como_away)
        gf    = como_home["home_score"].sum() + como_away["away_score"].sum()
        gc    = como_home["away_score"].sum() + como_away["home_score"].sum()

        # Puntos
        pts = 0
        for _, row in como_home.iterrows():
            if row["home_score"] > row["away_score"]:   pts += 3
            elif row["home_score"] == row["away_score"]: pts += 1
        for _, row in como_away.iterrows():
            if row["away_score"] > row["home_score"]:   pts += 3
            elif row["away_score"] == row["home_score"]: pts += 1

        rows.append({
            "equipo": equipo,
            "pj":     pj,
            "gf":     int(gf),
            "gc":     int(gc),
            "dg":     int(gf - gc),
            "puntos": pts,
            "promedio_gf": round(gf / pj, 2) if pj > 0 else 0,
            "promedio_gc": round(gc / pj, 2) if pj > 0 else 0,
        })

    df = pd.DataFrame(rows).sort_values("puntos", ascending=False)
    df.to_csv(PROCESSED_DIR / "kpis_equipos.csv", index=False)
    print(f"  ✅ KPIs calculados: {len(df)} equipos")
    return df


# ─── METADATA ─────────────────────────────────────────────────────────────────
def save_metadata(games_df: pd.DataFrame):
    terminados = int(games_df["finished"].sum()) if not games_df.empty else 0
    meta = {
        "ultima_actualizacion": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "partidos_totales": len(games_df),
        "partidos_terminados": terminados,
        "fuentes": ["worldcup26.ir", "football-data.org"],
    }
    with open(PROCESSED_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  ✅ Metadata guardada ({terminados} partidos terminados)")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("\n🏆 Mundial 2026 — Ingesta iniciada")
    print(f"   {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

    games     = fetch_games()
    teams     = fetch_teams()
    stadiums  = fetch_stadiums()
    standings = fetch_standings()
    scorers   = fetch_scorers()
    kpis      = calculate_team_kpis(games)

    save_metadata(games)

    print("\n✅ Ingesta completada")
    print(f"   Games:      {len(games)} partidos")
    print(f"   Teams:      {len(teams)} equipos")
    print(f"   Stadiums:   {len(stadiums)} estadios")
    print(f"   Standings:  {len(standings)} filas")
    print(f"   Scorers:    {len(scorers)} jugadores")
    print(f"   KPIs:       {len(kpis)} equipos")


if __name__ == "__main__":
    main()
