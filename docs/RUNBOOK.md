# Operations Runbook

This runbook covers the local production-style implementation. It is not an enterprise on-call procedure.

## Triage order

1. Identify the failed Airflow task and capture its log/error.
2. Check the latest `ops.ingestion_runs` rows for dataset status, inserted rows, duplicates, backfill range, and error message.
3. If ingestion succeeded, inspect dbt build/test output to separate transformation failure from business DQ failure.
4. Run `python scripts/check_operational_health.py` against the relevant target schema to classify current signals as OK, WARNING, or BLOCKING.
5. Recover only after the failure domain is understood; do not manually patch trusted tables.

## Airflow task failure

`generate_source_data`: verify source-generation code and filesystem access. This is a demo-source task, not a real upstream dependency.

`validate_source_contracts`: treat exit code 2 as a breaking source-schema/data-type change. Do not bypass the gate. Compare the source header/types with `config/data_contracts.json`, assess downstream impact, and change the contract only together with code/tests.

`ingest_raw`: transient database failures may be retried by Airflow. The loader is idempotent because `ingestion_id` is deterministic and raw inserts use conflict protection. Inspect `ops.ingestion_runs` before rerunning.

`dbt_build_prod`: inspect the failing model/test. A dbt test failure is not automatically an infrastructure incident; determine whether it is a model defect, an intentionally blocking DQ rule, or an invalid reference/mapping change.

`operational_health`: a BLOCKING result fails the task; WARNING is observable but does not block publication. Thresholds are environment variables documented in the script.

## Controlled backfill

CLI example:

```bash
python scripts/load_raw.py --start-date 2026-09-01 --end-date 2026-09-07
```

Airflow manual runs accept `backfill_start` and `backfill_end` parameters in `YYYY-MM-DD` format. Bookings are selected by `booking_date`; payments are selected by the date of `source_updated_at`.

After loading the range, run the dbt build for the target environment and then the operational health check. Because core/mart models are currently rebuilt as tables, dbt recomputes trusted outputs from raw state. The project therefore favors correctness and clear recovery over incremental optimization at its current scale.

## Idempotent rerun

A rerun with the same source business key and `source_updated_at` generates the same `ingestion_id`; duplicate raw rows are skipped. CI proves this by loading the deterministic fixture twice and asserting that the second run inserts zero rows.

## DQ spike

1. Inspect `fct_data_quality_results` by `check_date`, `source_system_code`, and `rule_id`.
2. Inspect the corresponding exception table for affected record keys.
3. Determine whether the spike is mapping coverage, completeness, or validity.
4. For mapping failures, inspect source-to-canonical mapping coverage and effective dates before adding/changing a mapping.
5. Do not edit trusted facts directly; resolve source/reference logic and re-run the affected range.

## Unmapped canonical entity

For `DQ_MAP_HOTEL_001`, inspect `source_system_code`, `source_hotel_code`, booking date, and active/effective mapping rows. Add a mapping only when the canonical identity is verified. Then rebuild and confirm the record exits the exception table and enters trusted outputs.

## Rollback

Application changes are rolled back through Git: revert the offending commit/PR, rerun CI, deploy the reverted code locally, and rebuild the affected data. Data corrections should be made through governed source/reference inputs or deterministic reprocessing rather than direct edits to analytical tables.

## Failure-domain guide

- Source/contract failure: source file absent or structurally incompatible.
- Orchestration failure: Airflow execution/retry/timeout issue.
- Ingestion failure: database/connectivity/load error recorded in `ops.ingestion_runs`.
- Transformation failure: dbt model compilation/execution failure.
- DQ failure: validly ingested record violates a trusted-data rule and is routed to exceptions.
- Serving/health failure: marts exist but operational thresholds indicate stale or degraded output.
