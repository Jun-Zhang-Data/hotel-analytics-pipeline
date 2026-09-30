# Testing Strategy

The repository uses layered tests because no single test type proves production reliability.

## Static checks

GitHub Actions runs `ruff check` over Python orchestration/ingestion code and compiles Python modules with `compileall`. These checks catch style defects, unused imports, syntax errors, and similar failures before integration work starts.

## Source-contract tests

`scripts/validate_source_contracts.py` validates required columns, declared types, and configured allowed values before ingestion. Missing/renamed required fields and incompatible types are blocking.

CI also proves the gate by temporarily removing `source_hotel_code`, requiring validation to fail, then restoring the source fixture and requiring validation to pass again.

## Ingestion/recovery tests

CI initializes a fresh PostgreSQL warehouse, loads the deterministic fixture, loads it a second time, and asserts that the second run inserts zero rows. This is the automated idempotency proof for duplicate source delivery/retry behavior.

Bounded backfill behavior is tested with `--start-date`/`--end-date` against booking data. The test harness appends versioned source corrections, processes only the affected historical date range, and verifies that only the new source version is inserted while existing versions are skipped as duplicates.

## Exception lifecycle persistence test

After the initial dbt build creates structured exceptions, CI selects one exception from `mart_exception_register`, records an `ACKNOWLEDGED` action through `scripts/manage_dq_exception.py`, rebuilds the entire dbt project, and verifies two invariants:

- the exception still reports `ACKNOWLEDGED` after the rebuild;
- exactly one matching append-only action exists in `ops.dq_exception_actions`.

This proves that operational disposition survives recreation of dbt-generated exception tables and remains separate from trusted-data gating.

## Late-arriving data test

`scripts/reliability_scenarios.py` appends a newer `B001` source version after the initial pipeline run. CI backfills the affected booking date, rebuilds dbt, and verifies:

- two raw versions of `B001` are preserved;
- only one `B001` row exists in the trusted fact;
- the trusted row reflects the newer source status;
- the ingestion run reports exactly one new inserted booking version.

This proves that late-arriving updates can be incorporated without destructive replacement or duplicate trusted records.

## Historical correction test

The same harness appends a corrected `B003` version with a later `source_updated_at`. CI runs a bounded backfill and verifies that raw history contains both versions while `fct_bookings` resolves to the corrected `check_out_date` with one trusted booking row.

## Partial downstream failure and recovery

`dbt_hotel/tests/reliability/assert_no_forced_failure.sql` is normally empty and passes. CI deliberately runs it with `force_reliability_failure=true`, requires dbt to return a failure, then executes a clean `dbt build` and re-verifies the trusted late-arrival and historical-correction states.

This demonstrates the recovery boundary: successful raw ingestion remains durable when a downstream transformation/test step fails, so recovery can restart from the trusted raw state rather than deleting and reloading upstream data.

## dbt tests

`dbt build` executes seeds, transformations, generic schema tests, singular business-rule tests, DQ tests, reliability tests, and UAT tests together. Existing acceptance tests cover unmapped hotels, missing guest IDs, invalid stay dates, valid records reaching trusted output, expected DQ behavior, and lifecycle-aware exception mart constraints.

## Operational-health tests

CI exercises `scripts/check_operational_health.py` using thresholds adjusted for the deterministic historical fixture. Runtime defaults remain stricter. The health script covers freshness, DQ pass rate, mapping coverage, recent ingestion failures, and run-to-run volume change.

## Deliberately broken changes

The repository contains automated negative-path evidence rather than relying only on manual demonstrations:

- a missing required source column must fail the source-contract gate;
- a forced dbt reliability test must fail downstream processing;
- both scenarios must subsequently recover and pass after the fault is removed.

Additional manual failure demonstrations can still be used for Python syntax errors or business-rule regressions, but they are not required to prove the implemented recovery paths.

## Test responsibility split

Static checks validate code shape. Contract tests validate source compatibility. Ingestion tests validate deterministic loading/retry behavior. Exception lifecycle tests validate persistence of operational disposition across dbt rebuilds. Reliability scenarios validate late data, historical corrections, and partial-failure recovery. dbt tests validate transformations and business rules. UAT validates user-facing acceptance behavior. Operational health checks validate whether successful execution still produced data that is fresh and within defined quality/volume thresholds.
