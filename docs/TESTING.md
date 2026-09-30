# Testing Strategy

The repository uses layered tests because no single test type proves production reliability.

## Static checks

GitHub Actions runs `ruff check` over Python orchestration/ingestion code and compiles Python modules with `compileall`. These checks catch style defects, unused imports, syntax errors, and similar failures before integration work starts.

## Source-contract tests

`scripts/validate_source_contracts.py` validates required columns, declared types, and configured allowed values before ingestion. Missing/renamed required fields and incompatible types are blocking.

## Ingestion/recovery tests

CI initializes a fresh PostgreSQL warehouse, loads the deterministic fixture, loads it a second time, and asserts that the second run inserts zero rows. This is the automated idempotency proof for duplicate source delivery/retry behavior.

Backfill behavior is implemented through `--start-date`/`--end-date`; manual validation should confirm only candidate rows inside the requested range are processed and that reprocessing the same range does not increase raw row counts.

## dbt tests

`dbt build` executes seeds, transformations, generic schema tests, singular business-rule tests, DQ tests, and UAT tests together. Existing acceptance tests cover unmapped hotels, missing guest IDs, invalid stay dates, valid records reaching trusted output, and expected DQ behavior.

## Operational-health tests

CI exercises `scripts/check_operational_health.py` using thresholds adjusted for the deterministic historical fixture. Runtime defaults remain stricter. The health script covers freshness, DQ pass rate, mapping coverage, recent ingestion failures, and run-to-run volume change.

## Deliberately broken changes

To prove CI controls work, create a temporary branch that introduces one of these defects and capture the failed Actions run before reverting it:

- remove a required booking column from the generated fixture -> contract gate must fail;
- change a Python file to contain a syntax error -> compile step must fail;
- alter a dbt business rule so an existing UAT expectation is violated -> `dbt build` must fail.

Do not merge the broken change. The evidence is the failed workflow run plus the subsequent clean run after correction.

## Test responsibility split

Static checks validate code shape. Contract tests validate source compatibility. Ingestion tests validate deterministic loading/retry behavior. dbt tests validate transformations and business rules. UAT validates user-facing acceptance behavior. Operational health checks validate whether successful execution still produced data that is fresh and within defined quality/volume thresholds.
