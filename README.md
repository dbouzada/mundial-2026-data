# 🏆 Mundial 2026 — Data Hub

Pipeline de datos en tiempo (casi) real del Mundial 2026, con ingesta automatizada, transformación en Python y dashboard público interactivo.

**🔗 Dashboard en vivo:** [mundial-2026-data.streamlit.app](https://mundial-2026-data.streamlit.app)

---

## 📐 Arquitectura

```
football-data.org (API)
         ↓
GitHub Actions (cron automático)
  └── ingestion/fetch_data.py
         ↓
data/processed/*.csv  (almacenamiento público en GitHub)
         ↓
Streamlit Cloud (dashboard/app.py)
  └── Lee los CSVs directo desde GitHub raw
  └── Cache de 30s + boton de refresh manual
```

El pipeline funciona sin servidor propio ni base de datos: GitHub Actions hace de orquestador y el repo de GitHub hace de almacenamiento intermedio. Streamlit Cloud lee esos CSVs públicos y los renderiza.

---

## 🗂️ Estructura del repo

```
mundial-2026-data/
│
├── .github/workflows/
│   └── pipeline.yml          # Workflow de GitHub Actions (cron + ingesta)
│
├── ingestion/
│   └── fetch_data.py         # Script de ingesta y transformación
│
├── data/
│   ├── raw/                  # JSONs crudos tal cual los devuelve la API
│   └── processed/            # CSVs limpios y listos para consumir
│       ├── matches.csv
│       ├── standings.csv
│       ├── scorers.csv
│       ├── teams.csv
│       ├── kpis_equipos.csv
│       └── meta.json
│
├── dashboard/
│   └── app.py                # Dashboard Streamlit (single-page, dark theme)
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Pipeline de ingesta (`ingestion/fetch_data.py`)

Consume la API de football-data.org (plan free) y genera:

| Archivo | Contenido |
|---|---|
| `matches.csv` | Los 104 partidos del torneo: fecha, estado, grupo, goles, ganador |
| `standings.csv` | Tabla de posiciones por grupo |
| `scorers.csv` | Goleadores con goles, asistencias y penales |
| `teams.csv` | Equipos participantes con escudo y país |
| `kpis_equipos.csv` | KPIs calculados por equipo: PJ, GF, GC, DG, puntos, promedios |
| `meta.json` | Timestamp de última actualización y conteo de partidos |

El script es idempotente: cada corrida sobreescribe los CSVs con el estado actual del torneo, no acumula histórico.

### Variables de entorno

```bash
FD_API_KEY=tu_api_key_de_football-data.org
```

Se obtiene gratis registrándose en football-data.org/client/register.

---

## 🤖 Automatización (`.github/workflows/pipeline.yml`)

GitHub Actions corre el script de ingesta y commitea los CSVs actualizados automáticamente, sin servidor propio.

**Frecuencia del cron:**
- 13:00 a 02:50 ARG (franja de partidos) → cada 10 minutos
- 04:00 a 12:00 ARG (sin partidos) → cada hora

También se puede disparar manualmente desde la pestaña Actions → Run workflow, o automáticamente al hacer push de cambios en `ingestion/`.

**Secrets necesarios** (Settings → Secrets and variables → Actions):
- `FD_API_KEY`

**Permisos requeridos** (Settings → Actions → General → Workflow permissions):
- Read and write permissions (para que el bot pueda commitear los CSVs)

---

## 📊 Dashboard (`dashboard/app.py`)

Construido en Streamlit + Plotly, diseño dark theme custom, una sola página scrolleable.

**Secciones:**
- Overview — métricas globales, gauge de goles promedio, distribución de resultados, sparkline de tendencia
- Próximos partidos — con horarios oficiales en Argentina (hardcodeados desde fixture FIFA, ya que la API no siempre devuelve la hora confirmada)
- Resultados — últimos 6 partidos + expander con historial completo filtrable por grupo
- Análisis del torneo — goles acumulados, goles por grupo, partidos más goleadores, heatmap grupo x fecha
- Tabla de posiciones — los 12 grupos con progress bars y resaltado de clasificados (top 2)
- Goleadores — ranking con barras de progreso, desglose jugada/penal, participaciones en gol
- Rendimiento por equipo — puntos, scatter ofensivo/defensivo, diferencia de goles, radar comparativo
- Análisis avanzado — treemap de goles, combo chart GF/GC/DG
- Argentina — sección dedicada con próximo partido, historial y comparativa vs rivales

**Cache:** `st.cache_data(ttl=30)` + boton manual de actualizar que limpia cache y fuerza recarga.

**Responsive:** breakpoint en 768px para mobile (tipografia, padding y badges ajustados).

---

## 🚀 Cómo correrlo localmente

```bash
# Clonar el repo
git clone https://github.com/dbouzada/mundial-2026-data.git
cd mundial-2026-data

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key
cp .env.example .env
# completar FD_API_KEY en .env

# Correr la ingesta
python ingestion/fetch_data.py

# Levantar el dashboard
streamlit run dashboard/app.py
```

---

## 🛠️ Stack técnico

- Lenguaje: Python 3.11
- Ingesta: requests, pandas
- Orquestación: GitHub Actions (cron + workflow_dispatch)
- Almacenamiento: CSVs versionados en GitHub (sin base de datos)
- Visualización: Streamlit + Plotly
- Deploy: Streamlit Community Cloud (gratis, conectado directo al repo)
- Fuente de datos: football-data.org API v4

---

## 📌 Decisiones de diseño

- Sin base de datos: para un proyecto de este tamaño, CSVs versionados en Git son suficiente y eliminan infraestructura extra.
- GitHub Actions como cron: evita tener un servidor corriendo 24/7 solo para la ingesta.
- Horarios hardcodeados para Argentina: la API de football-data.org no siempre confirma el horario exacto de partidos futuros (devuelve 00:00 UTC como placeholder), así que se mantiene un diccionario con los horarios oficiales confirmados por FIFA como fallback.
- Streamlit en vez de un framework JS: prioriza velocidad de desarrollo y mantenimiento simple sobre personalización visual extrema, dado que el objetivo es un dashboard de datos, no un producto consumer.

---

## ✍️ Autor

**Diego Bouzada** — Data Analytics Engineer

GitHub: github.com/dbouzada · LinkedIn: linkedin.com/in/bouzadadiego
