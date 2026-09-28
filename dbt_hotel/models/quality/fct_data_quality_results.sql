{{ config(materialized='table') }}

with booking_mapping_checks as (
    select
        booking_date as check_date,
        source_system_code,
        'DQ_MAP_HOTEL_001' as rule_id,
        'Booking hotel code must map to an active canonical hotel' as rule_name,
        'MAPPING_COVERAGE' as quality_dimension,
        count(*) as records_checked,
        sum(case when is_hotel_mapped then 1 else 0 end) as records_passed,
        sum(case when not is_hotel_mapped then 1 else 0 end) as records_failed
    from {{ ref('int_bookings_mapped') }}
    group by booking_date, source_system_code
)

select
    check_date,
    source_system_code,
    rule_id,
    rule_name,
    quality_dimension,
    records_checked,
    records_passed,
    records_failed,
    round(records_passed::numeric / nullif(records_checked, 0), 4) as pass_rate,
    round(records_passed::numeric / nullif(records_checked, 0), 4) as mapping_coverage_rate
from booking_mapping_checks
