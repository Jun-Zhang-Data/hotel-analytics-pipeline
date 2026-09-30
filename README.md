# Hotel Analytics Pipeline 2.0

A production-style local analytics engineering project for hotel booking data, built with PostgreSQL, dbt, Apache Airflow, Docker, Python, and GitHub Actions.

The project demonstrates how operational booking and payment data can be ingested and standardized, enriched with governed master/reference data, validated through explicit data-quality rules, routed into structured exception outputs, transformed into trusted analytical models, and exposed through reporting-ready marts. The production-grade upgrade extends that baseline with explicit recovery, source contracts, operational health checks, controlled backfills, CI failure simulations, run metadata, and operational documentation.

## What this repository implements

The pipeline processes operational booking and payment data and enriches them with governed hotel master, source-system reference, and source-to-canonical mapping data. It includes:

- raw ingestion with source traceability and deterministic idempotency
- controlled date/range backfills
- operational ingestion-run metadata in `ops.ingestion_runs`
- executable source data contracts with fail-fast breaking-change detection
- dbt staging, intermediate, core, quality, and mart layers
- canonical hotel master data
- source-system reference data
- effective-date-aware source-to-canonical hotel mappings
- mapping, completeness, and validity controls
- structured exception tables with severity and ownership metadata
- data-quality KPI models
- operational health checks for freshness, DQ pass rate, mapping coverage, volume change, and failed ingestions
- automated reliability scenarios for duplicate delivery, breaking contracts, late arrivals, historical corrections, and downstream failure recovery
- source-to-target mapping documentation
- automated UAT acceptance tests
- Power BI-ready operational and data-quality marts
- Airflow orchestration with retries, contract gating, backfill parameters, and a final health gate
- Dockerized local infrastructure
- GitHub Actions CI with linting, integration tests, idempotency proof, deliberate contract-failure simulation, and controlled recovery scenarios
- runbook, incident examples, testing strategy, reliability scenario evidence, data contracts, and Architecture Decision Records

## End-to-end data flow

```text
Operational CSV sources (bookings, payments)
→ executable source-contract validation
→ Python ingestion
→ PostgreSQL raw tables + ops.ingestion_runs
→ dbt staging
→ source-to-canonical hotel mapping ← governed dbt seeds
                                  ├─ hotel master
                                  ├─ source-system reference
                                  └─ source-to-canonical mappings
→ data-quality validation
→ structured exceptions OR trusted booking flow
→ core facts / governed dimensions
→ operational + DQ marts
→ operational health gate
→ Power BI-ready reporting layer
```

The generated operational source files are `bookings.csv` and `payments.csv`. Governed hotel master/reference inputs are maintained separately as dbt seeds and loaded during `dbt build`.

## Reliability and recovery

### Idempotent ingestion

Each raw source row receives a deterministic `ingestion_id` derived from its business key and `source_updated_at`. Raw tables use that key as a primary key and ingestion uses `ON CONFLICT DO NOTHING`, so an identical source delivery can be processed repeatedly without duplicating raw records.

Every ingestion writes operational metadata to `ops.ingestion_runs`, including candidate rows, inserted rows, duplicates skipped, source timestamp range, backfill range, status, and errors. CI loads the same deterministic fixture twice and asserts the second run inserts zero rows.

### Controlled backfill

The loader supports:

```bash
python scripts/load_raw.py --start-date 2026-09-01 --end-date 2026-09-02
```

Airflow exposes `backfill_start` and `backfill_end` parameters and passes them to ingestion. Reprocessing remains idempotent, so historical ranges can be rerun safely.

### Late-arriving data and historical correction

Raw history preserves multiple legitimate source versions for the same `booking_id` when `source_updated_at` changes. `int_bookings_latest` selects the newest source version before downstream trusted models are built.

CI proves this behavior in two deterministic scenarios:

- a newer `B001` update arrives after the baseline load; the affected booking date is reprocessed, raw keeps both versions, and trusted output resolves to the newest status with one trusted booking row;
- a corrected historical `B003` version is appended and bounded-reprocessed; trusted output receives the corrected field while preserving one-row-per-booking grain.

### Partial downstream failure recovery

CI also forces a singular dbt test to fail after raw ingestion has already succeeded. The failure is expected and visible; CI then runs a clean `dbt build` from the unchanged committed raw state and verifies the trusted dataset recovers correctly.

This demonstrates that successful upstream ingestion does not need to be destructively repeated simply because a downstream transformation/test stage failed.

### Retry behavior

