# Incremental Processing

The pipeline uses changed-business-key incremental processing rather than a simple `source_updated_at > max(source_updated_at)` filter. The goal is to reduce downstream recomputation while preserving correctness for late-arriving data, payment changes, historical corrections, and targeted backfills.

## Processing model

```text
append-only raw booking/payment versions
        ↓
per-model ingestion watermarks
        ↓
detect changed booking_id values
        ↓
incrementally replace affected booking current state
        ↓
trusted fct_bookings projection
        ↓
rebuild affected booking_date + hotel_id mart partitions
```

Raw ingestion remains append-only and idempotent. A new source version is inserted only when its deterministic `ingestion_id` has not already been seen.

## Watermarks

`ops.incremental_model_watermarks` stores one watermark per model and raw source. The watermark is based on warehouse `ingested_at`, not business event time. This is deliberate: a historical correction may have an old `booking_date` or `source_updated_at` but is still new to the warehouse and therefore must be processed.

The current incremental models maintain independent watermarks for `bookings` and `payments` so a new payment can refresh a booking even when the booking source row itself did not change.

## Changed booking keys

`changed_booking_keys()` unions booking IDs from raw booking and payment rows whose `ingested_at` is newer than the requesting model's persisted watermark. This makes the increment unit the business key rather than an arbitrary time partition.

`int_booking_current_state` uses `booking_id` as its dbt `unique_key` and `delete+insert` strategy. On an incremental run it recomputes only changed booking IDs while leaving unaffected current-state rows untouched.

## Trusted-data behavior

The current-state model retains mapping, completeness, and stay-date validity outcomes. `fct_bookings` is a view over rows whose `is_trusted` flag is true. A changed booking therefore cannot enter the trusted fact merely because it was incrementally processed; it must still satisfy the same blocking DQ rules.

## Affected mart partitions

`mart_hotel_daily` is incremental at `booking_date + hotel_id` grain. For each changed booking it tracks both the current trusted partition and the previous trusted partition. Before rebuilding, those affected partitions are removed and then recomputed from the complete trusted fact.

Tracking the previous partition matters when a correction moves a booking to another date/hotel or changes a previously trusted booking into a quarantined record. Without cleaning the previous partition, stale aggregates could remain.

## Full refresh and reference-data changes

Incremental change detection currently watches raw booking and payment ingestion. A change to hotel master/reference seeds or mapping logic can affect bookings without creating a new raw booking/payment row. For those changes, run a full refresh:

```bash
dbt build --full-refresh --profiles-dir . --target dev
```

CI compares logical hashes of the incremental fact/mart outputs with a subsequent full refresh so the two execution paths must converge to the same business result.

## Recovery semantics

Raw history is the recovery boundary. If downstream transformation fails, successful raw ingestion remains available. After the fault is corrected, rerunning dbt processes keys newer than the persisted model watermarks. A full refresh remains available when model semantics, mapping/reference data, or persisted incremental state require complete recomputation.

## Scope

This implementation demonstrates warehouse incremental-processing semantics locally. It is not a streaming CDC platform and does not claim exactly-once distributed delivery. The important properties demonstrated here are deterministic raw ingestion, persisted processing state, changed-key recomputation, late/historical correction handling, partition-aware mart refresh, and full-refresh parity.
