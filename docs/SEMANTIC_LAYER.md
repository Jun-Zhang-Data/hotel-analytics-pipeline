# Semantic Layer MVP

The semantic layer provides a governed business interface over trusted reporting marts.

## Purpose

Stakeholders should not need to know warehouse table names or SQL expressions. The semantic catalog defines approved business metrics and dimensions, and application code converts a structured semantic query into parameterized SQL.

The current MVP intentionally does **not** let an LLM generate unrestricted SQL. Natural-language parsing can be added later as a thin layer that produces the same validated semantic-query JSON.

## Current domains

- `hotel_operations`
- `data_quality`

Default DEV source relations:

- `analytics_dev_ops.mart_power_bi_hotel_daily`
- `analytics_dev_dq.mart_power_bi_dq_rule_daily`

The domain schemas can be overridden with `HOTEL_OPS_SCHEMA` and `DATA_QUALITY_SCHEMA`.

## Governed metrics

- `total_bookings`
- `cancelled_bookings`
- `active_bookings`
- `total_revenue`
- `cancellation_rate`
- `revenue_per_booking`

## Governed dimensions

- `booking_date`
- `hotel`
- `city`

## Query contract

Example semantic query:

```json
{
  "metric": "total_revenue",
  "dimensions": ["hotel"],
  "filters": [
    {
      "dimension": "city",
      "operator": "=",
      "value": "Stockholm"
    }
  ],
  "date_range": {
    "start": "2026-09-01",
    "end": "2026-09-30"
  },
  "order": "desc",
  "limit": 5
}
```

The validator only accepts metrics and dimensions declared in the catalog. Filter values are passed to PostgreSQL as query parameters instead of being interpolated into SQL.

## Dry run

From the repository root:

```bash
python scripts/query_semantic.py \
  --query-json '{"metric":"total_revenue","dimensions":["hotel"],"date_range":{"start":"2026-09-01","end":"2026-09-30"},"limit":5}' \
  --dry-run
```

A dry run validates the semantic query and prints the SQL plus parameters without connecting to PostgreSQL.

## Execute against the local warehouse

After the pipeline has built the reporting marts:

```bash
python scripts/query_semantic.py \
  --query-json '{"metric":"cancellation_rate","dimensions":["city"],"limit":10}'
```

Database connection settings use the existing `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` environment variables.

## Natural-language extension

The next layer can convert a stakeholder question such as:

> Which hotel generated the most revenue in September?

into the governed JSON contract:

```json
{
  "metric": "total_revenue",
  "dimensions": ["hotel"],
  "date_range": {
    "start": "2026-09-01",
    "end": "2026-09-30"
  },
  "order": "desc",
  "limit": 1
}
```

The LLM should only produce the semantic query. Validation and SQL generation remain deterministic application responsibilities.


## Optional LLM parser

The deterministic rule parser remains available for reproducible local tests. An optional LLM parser can translate more varied stakeholder wording into the same governed semantic-query contract.

The LLM is not allowed to write or execute SQL. Its output is parsed as JSON and then passed through the same deterministic semantic validator before SQL generation.

Store local API settings in a repository-root `.env` file. The semantic package loads it automatically and does not override environment variables that are already set by the shell or deployment platform.

Create the local file from the safe template:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` locally:

```text
OPENAI_API_KEY=your-real-key
OPENAI_SEMANTIC_MODEL=your-api-model
```

The repository already ignores `.env`, so the real key is not committed. Never put a real key in `.env.example`.

Install dependencies:

```powershell
pip install -r requirements-semantic.txt
```

Run an LLM-backed dry run:

```powershell
python -m scripts.query_natural_language --parser llm --question "Which hotel generated the most revenue in September 2026?" --dry-run
```

Run the governed query against PostgreSQL:

```powershell
python -m scripts.query_natural_language --parser llm --question "Which hotel generated the most revenue in September 2026?"
```

Start the interactive terminal chat:

```powershell
python -m scripts.chat_semantic
```

Questions that cannot be mapped safely should request clarification instead of producing unrestricted SQL.


## Multi-domain routing

The semantic layer now supports multiple governed domains through `semantic/domains.yml`.

Current domains:

- `hotel_operations` -> `semantic/hotel_operations.yml`
- `data_quality` -> `semantic/data_quality.yml`

A question can either specify a domain explicitly or use automatic routing.

Examples:

```powershell
python -m scripts.query_natural_language --domain hotel_operations --parser llm --question "Which hotel generated the most revenue in September 2026?"
```

```powershell
python -m scripts.query_natural_language --domain data_quality --parser llm --question "Which source system had the lowest data quality pass rate in September 2026?"
```

Automatic routing:

```powershell
python -m scripts.query_natural_language --domain auto --parser llm --question "Which source system had the lowest data quality pass rate in September 2026?"
```

The flow is:

```text
stakeholder question
-> governed domain router
-> domain-specific semantic catalog
-> semantic query parser
-> deterministic validator
-> deterministic SQL generator
-> domain mart
-> formatted answer
```

The routing layer does not grant access to arbitrary warehouse objects. Each domain can only query the source relation, metrics, dimensions, filters, and row limits declared in its own semantic catalog.


## Physical domain schemas

The reporting marts consumed by the semantic layer are physically separated by stakeholder domain.

In DEV:

```text
analytics_dev_ops.mart_power_bi_hotel_daily
analytics_dev_dq.mart_power_bi_dq_rule_daily
```

The shared core models still live in the base analytics schema and remain reusable. Only the reporting marts intended for a stakeholder domain are exposed through that domain's semantic catalog. This gives the project both logical governance through the catalog and physical separation through PostgreSQL schemas.


## Database access control

Each semantic domain now has a PostgreSQL read role in addition to its catalog and schema boundary:

```text
hotel_operations
-> hotel_ops_reader
-> analytics_dev_ops

