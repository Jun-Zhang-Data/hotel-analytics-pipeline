# Simulated Incident Examples

## Incident 1 — Duplicate source delivery

**Symptom:** the same booking/payment files are processed twice after a retry.

**Investigation:** compare consecutive `ops.ingestion_runs` rows and raw row counts. The second run should report candidate rows but zero inserted rows and corresponding `duplicate_rows`.

**Root cause:** upstream redelivery or an operator retry, not a new business event.

**Recovery:** rerun safely. Deterministic `ingestion_id` plus `ON CONFLICT DO NOTHING` prevents duplicate raw records; dbt rebuilds trusted outputs from unchanged raw state.

**Prevention/evidence:** CI performs the load twice and asserts the second run inserts zero rows.

## Incident 2 — Breaking source schema change

**Symptom:** `validate_source_contracts` fails before ingestion because a required column disappeared or became incompatible with the declared type.

**Investigation:** compare source headers/types with `config/data_contracts.json`; identify downstream staging, mapping, DQ, and mart fields that depend on the changed field.

**Root cause:** source producer changed its contract without a coordinated downstream release.

**Recovery:** do not bypass the gate. Update ingestion/dbt/tests and the contract together, or restore the upstream field. Re-run contract validation and CI before processing.

**Prevention/evidence:** source compatibility is executable and fail-fast rather than only documented.

## Incident 3 — Mapping-quality spike

**Symptom:** operational health reports low mapping coverage and `dq_unmapped_hotel_bookings` grows.

**Investigation:** group failures by `source_system_code` and `source_hotel_code`; check canonical identity and effective-date mapping rows.

**Root cause:** a new/changed source hotel code has no valid canonical mapping.

**Recovery:** verify the business identity, add or correct governed mapping data, rerun the affected date range, rebuild dbt, and confirm both exception count and mapping coverage recover.

**Prevention/evidence:** mapping failures remain visible as structured exceptions with rule ID, severity, responsible domain, and affected record key instead of silently contaminating trusted facts.
