# ADR 002 — Deterministic idempotent raw ingestion

## Status
Accepted

## Context
Retries, duplicate source delivery, and manual backfills must not duplicate trusted business records. Raw ingestion is the first place to make repeated processing safe.

## Decision
Derive `ingestion_id` deterministically from the dataset business key plus `source_updated_at`, enforce it as the raw-table primary key, and insert with conflict protection. Record each ingestion attempt in `ops.ingestion_runs` with candidate, inserted, duplicate, time-range, and status metadata.

## Alternatives considered
A random UUID per load would preserve every delivery but would not prevent duplicate reprocessing. Deleting/reloading whole raw tables would make retries destructive and would lose source-delivery history. Database `MERGE`/upsert by business key alone would overwrite source versions and blur late-arriving updates.

## Consequences
The same source version can be delivered repeatedly without creating duplicate raw rows. A changed `source_updated_at` is treated as a new source version. This design depends on the source timestamp meaningfully identifying revisions; a real source with weaker semantics would require a different source-version key.
