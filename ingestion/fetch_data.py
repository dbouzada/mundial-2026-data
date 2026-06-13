"""
Mundial 2026 — Script de ingesta y transformación
Fuentes: football-data.org + API-Football
Autor: Diego Bouzada
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

FD_API_KEY = os.getenv("FD_API_KEY", "")          # football-data.org
AF_API_KEY = os.getenv("AF_API_KEY", "")          # api-football (RapidAPI)

FD_BASE = "https://api.football-data.org/v4"
AF_BASE = "https://v3.football.api-sports.io"

FD_HEADERS = {"X-Auth-Token": FD_API_KEY}
AF_HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": AF_API_KEY,
}

WC_COMPETITION = "WC"   # football-data.org
WC_LEAGUE_AF   = 1      # api-football  (World Cup)
WC_SEASON_AF   = 2026


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def safe_get(url: str, headers: dict, params: dict = None) -> dict | None:
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ⚠️  Error en {url}: {e}")
        return None


def save_raw(data: dict, filename: str):
    path = RAW_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Raw guardado: {filename}")


# ─── FOOTBALL-DATA.ORG ────────────────────────────────────────────────────────
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
                "grupo":        group_name,
                "posicion":     entry.get("position"),
                "equipo":       team.get("name"),
                "equipo_id":    team.get("id"),
                "pj":           entry.get("playedGames"),
                "ganados":      entry.get("won"),
                "empatados":    entry.get("draw"),
                "perdidos":     entry.get("lost"),
                "gf":           entry.get("goalsFor"),
                "gc":           entry.get("goalsAgainst"),
                "dg":           entry.get("goalDifference"),
                "puntos":       entry.get("points"),
            })

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "standings.csv", index=False)
    print(f"  ✅ Standings procesados: {len(df)} equipos")
    return df


def fetch_matches() -> pd.DataFrame:
    """Todos los partidos del torneo."""
    print("📥 Fetching matches...")
    data = safe_get(f"{FD_BASE}/competitions/{WC_COMPETITION}/matches", FD_HEADERS)
    if not data:
        return pd.DataFrame()
    save_raw(data, "matches.json")

    rows = []
    for m in data.get("matches", []):
        home = m.get("homeTeam", {})
        away = m.get("awayTeam", {})
        score = m.get("score", {})
        ft = score.get("fullTime", {})
        rows.append({
            "match_id":         m.get("id"),
            "fecha":            m.get("utcDate", "")[:10],
            "estado":           m.get("status"),
            "etapa":            m.get("stage"),
            "grupo":            m.get("group"),
            "estadio":          m.get("venue"),
            "home":             home.get("name"),
            "home_id":          home.get("id"),
            "away":             away.get("name"),
            "away_id":          away.get("id"),
            "goles_home":       ft.get("home"),
            "goles_away":       ft.get("away"),
            "ganador":          score.get("winner"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "matches.csv", index=False)
    print(f"  ✅ Matches procesados: {len(df)} partidos")
    return df


def fetch_scorers() -> pd.DataFrame:
    """Tabla de goleadores."""
    print("📥 Fetching top scorers...")
    data = safe_get(f"{FD_BASE}/competitions/{WC_COMPETITION}/scorers?limit=50", FD_HEADERS)
    if not data:
        return pd.DataFrame()
    save_raw(data, "scorers.json")

    rows = []
    for s in data.get("scorers", []):
        player = s.get("player", {})
        team   = s.get("team", {})
        rows.append({
            "jugador":      player.get("name"),
            "jugador_id":   player.get("id"),
            "equipo":       team.get("name"),
            "goles":        s.get("goals"),
            "asistencias":  s.get("assists"),
            "penales":      s.get("penalties"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED_DIR / "scorers.csv", index=False)
    print(f"  ✅ Scorers procesados: {len(df)} jugadores")
    return df


# ─── API-FOOTBALL (xG y stats avanzadas) ──────────────────────────────────────
def fetch_xg_stats(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Obtiene xG y stats avanzadas por partido desde api-football.
    Solo procesa partidos ya terminados (FINISHED).
    """
    if AF_API_KEY == "":
        print("  ⚠️  AF_API_KEY no configurada, saltando xG")
        return pd.DataFrame()

    print("📥 Fetching xG stats...")
    finished = matches_df[matches_df["estado"] == "FINISHED"] if not matches_df.empty else pd.DataFrame()

    if finished.empty:
        print("  ℹ️  Sin partidos terminados todavía")
        return pd.DataFrame()

    # Obtenemos todos los fixtures de api-football para el torneo
    data = safe_get(
        f"{AF_BASE}/fixtures",
        AF_HEADERS,
        params={"league": WC_LEAGUE_AF, "season": WC_SEASON_AF}
    )
    if not data:
        return pd.DataFrame()
    save_raw(data, "fixtures_af.json")

    rows = []
    for fixture in data.get("response", []):
        fix     = fixture.get("fixture", {})
        teams   = fixture.get("teams", {})
        goals   = fixture.get("goals", {})
        stats_f = fixture.get("statistics", [])

        # xG viene en fixture.score.xg en algunos endpoints — lo buscamos
        score = fixture.get("score", {})

        row = {
            "fixture_id":   fix.get("id"),
            "fecha":        fix.get("date", "")[:10],
            "estado":       fix.get("status", {}).get("short"),
            "home":         teams.get("home", {}).get("name"),
            "away":         teams.get("away", {}).get("name"),
            "goles_home":   goals.get("home"),
            "goles_away":   goals.get("away"),
            # xG si está disponible en este endpoint
            "xg_home":      None,
            "xg_away":      None,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Enriquecemos con xG por fixture (requiere llamada individual)
    # Para no agotar los 100 requests/día, solo lo hacemos para partidos recientes
    xg_rows = []
    finished_ids = df[df.get("estado", pd.Series(dtype=str)) == "FT"]["fixture_id"].tolist()[:10] if "estado" in df.columns else []  # últimos 10

    for fid in finished_ids:
        stats = safe_get(
            f"{AF_BASE}/fixtures/statistics",
            AF_HEADERS,
            params={"fixture": fid}
        )
        if not stats:
            continue
        response = stats.get("response", [])
        xg_home = xg_away = None
        for team_stats in response:
            team_name = team_stats.get("team", {}).get("name")
            for stat in team_stats.get("statistics", []):
                if stat.get("type") == "expected_goals":
                    val = stat.get("value")
                    if xg_home is None:
                        xg_home = val
                    else:
                        xg_away = val
        xg_rows.append({"fixture_id": fid, "xg_home": xg_home, "xg_away": xg_away})

    if xg_rows:
        xg_df = pd.DataFrame(xg_rows)
        df = df.merge(xg_df, on="fixture_id", how="left", suffixes=("", "_real"))
        df["xg_home"] = df["xg_home_real"].combine_first(df["xg_home"])
        df["xg_away"] = df["xg_away_real"].combine_first(df["xg_away"])
        df.drop(columns=["xg_home_real", "xg_away_real"], inplace=True, errors="ignore")

    df.to_csv(PROCESSED_DIR / "fixtures_xg.csv", index=False)
    print(f"  ✅ xG stats procesadas: {len(df)} fixtures")
    return df


# ─── KPIs CALCULADOS ──────────────────────────────────────────────────────────
def calculate_kpis(matches_df: pd.DataFrame, xg_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula KPIs avanzados por equipo:
    - xG a favor / en contra acumulado
    - Diferencia xG vs goles reales (suerte/eficiencia)
    - xPoints estimados
    """
    print("⚙️  Calculando KPIs...")

    if xg_df.empty or matches_df.empty:
        print("  ⚠️  Sin datos suficientes para KPIs")
        return pd.DataFrame()

    finished = xg_df[xg_df["estado"] == "FT"].copy()
    finished["xg_home"] = pd.to_numeric(finished["xg_home"], errors="coerce")
    finished["xg_away"] = pd.to_numeric(finished["xg_away"], errors="coerce")
    finished["goles_home"] = pd.to_numeric(finished["goles_home"], errors="coerce")
    finished["goles_away"] = pd.to_numeric(finished["goles_away"], errors="coerce")

    rows = []
    equipos = pd.concat([finished["home"], finished["away"]]).unique()

    for equipo in equipos:
        como_home = finished[finished["home"] == equipo]
        como_away = finished[finished["away"] == equipo]

        xg_favor     = como_home["xg_home"].sum() + como_away["xg_away"].sum()
        xg_contra    = como_home["xg_away"].sum() + como_away["xg_home"].sum()
        goles_favor  = como_home["goles_home"].sum() + como_away["goles_away"].sum()
        goles_contra = como_home["goles_away"].sum() + como_away["goles_home"].sum()

        rows.append({
            "equipo":           equipo,
            "xg_favor":         round(xg_favor, 2),
            "xg_contra":        round(xg_contra, 2),
            "xg_diff":          round(xg_favor - xg_contra, 2),
            "goles_favor":      int(goles_favor),
            "goles_contra":     int(goles_contra),
            "eficiencia_of":    round(goles_favor - xg_favor, 2),   # + = convierte más de lo esperado
            "eficiencia_def":   round(xg_contra - goles_contra, 2), # + = defiende mejor de lo esperado
        })

    df = pd.DataFrame(rows).sort_values("xg_diff", ascending=False)
    df.to_csv(PROCESSED_DIR / "kpis_equipos.csv", index=False)
    print(f"  ✅ KPIs calculados: {len(df)} equipos")
    return df


# ─── METADATA ─────────────────────────────────────────────────────────────────
def save_metadata():
    meta = {
        "ultima_actualizacion": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "fuentes": ["football-data.org", "api-football"],
    }
    with open(PROCESSED_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  ✅ Metadata guardada")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("\n🏆 Mundial 2026 — Ingesta iniciada")
    print(f"   {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

    standings = fetch_standings()
    matches   = fetch_matches()
    scorers   = fetch_scorers()
    xg        = fetch_xg_stats(matches)
    kpis      = calculate_kpis(matches, xg)

    save_metadata()

    print("\n✅ Ingesta completada")
    print(f"   Standings:  {len(standings)} filas")
    print(f"   Matches:    {len(matches)} filas")
    print(f"   Scorers:    {len(scorers)} filas")
    print(f"   xG Stats:   {len(xg)} filas")
    print(f"   KPIs:       {len(kpis)} filas")


if __name__ == "__main__":
    main()