Airflow uses controlled retries for transient task failures. The source-contract task and final operational-health task intentionally do not retry because they represent deterministic blocking conditions that require investigation rather than blind repetition.

See `docs/RELIABILITY_SCENARIOS.md` for the scenario-to-mechanism evidence matrix and reproducible test sequence.

## Source data contracts

Executable contracts live in:

`config/data_contracts.json`

They define required columns, expected logical types, and selected allowed values. `scripts/validate_source_contracts.py` runs before ingestion in both Airflow and CI.

Breaking changes such as a missing required column, incompatible type, or disallowed value fail fast before trusted data is produced. Additional columns are treated as non-breaking warnings. CI deliberately removes a required source column, proves the contract gate fails, restores the fixture, and proves validation recovers.

See `docs/DATA_CONTRACTS.md` for compatibility rules and change handling.

## Data quality framework

The implemented DQ framework currently covers three quality dimensions:

### Mapping coverage

`DQ_MAP_HOTEL_001`

A booking source hotel code must resolve to an active canonical hotel mapping that is valid for the booking date.

Failures are written to `dq_unmapped_hotel_bookings`.

### Completeness

`DQ_COMP_GUEST_001`

Mapped bookings must contain `guest_id`.

Failures are written to `dq_missing_guest_id`.

### Validity

`DQ_VALID_STAY_001`

`check_out_date` must not be before `check_in_date`.

Failures are written to `dq_invalid_stay_dates`.

Records that fail implemented trusted-data rules are excluded from the trusted booking fact. Structured exception outputs include stable rule IDs plus severity, responsible domain, affected record key, detection timestamp, and exception status.

## Data-quality KPIs

`fct_data_quality_results` provides rule-level analytical results including:

- records checked
- records passed
- records failed
- pass rate
- mapping coverage rate where applicable

Reporting marts include:

- `mart_dq_daily`
- `mart_dq_by_source`
- `mart_exception_summary`
- `mart_power_bi_dq_rule_daily`

The sample dataset intentionally contains mapped records and known failures so CI can validate expected behavior.

## Operational health monitoring

`scripts/check_operational_health.py` produces a machine-readable health payload and classifies checks as `OK`, `INFO`, `WARNING`, or `BLOCKING`.

Current checks cover:

- raw booking freshness
- overall DQ pass rate
- hotel mapping coverage
- run-to-run booking volume change
- failed ingestion runs in the previous 24 hours

Thresholds are configurable through environment variables. A blocking health result exits non-zero so Airflow can stop the pipeline from being treated as healthy.

This is intentionally a lightweight local observability design rather than a claim of enterprise monitoring infrastructure.

## Trusted analytical models

Trusted downstream booking records flow through validated intermediate models into:

- `fct_bookings`
- `dim_hotels`
- `mart_hotel_daily`

Records with implemented DQ failures are routed to exception models rather than silently entering trusted outputs.

## Power BI-ready reporting layer

The repository includes reporting-ready dbt models designed for direct BI consumption:

### `mart_power_bi_hotel_daily`

Daily hotel-level metrics including:

- total bookings
- active bookings
- cancelled bookings
- cancellation rate
- total revenue
- revenue per booking
- hotel and city attributes

### `mart_power_bi_dq_rule_daily`

Daily rule/source-level DQ reporting including:

- source system
- DQ rule
- quality dimension
- records checked
- passed / failed counts
- pass rate
- mapping coverage rate

### `mart_exception_summary`

Exception counts by date, source, rule, quality dimension, and exception status.

The repository does **not** include a `.pbix` file, Power BI Service deployment, or configured Power BI refresh. It implements the downstream data layer that a Power BI model can consume.

## Source-to-target mapping

`docs/source_to_target_mapping.csv` documents implemented field-level lineage across:

```text
source system
→ source table / field
→ transformation rule
→ target model / field
→ validation rule
```

This provides explicit traceability from operational inputs to trusted analytical outputs.

## UAT and acceptance criteria

`docs/uat_test_cases.md` records Given / When / Then acceptance scenarios with expected results, actual results, status, and automated evidence.

Automated dbt UAT tests verify scenarios including:

- unmapped hotel booking quarantine
- missing guest quarantine
- invalid stay-date quarantine
- valid bookings reaching trusted output
- expected mapping-coverage KPI results

The UAT statuses are marked PASS only after the linked tests pass in GitHub Actions CI.

## Continuous integration

GitHub Actions validates pull requests and pushes to `master` by:

