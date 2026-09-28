# Hotel Analytics Pipeline 2.0 Architecture

## Overview

The pipeline is a local, containerized analytics platform that demonstrates governed source onboarding, canonicalization, data-quality controls, structured exceptions, trusted analytical outputs, and reporting-ready marts.

## Logical flow

```text
CSV sources
  ↓
Python ingestion
  ↓
PostgreSQL raw
  ↓
dbt staging
  ↓
Master / reference standardization
  ↓
Validation and source-to-canonical mapping
  ├─ failed records → structured exception tables
  └─ passed records → trusted intermediate layer
  ↓
Core facts and dimensions
  ↓
Operational marts + DQ marts
  ↓
Power BI-ready reporting models
```

## Layer responsibilities

### Raw

Purpose: preserve source data and ingestion metadata.

Key characteristics:
- source-file traceability
- ingestion IDs
- idempotent loading
- source-native booking hotel codes

### Staging

Purpose: normalize types and source representations without introducing business-domain canonical IDs.

Examples:
- standardized source-system codes
- source hotel codes
- booking status normalization
- date/timestamp casting

### Master and reference

Purpose: separate canonical entities, governed reference values, and source-to-standard mappings.

Models:
- `dim_hotel_master`
- `dim_source_system_reference`
- `map_hotel_source_to_canonical`

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

### Marts

Operational:
- `mart_hotel_daily`
- `mart_power_bi_hotel_daily`

Data quality:
- `mart_dq_daily`
- `mart_dq_by_source`
- `mart_exception_summary`
- `mart_power_bi_dq_rule_daily`

## Orchestration

Airflow DAG flow:

```text
generate_source_data
→ ingest_raw
→ dbt_build_prod
```

## CI validation

GitHub Actions starts PostgreSQL, initializes the warehouse, generates and loads sample data, runs `dbt debug`, then runs `dbt build` so transformations, generic tests, singular business-rule tests, DQ tests, and UAT tests execute together.

## Governance evidence in the repository

The implementation includes:
- explicit canonical hotel master data
- governed source-system reference values
- source-to-canonical mappings with lifecycle status/effective dates
- relationship and uniqueness controls
- documented DQ rules
- source-to-target mapping
- automated UAT evidence
- structured exception outputs

## Scope boundary

The repository demonstrates these patterns locally. It does not implement enterprise MDM software, cloud production deployment, Power BI Service administration, or a full human exception-remediation workflow.
