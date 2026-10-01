# Portfolio Evidence and Safe Claims

This file lists claims that are directly supported by implemented repository functionality.

## Safe project summary

Built a containerized hotel analytics pipeline using PostgreSQL, dbt, Apache Airflow, Docker, Python, and GitHub Actions, with deterministic idempotent ingestion, controlled historical backfills, executable source contracts, governed master/reference data, structured data-quality exceptions, lifecycle-aware exception reporting, operational health checks, automated reliability scenarios, UAT tests, and Power BI-ready reporting models.

## Safe external summary bullets

- Built a layered PostgreSQL/dbt analytics pipeline for hotel booking and payment data, orchestrated with Apache Airflow and validated through GitHub Actions CI.
- Implemented deterministic raw ingestion with duplicate protection, run-level operational metadata, and bounded date-range backfills for repeatable recovery and historical reprocessing.
- Added executable source contracts that fail fast on missing or incompatible required fields before ingestion.
- Implemented canonical hotel master data, source-system reference data, and source-to-canonical hotel mappings with relationship, uniqueness, lifecycle-status, and effective-date controls.
- Added mapping, completeness, and validity data-quality rules with blocking trusted-data gates and structured exception outputs.
- Added append-only exception lifecycle actions (`ACKNOWLEDGED`, `RESOLVED`, `REPROCESSED`) and a lifecycle-aware exception register without mutating dbt-generated exception tables.
- Developed DQ and operational health signals for pass rate, mapping coverage, freshness, volume change, failed ingestion runs, and exception counts by date, source, rule, and lifecycle status.
- Automated reliability scenarios for duplicate delivery, breaking source contracts, late-arriving updates, historical correction, changed-key incremental processing, and incremental/full-refresh parity.
- Documented source-to-target mappings, runbook procedures, incident examples, data contracts, reliability scenarios, and architecture decisions.
- Built Power BI-ready operational and data-quality marts without claiming a Power BI Service deployment or `.pbix` artifact.

## Evidence map

| Capability | Repository evidence |
|---|---|
| Idempotent ingestion and run metadata | `scripts/load_raw.py`, `scripts/init_warehouse.sql` |
| Controlled backfill | `scripts/load_raw.py`, `airflow/dags/hotel_pipeline.py` |
| Executable source contracts | `config/data_contracts.json`, `scripts/validate_source_contracts.py` |
| Operational health gate | `scripts/check_operational_health.py` |
| Reliability scenarios | `scripts/reliability_scenarios.py`, `docs/RELIABILITY_SCENARIOS.md` |
| Changed-key incremental processing | `dbt_hotel/macros/incremental_processing.sql`, `dbt_hotel/models/intermediate/int_booking_current_state.sql` |
| Incremental mart refresh | `dbt_hotel/models/marts/mart_hotel_daily.sql` |
| Master data | `dbt_hotel/models/master/dim_hotel_master.sql` |
| Source-system reference data | `dbt_hotel/models/reference/dim_source_system_reference.sql` |
| Source-to-canonical mapping | `dbt_hotel/models/master/map_hotel_source_to_canonical.sql` |
| Active-mapping uniqueness control | `dbt_hotel/tests/business_rules/master_data/assert_unique_active_hotel_mapping.sql` |
| Mapping exception | `dbt_hotel/models/quality/exceptions/dq_unmapped_hotel_bookings.sql` |
| Completeness exception | `dbt_hotel/models/quality/exceptions/dq_missing_guest_id.sql` |
| Validity exception | `dbt_hotel/models/quality/exceptions/dq_invalid_stay_dates.sql` |
| Exception lifecycle action log | `ops.dq_exception_actions` created by `scripts/init_warehouse.sql` |
| Exception lifecycle command | `scripts/manage_dq_exception.py` |
| Lifecycle-aware exception register | `dbt_hotel/models/marts/mart_exception_register.sql` |
| DQ KPI fact | `dbt_hotel/models/quality/fct_data_quality_results.sql` |
| DQ reporting marts | `dbt_hotel/models/marts/mart_dq_daily.sql`, `mart_dq_by_source.sql`, `mart_exception_register.sql`, `mart_exception_summary.sql`, `mart_power_bi_dq_rule_daily.sql` |
| Operational BI mart | `dbt_hotel/models/marts/mart_power_bi_hotel_daily.sql` |
| Source-to-target mapping | `docs/source_to_target_mapping.csv` |
| UAT | `docs/uat_test_cases.md` and `dbt_hotel/tests/uat/` |
| Runbook | `docs/RUNBOOK.md` |
| Data contracts | `docs/DATA_CONTRACTS.md` |
| Incident evidence | `docs/INCIDENT_EXAMPLES.md`, `docs/RELIABILITY_SCENARIOS.md` |
| Architecture decisions | `docs/adr/` |
| Power BI reporting contract | `docs/power_bi_reporting_contract.md` |
| Orchestration | `airflow/dags/hotel_pipeline.py` |
| CI | `.github/workflows/dbt-ci.yml` |

## Claims to avoid

Do not claim that the repository includes:
- a Power BI `.pbix` dashboard
- Power BI Service deployment or refresh configuration
- Azure or Microsoft Fabric implementation
- enterprise MDM software
- a full human case-management interface for exception remediation
- centralized enterprise monitoring or alert routing
- distributed exactly-once processing guarantees
- a fully deployed production cloud platform

Use wording such as `Power BI-ready marts` rather than `Power BI dashboard`, `append-only exception lifecycle actions` rather than `full case-management workflow`, and `production-style local reliability controls` rather than `enterprise production deployment`.