- starting PostgreSQL 16
- linting and compiling Python
- initializing warehouse, raw, analytics, and operational schemas
- generating deterministic booking and payment sample data
- validating executable source contracts
- deliberately breaking a required source column and proving the contract gate blocks it
- restoring the source and proving validation recovers
- loading operational raw data
- loading the same data again and asserting zero duplicate inserts
- running `dbt debug`
- running `dbt build`, including seeds and all dbt tests
- appending a late-arriving booking update, bounded-reprocessing it, and verifying latest-version trusted behavior
- appending a historical correction, bounded-reprocessing it, and verifying corrected trusted state without duplicate business rows
- deliberately forcing a downstream dbt test failure and proving a clean rebuild recovers from unchanged raw state
- executing operational-health checks against deterministic thresholds

This provides executable evidence for safe change management and recovery behavior before changes are merged.

## Pipeline orchestration

Apache Airflow orchestrates the local workflow:

```text
generate_source_data
→ validate_source_contracts
→ ingest_raw
→ dbt_build_prod
→ operational_health
```

Docker Compose provides the local runtime for PostgreSQL, Airflow, and the dbt project environment.

## Repository documentation

Key documentation:

- `docs/architecture.md`
- `docs/RUNBOOK.md`
- `docs/DATA_CONTRACTS.md`
- `docs/TESTING.md`
- `docs/RELIABILITY_SCENARIOS.md`
- `docs/INCIDENT_EXAMPLES.md`
- `docs/data_quality_rules.md`
- `docs/master_reference_data.md`
- `docs/source_to_target_mapping.csv`
- `docs/uat_test_cases.md`
- `docs/power_bi_reporting_contract.md`
- `docs/portfolio_evidence.md`
- `docs/adr/001-postgres-dbt-airflow.md`
- `docs/adr/002-idempotent-raw-ingestion.md`
- `docs/adr/003-contract-gate-before-ingestion.md`

## Tech stack

Python · SQL · PostgreSQL · dbt · Apache Airflow · Docker · Docker Compose · Git · GitHub · GitHub Actions

## Scope boundaries

This is a local, containerized portfolio implementation rather than a deployed enterprise platform. It demonstrates production engineering thinking through executable reliability controls and operational evidence.

Implemented:

- PostgreSQL warehouse
- Python ingestion for operational booking/payment data
- deterministic idempotent ingestion
- controlled backfill
- late-arriving version handling
- historical correction/reprocessing evidence
- partial downstream failure/recovery evidence
- ingestion-run observability
- executable source data contracts
- dbt transformation and validation
- seed-backed master/reference mapping
- structured exception outputs
- DQ KPI marts
- operational health checks
- formal UAT tests
- Power BI-ready marts
- Airflow orchestration
- GitHub Actions CI
- runbook, incident examples, reliability scenario evidence, testing strategy, and ADRs

Not implemented:

- Azure or Microsoft Fabric
- cloud production deployment
- Kubernetes, Kafka, or Terraform
- `.pbix` dashboard file
- Power BI Service deployment / refresh
- enterprise MDM tooling
- centralized enterprise monitoring/alert delivery
- production secrets management
- full exception case-management workflow with human remediation UI

## Start locally

```bash
docker compose up -d --build
```

Generate operational sample data:

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project && python scripts/generate_data.py"
```

Validate source contracts:

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project && python scripts/validate_source_contracts.py"
```

Load operational raw data:

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project && python scripts/load_raw.py"
```

Run a bounded backfill:

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project && python scripts/load_raw.py --start-date 2026-09-01 --end-date 2026-09-02"
```

Build DEV models and load governed dbt seeds:

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project/dbt_hotel && dbt build --target dev --profiles-dir ."
```

Run operational health checks:

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project && TARGET_SCHEMA=analytics_dev python scripts/check_operational_health.py"
```

Inspect operational ingestion history:

```bash
docker compose exec warehouse psql -U analytics -d hotel -c "select * from ops.ingestion_runs order by started_at desc;"
```

Inspect DQ reporting:

```bash
docker compose exec warehouse psql -U analytics -d hotel -c "select * from analytics_dev.mart_power_bi_dq_rule_daily order by check_date, source_system_code, rule_id;"
```

## Airflow UI

Open `http://localhost:8080`.

Default local credentials:

- username: `admin`
- password: `admin`

Enable and trigger:

`hotel_analytics_pipeline`

Optional Airflow run parameters:

```json
{
  "backfill_start": "2026-09-01",
  "backfill_end": "2026-09-02"
}
```

## Stop

```bash
docker compose down
```

Remove local database volumes too:

```bash
docker compose down -v
```
