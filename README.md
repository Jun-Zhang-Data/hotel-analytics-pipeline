# Hotel Analytics Pipeline 2.0

A production-style local analytics engineering project for hotel booking data, built with PostgreSQL, dbt, Apache Airflow, Docker, Python, and GitHub Actions.

The project demonstrates how operational booking and payment data can be ingested and standardized, enriched with governed master/reference data, validated through explicit data-quality rules, routed into structured exception outputs, transformed into trusted analytical models, and exposed through reporting-ready marts.

## What this repository implements

The pipeline processes operational booking and payment data and enriches them with governed hotel master, source-system reference, and source-to-canonical mapping data. It includes:

- raw ingestion with source traceability and idempotent loading
- dbt staging, intermediate, core, quality, and mart layers
- canonical hotel master data
- source-system reference data
- effective-date-aware source-to-canonical hotel mappings
- mapping, completeness, and validity controls
- structured exception tables
- data-quality KPI models
- source-to-target mapping documentation
- automated UAT acceptance tests
- Power BI-ready operational and data-quality marts
- Airflow orchestration
- Dockerized local infrastructure
- GitHub Actions CI
- a demonstrated regression-testing workflow for safe SQL refactoring

## End-to-end data flow

```text
Operational CSV sources (bookings, payments)
→ Python ingestion
→ PostgreSQL raw tables
→ dbt staging
→ source-to-canonical hotel mapping ← governed dbt seeds
                                  ├─ hotel master
                                  ├─ source-system reference
                                  └─ source-to-canonical mappings
→ data-quality validation
→ structured exceptions OR trusted booking flow
→ core facts / governed dimensions
→ operational + DQ marts
→ Power BI-ready reporting layer
```

The generated operational source files are `bookings.csv` and `payments.csv`. Governed hotel master/reference inputs are maintained separately as dbt seeds and loaded during `dbt build`.

## Master and reference data

The project separates three responsibilities:

- `dim_hotel_master`: canonical hotel entities
- `dim_source_system_reference`: governed source-system reference values
- `map_hotel_source_to_canonical`: source-specific hotel code mappings

For example, different source systems can use different values for the same hotel:

```text
PMS_A / STO01  → H001
PMS_B / SE-STH → H001
```

The mapping layer includes dbt controls for required fields, accepted lifecycle values, referential integrity, effective-date-aware mapping logic, and safeguards against a booking matching multiple temporal mappings.

The governed hotel master is the source of truth for the downstream `dim_hotels` dimension.

## Data quality framework

The implemented DQ framework currently covers three quality dimensions:

### Mapping coverage

`DQ_MAP_HOTEL_001`

A booking source hotel code must resolve to an active canonical hotel mapping that is valid for the booking date.

Failures are written to:

`dq_unmapped_hotel_bookings`

### Completeness

`DQ_COMP_GUEST_001`

Mapped bookings must contain `guest_id`.

Failures are written to:

`dq_missing_guest_id`

### Validity

`DQ_VALID_STAY_001`

`check_out_date` must not be before `check_in_date`.

Failures are written to:

`dq_invalid_stay_dates`

Records that fail implemented trusted-data rules are excluded from the trusted booking fact.

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

The sample dataset intentionally contains mapped records and known failures so CI can validate the expected behavior.

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

## Safe SQL refactoring and regression testing

The repository also demonstrates a safe SQL refactoring workflow.

`int_bookings_enriched` was refactored from direct joins into clearer CTE-based logic while preserving business behavior and output structure. Temporary old-vs-new regression checks compared:

- missing booking IDs
- extra booking IDs
- field-level parity
- aggregate-level parity

After parity was verified, the refactored model replaced the old implementation and the temporary migration tests were removed, while long-lived business-rule tests remained.

## Continuous integration

GitHub Actions validates pull requests and pushes to `master` by:

- starting PostgreSQL 16
- initializing warehouse schemas and operational raw tables
- generating deterministic booking and payment sample data
- loading operational raw data with Python
- running `dbt debug`
- running `dbt build`, including seeds
- executing model tests, DQ tests, business-rule tests, and UAT tests

This provides integration-level validation before changes are merged.

## Pipeline orchestration

Apache Airflow orchestrates the local workflow:

```text
generate_source_data
→ ingest_raw
→ dbt_build_prod
```

Docker Compose provides the local runtime for PostgreSQL, Airflow, and the dbt project environment.

## Repository documentation

Key documentation:

- `docs/master_reference_data.md`
- `docs/data_quality_rules.md`
- `docs/source_to_target_mapping.csv`
- `docs/uat_test_cases.md`
- `docs/power_bi_reporting_contract.md`
- `docs/architecture.md`
- `docs/portfolio_evidence.md`

## Tech stack

Python · SQL · PostgreSQL · dbt · Apache Airflow · Docker · Docker Compose · Git · GitHub · GitHub Actions

## Engineering and data-management concepts demonstrated

- layered ELT architecture
- dimensional modeling
- master data management concepts
- reference data management
- source-to-standard mappings
- temporal/effective-date mapping logic
- data-quality rule design
- completeness, validity, mapping coverage, and referential-integrity controls
- structured exception handling
- data-quality KPI monitoring
- source-to-target mapping and lineage documentation
- UAT / acceptance testing
- Power BI-ready downstream modeling
- SQL regression testing
- workflow orchestration
- CI validation
- containerized local infrastructure
- Git branching and pull-request workflows

## Scope boundaries

This is a local, containerized portfolio implementation rather than a deployed enterprise platform.

Implemented:

- PostgreSQL warehouse
- Python ingestion for operational booking/payment data
- dbt transformation and validation
- seed-backed master/reference mapping
- structured exception outputs
- DQ KPI marts
- formal UAT tests
- Power BI-ready marts
- Airflow orchestration
- GitHub Actions CI

Not implemented:

- Azure or Microsoft Fabric
- cloud production deployment
- `.pbix` dashboard file
- Power BI Service deployment / refresh
- enterprise MDM tooling
- centralized production monitoring
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

Load operational raw data:

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project && python scripts/load_raw.py"
```

Build DEV models and load governed dbt seeds:

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project/dbt_hotel && dbt build --target dev --profiles-dir ."
```

Inspect an operational reporting mart:

```bash
docker compose exec warehouse psql -U analytics -d hotel -c "select * from analytics_dev.mart_power_bi_hotel_daily order by booking_date, hotel_id;"
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

## Stop

```bash
docker compose down
```

Remove local database volumes too:

```bash
docker compose down -v
```
