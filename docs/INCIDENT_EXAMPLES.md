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

## Incident 4 — Late-arriving booking update

**Symptom:** an existing booking receives a newer source version after the normal processing window; the trusted model still shows the older business state until the update is ingested and transformed.

**Investigation:** compare all raw versions for the booking by `source_updated_at`, then inspect the incremental current-state model and trusted fact. The raw layer should preserve both versions while the current-state model should select only the newest valid version.

**Root cause:** the operational source delivered a legitimate update after the original booking had already been processed.

**Recovery:** run a bounded backfill for the affected booking-date range, then rebuild dbt. The deterministic ingestion key preserves the new source version without duplicating the earlier one, and changed-key processing updates the affected booking only.

**Prevention/evidence:** CI appends a later `B001` version, performs a date-bounded backfill, rebuilds dbt, and asserts two raw versions but one trusted row with the later status.

## Incident 5 — Historical correction

**Symptom:** a historical booking attribute is corrected after downstream marts have already been produced.

**Investigation:** identify the affected business key and date range, compare source versions, and confirm which downstream facts/marts consume the corrected field.

**Root cause:** the source system corrected previously supplied historical data rather than emitting a new business entity.

**Recovery:** append the corrected source version, run the documented historical date-range backfill, and rebuild dbt. Raw history remains intact while changed-key processing refreshes the affected trusted state and impacted mart partition.

**Prevention/evidence:** CI applies a later `B003` correction, processes only the historical booking-date range, and asserts that the trusted `check_out_date` changes without creating a second trusted booking.
