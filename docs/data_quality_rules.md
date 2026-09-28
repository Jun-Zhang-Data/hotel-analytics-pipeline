# Data Quality Rules

This catalogue records implemented data-quality controls. It only documents rules that exist in the repository.

## DQ_MAP_HOTEL_001 — Source hotel must map to an active canonical hotel

- Quality dimension: MAPPING_COVERAGE
- Scope: booking records
- Source fields: source_system_code, source_hotel_code
- Rule: each booking source hotel code must resolve through an ACTIVE source-to-canonical hotel mapping
- Pass condition: a canonical hotel_id is found
- Failure handling: the booking is excluded from trusted downstream booking output and materialized in dq_unmapped_hotel_bookings
- Exception lifecycle default: OPEN
- KPI outputs: records checked, records passed, records failed, pass rate, mapping coverage rate

## DQ_COMP_GUEST_001 — Booking guest_id must be present

- Quality dimension: COMPLETENESS
- Scope: mapped booking records
- Source field: guest_id
- Rule: each mapped booking must contain guest_id before entering trusted downstream models
- Pass condition: guest_id is not null
- Failure handling: the booking is excluded from trusted downstream output and materialized in dq_missing_guest_id
- Exception lifecycle default: OPEN
- KPI outputs: records checked, records passed, records failed, pass rate

## DQ_VALID_STAY_001 — Check-out date must not be before check-in date

- Quality dimension: VALIDITY
- Scope: mapped booking records
- Source fields: check_in_date, check_out_date
- Rule: check_out_date must be greater than or equal to check_in_date
- Pass condition: check_out_date >= check_in_date
- Failure handling: the booking is excluded from trusted downstream output and materialized in dq_invalid_stay_dates
- Exception lifecycle default: OPEN
- KPI outputs: records checked, records passed, records failed, pass rate

## Reporting outputs

Implemented rules feed fct_data_quality_results, mart_dq_daily, mart_dq_by_source and mart_exception_summary.

Mapping coverage is calculated only from the mapping rule. Overall DQ pass rate aggregates all implemented rule checks.
