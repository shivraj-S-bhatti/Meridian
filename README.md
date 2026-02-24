# Meridian

Meridian is a web-scale evidence compiler for IPO alpha research.

It exposes one flagship function:

```python
ipo_dislocation_score(company_id, as_of_ts, horizon_days=28)
```

The system combines:

- A C++ data plane (`cpp/`) for high-throughput fetch/dispatch skeleton.
- A Python control plane (`python/meridian/`) for DOM analysis, agentic contradiction reasoning, and scoring.
- PostgreSQL-backed lineage and signal storage (`db/schema.sql`).
- A premium landing page (`landing/index.html`).

## API

Run from `python/`:

```bash
python3 -m pip install -r requirements.txt
uvicorn meridian.api:app --reload --port 8080
```

Endpoints:

- `POST /v1/ipo/score`
- `GET /v1/ipo/{company_id}/evidence-graph?as_of=...`
- `POST /v1/ipo/backtest`
- `GET /v1/system/throughput`

## Quick Start

```bash
docker compose up -d postgres
cd python
python3 -m pip install -r requirements.txt
export DATABASE_URL=postgresql://crawler:crawler@localhost:5432/crawler
uvicorn meridian.api:app --reload --port 8080
```

Sample call:

```bash
curl -X POST localhost:8080/v1/ipo/score \
  -H "content-type: application/json" \
  -d '{"company_id":"ACME-IPO","as_of_ts":"2026-02-24T15:30:00Z","horizon_days":28}'
```

## C++ Engine Skeleton

```bash
mkdir -p cpp/build && cd cpp/build
cmake ..
cmake --build .
./stashy_engine --db postgresql://crawler:crawler@localhost:5432/crawler --workers 16
```

The C++ engine includes optional `libcurl` and `libpq` integration points and compiles with deterministic stubs if those libraries are unavailable.

## Tests

From `python/`:

```bash
pytest -q
```

## Notes

This repository is intentionally scoped for shadow research and explainability, not live execution.
