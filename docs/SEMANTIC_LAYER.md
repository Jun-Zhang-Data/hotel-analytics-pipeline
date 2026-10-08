# Semantic Layer MVP

The semantic layer provides a governed business interface over trusted reporting marts.

## Purpose

Stakeholders should not need to know warehouse table names or SQL expressions. The semantic catalog defines approved business metrics and dimensions, and application code converts a structured semantic query into parameterized SQL.

The current MVP intentionally does **not** let an LLM generate unrestricted SQL. Natural-language parsing can be added later as a thin layer that produces the same validated semantic-query JSON.

## Current domain

`hotel_operations`

Source relation:

`analytics_dev.mart_power_bi_hotel_daily`

The schema can be overridden with the `TARGET_SCHEMA` environment variable.

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
