# Hotel Analytics Pipeline 2.0 Architecture

## Overview

The pipeline is a local, containerized analytics platform that demonstrates governed source onboarding, canonicalization, data-quality controls, structured exceptions, trusted analytical outputs, reporting-ready marts, and explicit production-reliability mechanisms.

Operational booking and payment data enter through executable source-contract validation and Python ingestion into PostgreSQL raw tables. Governed hotel master data, source-system reference values, and source-to-canonical mappings are maintained separately as dbt seeds so downstream models have a clear canonical source of truth. Operational state such as ingestion runs is stored separately in the `ops` schema.

## End-to-end logical flow

```text
Operational CSV sources (bookings, payments)
  ↓
Executable source-contract validation
  ↓
Python ingestion ───────────────→ ops.ingestion_runs
  ↓
PostgreSQL raw
  ↓
dbt staging
  ↓
Validation and source-to-canonical mapping ← governed dbt seeds
                                     ├─ hotel master
                                     ├─ source-system reference
                                     └─ source-to-canonical mappings
  ├─ failed records → structured exception tables
  └─ passed records → trusted intermediate layer
  ↓
Core facts and governed dimensions
  ↓
Operational marts + DQ marts
  ↓
Operational health gate
  ↓
Power BI-ready reporting models
```

## Layer responsibilities and grain

### Raw

Purpose: preserve operational source data and ingestion metadata without applying downstream business semantics.

Grain:
- `raw.bookings`: one source booking version per deterministic `ingestion_id`
- `raw.payments`: one source payment version per deterministic `ingestion_id`

Key characteristics:
- booking and payment source-file traceability
- deterministic ingestion IDs
- idempotent loading through a primary key and `ON CONFLICT DO NOTHING`
- source-native booking hotel codes
- source update timestamps retained for freshness and latest-record logic

### Operational metadata

Purpose: record execution state independently of business data.

`ops.ingestion_runs` records one row per dataset per ingestion invocation. It stores run status, source/candidate/inserted/duplicate row counts, source timestamp range, requested backfill range, completion timestamp, and error text.

This state is used for operational troubleshooting and run-to-run volume monitoring. It does not determine business truth in trusted analytical models.

### Staging

Purpose: normalize operational source types and representations without introducing business-domain canonical IDs.

Examples:
- standardized source-system codes
- source hotel codes
- booking status normalization
- payment amount/currency normalization
- date/timestamp casting

### Master and reference

Purpose: separate canonical entities, governed reference values, and source-to-standard mappings from operational ingestion.

Seed-backed models:
- `dim_hotel_master`
- `dim_source_system_reference`
- `map_hotel_source_to_canonical`

The governed hotel master is the source of truth for the downstream `dim_hotels` dimension.

### Validation and quality

Purpose: evaluate implemented business/data-quality rules and preserve failures as analytical exception outputs.

Implemented quality dimensions:
- `MAPPING_COVERAGE`
- `COMPLETENESS`
- `VALIDITY`

Exception models:
- `dq_unmapped_hotel_bookings`
- `dq_missing_guest_id`
- `dq_invalid_stay_dates`

Exception outputs carry stable rule IDs, severity, responsible domain, detection timestamp, affected record key, and lifecycle status.

Analytical DQ results:
- `fct_data_quality_results`

### Trusted intermediate and core

Purpose: allow only records that satisfy implemented trusted-data rules into downstream analytical facts.

Key models:
- `int_bookings_mapped`
- `int_bookings_validated`
- `int_bookings_enriched`
- `fct_bookings`
- `dim_hotels`

Trusted-data gating is explicit: implemented blocking DQ failures are routed to structured exception models and excluded from `fct_bookings`.

### Marts

Operational:
- `mart_hotel_daily`
- `mart_power_bi_hotel_daily`

Data quality:
- `mart_dq_daily`
- `mart_dq_by_source`
- `mart_exception_summary`
- `mart_power_bi_dq_rule_daily`

## Source contract boundary

`config/data_contracts.json` defines the expected source interface for booking and payment files. The contract gate runs before ingestion.

Breaking conditions include:
- missing required columns
- values incompatible with declared logical types
- violations of explicitly governed allowed values

Additional columns are treated as non-breaking warnings because downstream ingestion selects its declared fields explicitly.

The contract boundary protects the ingestion/staging interface. Business-semantic failures such as an unmapped hotel code are intentionally handled later as data-quality exceptions rather than source-schema failures.

## Orchestration boundaries

Airflow DAG flow:

