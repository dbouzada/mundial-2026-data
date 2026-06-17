# 🏆 Mundial 2026 — Data Hub

Pipeline de datos en tiempo (casi) real del Mundial 2026, con ingesta automatizada, transformación en Python y dashboard público interactivo.

**🔗 Dashboard en vivo:** [mundial-2026-data.streamlit.app](https://mundial-2026-data.streamlit.app)

---

## 📐 Arquitectura

```
cron-job.org (trigger externo, cada 10 min)
         ↓
GitHub Actions (workflow_dispatch)
  └── ingestion/fetch_data.py
         ↓
football-data.org (API)
         ↓
data/processed/*.csv  (almacenamiento público en GitHub)
         ↓
Streamlit Cloud (dashboard/app.py)
  └── Lee los CSVs directo desde GitHub raw
  └── Cache de 30s + boton de refresh manual
```

El pipeline funciona sin servidor propio ni base de datos: cron-job.org dispara el trigger al minuto exacto, GitHub Actions hace de orquestador (corre el script y commitea), y el repo de GitHub hace de almacenamiento intermedio. Streamlit Cloud lee esos CSVs públicos y los renderiza.

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

**⚠️ Nota sobre el scheduler de GitHub:** inicialmente el plan era usar el `schedule` (cron) nativo de GitHub Actions para disparar la ingesta cada 10 minutos. En la práctica, GitHub Free **no respeta esos intervalos cortos** — los runs scheduled llegaron a espaciarse varias horas entre sí, incluso con múltiples entradas de cron configuradas. Es una limitación conocida de la plataforma en cuentas gratuitas, no un error de configuración.

**Solución adoptada:** se sacó el `schedule` del workflow y se reemplazó por un disparador externo usando [cron-job.org](https://cron-job.org) (gratis), que llama a la API de GitHub (`workflow_dispatch`) cada 10 minutos vía `POST`:

```
POST https://api.github.com/repos/dbouzada/mundial-2026-data/actions/workflows/pipeline.yml/dispatches
Headers:
  Authorization: Bearer <personal access token>
  Accept: application/vnd.github+json
  Content-Type: application/json
Body:
  {"ref":"main"}
```

Esto sí es confiable al minuto, porque cron-job.org no tiene las limitaciones de scheduling de GitHub.

**Triggers actuales del workflow:**
- `workflow_dispatch` — disparado externamente por cron-job.org cada 10 minutos
- `push` a `main` con cambios en `ingestion/` — corre automáticamente si se actualiza el script

**Token de GitHub usado por cron-job.org:**
- Fine-grained personal access token, scope limitado al repo `mundial-2026-data`
- Permiso necesario: **Actions → Read and write** (con solo "Read" devuelve 403 al intentar disparar el workflow)

**Manejo de corridas simultáneas:** el step de commit hace `git pull --rebase --autostash` antes de `git push`, para evitar que dos ejecuciones cercanas en el tiempo se pisen al subir los CSVs.

**Secrets necesarios** (Settings → Secrets and variables → Actions):
- `FD_API_KEY`

**Permisos requeridos** (Settings → Actions → General → Workflow permissions):
- *Read and write permissions* (para que el bot pueda commitear los CSVs)

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
- Fase Eliminatoria — bracket en árbol (16avos a Final + 3er puesto), colapsado en un expander al final de la página. Se activa solo cuando arranca la fase eliminatoria; antes de eso muestra un mensaje explicando que los cruces dependen del cierre de la fase de grupos

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
- GitHub Actions como orquestador, no como scheduler: el cron nativo de GitHub Actions no es confiable en cuentas free para intervalos cortos (en pruebas reales, runs programados cada 10 minutos llegaron a espaciarse varias horas). Se resolvió moviendo el disparo a cron-job.org, que llama a la API de GitHub vía `workflow_dispatch` con precisión al minuto.
- Horarios hardcodeados para Argentina: la API de football-data.org no siempre confirma el horario exacto de partidos futuros (devuelve 00:00 UTC como placeholder), así que se mantiene un diccionario con los horarios oficiales confirmados por FIFA como fallback.
- Streamlit en vez de un framework JS: prioriza velocidad de desarrollo y mantenimiento simple sobre personalización visual extrema, dado que el objetivo es un dashboard de datos, no un producto consumer.
- Bracket de eliminatorias sin inventar cruces: la API devuelve `null` en los equipos de partidos de fase eliminatoria todavía no definidos (no manda placeholders tipo "1A"). Además, los cruces exactos de 16avos solo se conocen al cerrar la fase de grupos, porque dependen de qué terceros lugares clasifican. Por eso el dashboard muestra "Por definir" en esos casos en vez de simular un cruce que todavía no es oficial — apenas la API resuelve el nombre real, se actualiza solo en la siguiente corrida del pipeline, sin intervención manual.

---

## ✍️ Autor

**Diego Bouzada** — Data Analytics Engineer

GitHub: github.com/dbouzada · LinkedIn: linkedin.com/in/bouzadadiego
