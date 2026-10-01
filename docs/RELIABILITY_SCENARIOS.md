# Reliability Scenario Evidence

This document maps production-reliability risks to the concrete mechanisms and automated evidence implemented in this repository. It is intentionally limited to behavior that is executable in the local portfolio environment.

## Scenario matrix

| Scenario | Production risk | Implemented mechanism | Automated evidence | Recovery expectation |
| --- | --- | --- | --- | --- |
| Duplicate source delivery | retries or upstream redelivery create duplicate raw/trusted records | deterministic `ingestion_id`, raw primary key, `ON CONFLICT DO NOTHING`, latest-version trusted logic | CI loads the same fixture twice and asserts the second run inserts zero rows | rerun safely without deleting prior successful data |
| Breaking source schema change | renamed/missing/incompatible fields corrupt ingestion or downstream models | executable source contract gate before ingestion | CI removes a required booking column, proves validation fails, restores the source, then proves validation succeeds | coordinate source/consumer change or restore compatible input before ingestion |
| Late-arriving booking update | a newer business event arrives after the normal processing window | raw version preservation plus changed-key incremental processing | CI appends a newer `B001` version, performs bounded reprocessing, and verifies two raw versions but one latest trusted row | rerun the affected date range; latest valid source version becomes trusted state |
| Historical correction | a past business record must be corrected without full destructive reload | bounded backfill plus idempotent versioned raw ingestion | CI appends a corrected `B003` version, reprocesses the affected historical date, and verifies the corrected trusted value with one trusted booking row | reprocess only the affected range and refresh affected downstream state |
| Mapping-quality failure | new source code enters without governed canonical mapping | structured DQ exception and trusted-data gating | existing UAT/DQ tests verify unmapped records are quarantined and mapping coverage is measurable | correct governed mapping data and rebuild the affected data |
| Bad-data spike / health degradation | pipeline technically succeeds while output quality becomes unacceptable | operational health thresholds for freshness, DQ pass rate, mapping coverage, volume change, and failed ingestions | CI executes the health checker with deterministic fixture thresholds | investigate the failing metric; blocking severity exits non-zero so orchestration does not report a healthy run |

## CI scenario sequence

The GitHub Actions workflow executes reliability evidence in a deliberate order:

1. initialize a clean PostgreSQL warehouse;
2. generate deterministic source fixtures and validate their contracts;
3. prove a breaking contract is blocked and recoverable;
4. load the fixture and prove an identical rerun inserts zero duplicates;
5. build and test the baseline dbt state;
6. append a late-arriving booking update, bounded-reprocess it, rebuild dbt, and assert changed-key behavior;
7. append a historical correction, bounded-reprocess it, rebuild dbt, and assert corrected trusted state;
8. prove incremental outputs match a subsequent full refresh;
9. run operational health checks.

## Key invariants

The scenarios are designed around a small set of invariants:

- repeated delivery of the same source version does not increase raw row counts;
- multiple legitimate source versions may exist in raw history for the same business key;
- trusted booking grain remains one row per `booking_id`;
- the trusted row resolves to the latest valid source state after reprocessing;
- bounded historical reprocessing does not require truncating trusted or raw schemas;
- unaffected booking keys are not unnecessarily reprocessed by the changed-key incremental path;
- incremental outputs remain equivalent to full-refresh outputs for the deterministic fixture;
- deterministic contract failures are blocked before ingestion rather than retried blindly;
- business/DQ exceptions remain separate from technical execution failures.

## Local reproduction

Generate and load the baseline fixture first:

```bash
python scripts/generate_data.py
python scripts/validate_source_contracts.py
python scripts/load_raw.py --run-id local-baseline
cd dbt_hotel && dbt build --profiles-dir . --target dev && cd ..
```

Late-arriving update:

```bash
python scripts/reliability_scenarios.py append-late-arrival
python scripts/load_raw.py --dataset bookings --start-date 2026-09-01 --end-date 2026-09-01 --run-id ci-late-arrival
cd dbt_hotel && dbt build --profiles-dir . --target dev && cd ..
python scripts/reliability_scenarios.py assert-late-arrival
```

Historical correction:

```bash
python scripts/reliability_scenarios.py append-historical-correction
python scripts/load_raw.py --dataset bookings --start-date 2026-09-01 --end-date 2026-09-01 --run-id ci-historical-correction
cd dbt_hotel && dbt build --profiles-dir . --target dev && cd ..
python scripts/reliability_scenarios.py assert-historical-correction
```

The assertion helper intentionally expects the CI run IDs for the automated evidence path. For ad-hoc manual runs, inspect `ops.ingestion_runs`, `raw.bookings`, `int_booking_current_state`, and `fct_bookings` directly or use the same CI run IDs in a disposable local environment.

## Scope boundary

These scenarios demonstrate production engineering thinking in a local, deterministic environment. They do not claim distributed exactly-once processing, cross-region disaster recovery, enterprise alert routing, or zero-downtime cloud deployment. The evidence is specifically about predictable behavior under duplicate delivery, schema changes, late arrivals, historical correction, DQ exceptions, incremental/full-refresh parity, and health degradation.