```text
generate_source_data
→ validate_source_contracts
→ ingest_raw
→ dbt_build_prod
→ operational_health
```

Responsibilities are intentionally separated:
- Airflow coordinates execution order, retry policy, parameters, and task failure state.
- Python owns source contract validation and raw ingestion mechanics.
- dbt owns SQL transformations, governed mappings, data-quality models, trusted-data gating, tests, and marts.
- PostgreSQL owns persisted raw, operational, analytical, and exception state.

The generated operational source files are `bookings.csv` and `payments.csv`; governed master/reference inputs are loaded by dbt as seeds during `dbt build`.

## Retry, idempotency, and backfill

Airflow retries transient tasks up to two times with a controlled delay. Deterministic validation/health gates do not retry automatically because repeating the same invalid input is unlikely to recover.

Raw ingestion is safe to rerun because the same business key and source update timestamp produce the same `ingestion_id`. Duplicate deliveries therefore do not create duplicate raw versions.

Historical reprocessing is bounded using `--start-date` and `--end-date`, exposed as Airflow run parameters. Backfill filters source rows before insertion and records the requested range in `ops.ingestion_runs`.

A full refresh remains a separate operational choice for cases where model semantics or persisted derived structures require complete rebuilding. Routine late-arriving events and targeted historical corrections should prefer bounded idempotent reprocessing.

## Operational health and observability

`scripts/check_operational_health.py` evaluates:
- booking source freshness
- aggregate DQ pass rate
- mapping coverage
- booking volume change between successful ingestion runs
- failed ingestions in the previous 24 hours

Thresholds are environment-configurable. Results are emitted as a structured JSON payload with per-check severity and an overall status. `BLOCKING` results exit non-zero so orchestration can represent the pipeline as failed rather than silently healthy.

This local implementation intentionally does not introduce a dedicated metrics platform or alert-delivery service. The health script and Airflow task provide demonstrable observability and gating semantics while keeping the portfolio architecture proportionate.

## Failure domains

### Source failure
Examples: source file unavailable, missing required column, incompatible type.

Handling: contract validation fails before ingestion; no new trusted output is produced from invalid input.

### Orchestration failure
Examples: task process crash, transient database connectivity problem.

Handling: controlled Airflow retries; task state and logs provide execution evidence.

### Ingestion failure
Examples: database write error.

Handling: transaction rollback plus `FAILED` state in `ops.ingestion_runs`; rerun is safe after the fault is resolved.

### Transformation/test failure
Examples: dbt SQL error, relationship/uniqueness/UAT failure.

Handling: `dbt build` fails and downstream health/serving steps do not proceed.

### Business/data-quality failure
Examples: unmapped hotel code, missing guest ID, invalid stay dates.

Handling: structured exception outputs and explicit trusted-data gating; DQ metrics remain queryable for investigation.

### Serving/health failure
Examples: stale source data or blocking DQ degradation.

Handling: operational-health gate exits non-zero and Airflow marks the final task failed.

## CI validation

GitHub Actions provides executable change-control evidence by:
- linting and compiling Python
- starting PostgreSQL and initializing schemas
- generating deterministic fixtures
- validating source contracts
- deliberately removing a required column and proving the contract gate fails
- restoring the source and proving validation succeeds again
- loading the same source twice and asserting the second load inserts zero records
- running `dbt debug` and `dbt build`
- running generic, singular, DQ, business-rule, and UAT tests
- exercising operational-health checks

This validates both happy-path behavior and selected failure/recovery paths before merge.

## Architecture decisions

Important decisions and trade-offs are recorded in:
- `docs/adr/001-postgres-dbt-airflow.md`
- `docs/adr/002-idempotent-raw-ingestion.md`
- `docs/adr/003-contract-gate-before-ingestion.md`

The project deliberately avoids adding infrastructure such as Kafka, Kubernetes, Terraform, or cloud services without a concrete requirement.

## Scaling beyond the local implementation

The current design is intended as production-engineering evidence rather than a claim of enterprise deployment. The same boundaries could scale by replacing individual components without rewriting the entire conceptual model—for example, managed storage/warehouse services, external schedulers, centralized metric/alert platforms, or secret managers.

The important architectural properties to preserve are deterministic ingestion identity, explicit contracts, governed canonical mappings, trusted-data gates, observable execution state, reproducible backfills, and automated change validation.

## Scope boundary

The repository demonstrates these patterns locally. It does not implement enterprise MDM software, cloud production deployment, Power BI Service administration, centralized alert delivery, production secrets management, or a full human exception-remediation workflow.
