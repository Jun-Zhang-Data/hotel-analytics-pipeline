# Master and Reference Data — Version 2.0 Foundation

## Purpose

This layer introduces governed hotel master data, source-system reference data, and explicit source-to-canonical hotel mappings without replacing the existing PostgreSQL/dbt/Airflow architecture.

## Business problem

Operational systems can use different identifiers for the same hotel. Analytics should not depend directly on those source-specific codes because they can differ by system, change over time, or become inactive.

Example:

| Source system | Source hotel code | Canonical hotel_id |
| --- | --- | --- |
| PMS_A | STO01 | H001 |
| PMS_B | SE-STH | H001 |

Both source records represent the same governed hotel entity: `H001`.

## Controlled datasets

### `master_hotels`

Defines one canonical record per hotel with governed attributes such as name, city, country, status, and effective dates.

### `ref_source_systems`

Defines the source systems allowed to participate in onboarding and mapping. A source system can be active or inactive.

### `map_hotel_source_codes`

Maps a `(source_system_code, source_hotel_code)` pair to a canonical `hotel_id`. Mapping status and effective dates support lifecycle control without deleting historical mappings.

## dbt governed models

- `dim_hotel_master` — standardized canonical hotel master.
- `dim_source_system_reference` — standardized source-system reference.
- `map_hotel_source_to_canonical` — standardized source-to-canonical cross-reference.

## Validation controls

The models validate:

- canonical hotel IDs are non-null and unique;
- source-system codes are non-null and unique;
- mapping source systems exist in the controlled source-system reference;
- mapping hotel IDs exist in the canonical hotel master;
- statuses use controlled values;
- a source-system hotel code cannot have more than one active mapping.

## Current scope boundary

This increment establishes the controlled master/reference layer only. Existing operational booking models are not yet remapped through this cross-reference, and unmapped operational records are not yet materialized into exception tables. Those are subsequent Version 2.0 increments.