data_quality
-> data_quality_reader
-> analytics_dev_dq
```

After dbt builds the domain marts, configure the local roles:

```powershell
python scripts/configure_semantic_access.py
```

The semantic query service executes each query with `SET LOCAL ROLE` using the role declared in that domain's catalog. This means a hotel-operations query runs as `hotel_ops_reader`, while a data-quality query runs as `data_quality_reader`.

CI verifies both positive and negative access: each role can read its own domain mart and is blocked from the other domain mart.

The local `analytics` login is granted membership in both reader roles so the semantic service can switch roles. In a real deployment, role creation and membership would normally be managed by the platform or database administration layer rather than application startup.


## Stakeholder HTTP API

The same governed query flow is now exposed through a small FastAPI service. The API does not accept SQL. It accepts a stakeholder question plus an optional domain and parser mode, then uses the same domain router, semantic catalog, validator, SQL generator and database role used by the CLI.

Install the lightweight semantic dependencies:

```powershell
pip install -r requirements-semantic.txt
```

Start the local API from the repository root:

```powershell
python -m uvicorn semantic_api.app:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/health"
```

List governed domains:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/domains"
```

Ask a stakeholder question:

```powershell
$body = @{
  question = "Which hotel generated the most revenue in September 2026?"
  domain = "auto"
  parser = "llm"
  include_details = $false
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/query" -ContentType "application/json" -Body $body
```

By default the API returns only the selected domain and stakeholder-friendly answer. Internal SQL, rows, semantic JSON and database role are returned only when `include_details=true`.

This API is a local MVP and does not add end-user authentication, TLS termination or internet-facing deployment configuration.


## Browser UI

The FastAPI service now includes a lightweight local stakeholder interface.

Start the API:

```powershell
python -m uvicorn semantic_api.app:app --host 127.0.0.1 --port 8000
```

Restart Uvicorn after editing `.env`, because the process reads the local environment when the semantic package starts.

Then open this address in a browser:

```text
http://127.0.0.1:8000/
```

The page lets a stakeholder choose automatic or explicit domain routing, choose the LLM or deterministic parser, ask a natural-language question, and optionally inspect governed query details.

The browser does not accept SQL from the user. It calls the same `/query` endpoint and therefore keeps the same semantic validation and domain-role enforcement as the CLI and HTTP API.


## Semantic query observability

Executed and dry-run semantic requests now receive a unique `query_run_id` and are recorded in `ops.semantic_query_runs`.

The audit record stores operational metadata such as parser mode, requested and selected domain, governed metric, database access role, execution status, row count and duration. It stores a SHA-256 fingerprint of the normalized stakeholder question rather than the raw question text.

Initialize an existing local database after pulling this change:

```powershell
docker compose exec warehouse psql -U analytics -d hotel -f /docker-entrypoint-initdb.d/01_init.sql
```

Inspect recent semantic activity:

```powershell
docker compose exec warehouse psql -U analytics -d hotel -c "select query_run_id, selected_domain, metric, parser, status, row_count, duration_ms, completed_at from ops.semantic_query_runs order by completed_at desc limit 10;"
```

The HTTP API also returns `query_run_id` with each successful answer so a user-visible response can be correlated with the operational audit trail without exposing raw stakeholder questions.
