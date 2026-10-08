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

Set the API key and model only in your local environment. Do not commit credentials.

PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_SEMANTIC_MODEL="your-api-model"
```

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
