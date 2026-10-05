# JobbRadar

![CI](https://github.com/william-waly/JobbRadar/actions/workflows/ci.yml/badge.svg)

End-to-end data-pipeline som samler jobbannonser fra NAV sitt offentlige API, strukturerer dem med en lokal LLM, og gjør dataene tilgjengelige gjennom et REST API og et interaktivt dashboard.

Bygget som et portfolio-prosjekt for å demonstrere praktisk data engineering og full-stack-kompetanse — fra rå datainnsamling til ferdig presentert innsikt.

## Arkitektur

```
NAV pam-stilling-feed API
        │
        ▼
   Scrapy Spider
        │
        ▼
   Redis-kø ("jobs:queue")
        │
        ▼
   Python Worker
        │
   ┌────┴────┐
   ▼         ▼
Cleaning   LLM-ekstraksjon (Ollama)
   │         │
   └────┬────┘
        ▼
Pydantic-validering
        │
        ▼
PostgreSQL (idempotent upsert)
        │
        ▼
   FastAPI
        │
        ▼
   Streamlit Dashboard
```

Scraping og prosessering er bevisst frikoblet via en Redis-kø: scraperen vet ingenting om hva som skjer med dataene etterpå, og workeren kan skaleres uavhengig ved behov.

## Teknologistack

| Lag | Teknologi |
|---|---|
| Scraping | Scrapy |
| Kø | Redis |
| Prosessering | Python worker med retry/backoff |
| LLM | Ollama (lokal, `gemma3:4b`), skjema-tvunget JSON-output |
| Validering | Pydantic |
| Database | PostgreSQL, SQLAlchemy, Alembic (migrasjoner) |
| API | FastAPI |
| Dashboard | Streamlit |
| Testing | pytest |
| Kodekvalitet | Ruff |
| CI/CD | GitHub Actions |
| Containerisering | Docker / Docker Compose |

## Hvorfor disse valgene

- **Redis som kø, ikke Kafka**: prosjektets skala trenger ikke partisjonert meldingsrouting — en enkel, pålitelig FIFO-kø er nok, og enklere å forklare og drifte.
- **Lokal LLM via Ollama, ikke en sky-API**: null kostnad per kall, fungerer offline, full kontroll over data. Trade-off: mindre nøyaktig enn en stor skymodell, delvis kompensert med skjema-tvunget generering for strukturell pålitelighet.
- **Idempotent upsert (`ON CONFLICT DO UPDATE`), ikke "sjekk-så-sett-inn"**: atomisk på databasenivå, trygt selv med flere samtidige workers — unngår race conditions som et enklere mønster ville introdusert.
- **FastAPI og Streamlit som separate tjenester**: dashboardet snakker kun med API-et, aldri direkte med databasen — holder datatilgangslogikken samlet ett sted og gjør API-et gjenbrukbart av andre klienter.

## Komme i gang

### Forutsetninger

- Python 3.13
- Docker Desktop
- [Ollama](https://ollama.com) installert lokalt, med en modell hentet (f.eks. `ollama pull gemma3:4b`)

### Oppsett

```bash
git clone https://github.com/<ditt-brukernavn>/JobbRadar.git
cd JobbRadar

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -e ".[dev]"

cp .env.example .env            # fyll inn egne verdier

docker compose up -d
alembic upgrade head
```

### Kjør hele stacken

```bash
docker compose up -d --build
```

Dette starter PostgreSQL, Redis, worker, FastAPI og Streamlit samlet.

- API-dokumentasjon: http://localhost:8000/docs
- Dashboard: http://localhost:8501

### Hent data

```bash
scrapy crawl nav_feed -a hours_back=24 -a max_pages=5
```

## Testing

```bash
pytest -v
ruff check .
```

## Prosjektstruktur

```
JobbRadar/
├── app/
│   ├── scraper/       # Scrapy-spider mot NAV sitt API
│   ├── queue/          # Redis-tilkobling
│   ├── worker/          # Prosesseringsloop, retry-logikk
│   ├── llm/              # Ollama-integrasjon, Pydantic-skjema
│   ├── database/          # SQLAlchemy-modeller, repository
│   └── api/                # FastAPI-endepunkter
├── dashboard/                # Streamlit-dashboard
├── alembic/                    # Databasemigrasjoner
├── tests/                       # pytest unit-tester
└── docker-compose.yml
```

## Kjente begrensninger

- LLM-kategorisering er ikke alltid presis (liten, lokal modell — bevisst trade-off mot hastighet/kostnad)
- Integrasjonstester mot ekte database/Redis er ikke bygget ennå — kun unit-tester på ren forretningslogikk
- Statistikk over tid ("nye jobber per dag") krever lengre datainnsamlingsperiode for å gi mening

## Lisens

MIT