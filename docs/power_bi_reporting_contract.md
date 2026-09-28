# Power BI Reporting Contract

This document describes the reporting-ready dbt outputs implemented in the repository. It does not claim that a Power BI report file or dashboard has been built.

## Reporting tables

### mart_power_bi_hotel_daily
Grain: one row per booking_date and canonical hotel_id.

Fields exposed for reporting:
- booking_date
- hotel_id
- hotel_name
- city
- total_bookings
- cancelled_bookings
- active_bookings
- total_revenue
- cancellation_rate
- revenue_per_booking

Primary use: hotel operational performance reporting.

### mart_power_bi_dq_rule_daily
Grain: one row per check_date, source_system_code and DQ rule.

Fields exposed for reporting:
- check_date
- source_system_code
- rule_id
- rule_name
- quality_dimension
- records_checked
- records_passed
- records_failed
- pass_rate
- mapping_coverage_rate

Primary use: data-quality monitoring by source, rule and quality dimension.

### mart_exception_summary
Existing exception reporting table used alongside the DQ rule mart.

Grain: detected_date, source_system_code, rule_id, quality_dimension and exception_status.

Primary use: exception-volume and lifecycle-status reporting.

## Suggested Power BI relationships

If these tables are imported into Power BI, keep the two reporting marts at their native grains. A shared calendar dimension can relate to booking_date, check_date and detected_date. Hotel slicing should use hotel_id on mart_power_bi_hotel_daily. Source-system and rule slicing should use the fields already present in mart_power_bi_dq_rule_daily and mart_exception_summary.

## Suggested measures

These are consumer-layer measure definitions, not implemented DAX files in this repository:
- Total Bookings = SUM(total_bookings)
- Cancelled Bookings = SUM(cancelled_bookings)
- Total Revenue = SUM(total_revenue)
- Cancellation Rate = DIVIDE([Cancelled Bookings], [Total Bookings])
- Records Checked = SUM(records_checked)
- Records Failed = SUM(records_failed)
- DQ Pass Rate = DIVIDE(SUM(records_passed), SUM(records_checked))
- Exception Count = SUM(exception_count)

For mapping coverage, filter rule_id to DQ_MAP_HOTEL_001 or quality_dimension to MAPPING_COVERAGE before aggregating passed versus checked records.

## Scope boundary

Implemented here:
- reporting-ready operational mart
- reporting-ready DQ rule mart
- existing exception summary mart
- dbt tests for reporting outputs
- documented Power BI consumption contract

Not implemented here:
- .pbix file
- dashboard pages or visuals
- Power BI service deployment
- scheduled Power BI refresh configuration
