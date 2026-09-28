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
- Reporting outputs: fct_data_quality_results, mart_dq_daily, mart_dq_by_source, mart_exception_summary

Additional completeness, validity, uniqueness and referential-integrity KPI rules will be added only when their operational result models are implemented.
