# UAT Test Cases

These acceptance criteria cover only functionality already implemented in the repository.

| UAT ID | Given | When | Then / Expected Result | Automated Evidence | Actual Result | Status |
|---|---|---|---|---|---|---|
| UAT-001 | Booking B004 uses source system PMS_A and source hotel code UNKNOWN99 with no active mapping | The pipeline resolves source hotel codes | B004 is written once to dq_unmapped_hotel_bookings and is excluded from fct_bookings | dbt_hotel/tests/uat/assert_uat_unmapped_booking_quarantined.sql | CI run 15 passed | PASS |
| UAT-002 | Booking B005 has a valid hotel mapping but guest_id is null | Completeness validation runs | B005 is written once to dq_missing_guest_id and is excluded from fct_bookings | dbt_hotel/tests/uat/assert_uat_missing_guest_quarantined.sql | CI run 15 passed after ingestion normalized pandas missing values to SQL NULL | PASS |
| UAT-003 | Booking B006 has a valid hotel mapping but check_out_date is before check_in_date | Validity validation runs | B006 is written once to dq_invalid_stay_dates and is excluded from fct_bookings | dbt_hotel/tests/uat/assert_uat_invalid_stay_quarantined.sql | CI run 15 passed | PASS |
| UAT-004 | B001, B002 and B003 satisfy implemented mapping, completeness and stay-date rules | Trusted downstream models build | All three bookings are present in fct_bookings | dbt_hotel/tests/uat/assert_uat_valid_bookings_reach_trusted_output.sql | CI run 15 passed | PASS |
| UAT-005 | Six sample bookings are checked and only B004 lacks a valid hotel mapping | DQ KPI aggregation runs | DQ_MAP_HOTEL_001 reports 6 checked, 5 passed, 1 failed and mapping coverage 0.8333 | dbt_hotel/tests/uat/assert_uat_mapping_coverage.sql | CI run 15 passed | PASS |
| UAT-006 | Implemented mapping, completeness and validity rules generate structured failures | Exception summary mart builds | Exception summary contains rule-level counts sourced from all three implemented exception models | mart_exception_summary.sql plus dbt build | CI run 15 dbt build passed | PASS |

## Acceptance approach

A UAT case is marked PASS only after its linked automated dbt test or model build succeeds in CI against the committed sample data. The document does not treat planned rules as accepted functionality.
