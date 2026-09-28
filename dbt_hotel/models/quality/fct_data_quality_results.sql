{{ config(materialized='table') }}

with mapping_checks as (
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
),

guest_completeness_checks as (
    select
        booking_date as check_date,
        source_system_code,
        'DQ_COMP_GUEST_001' as rule_id,
        'Booking guest_id must be present' as rule_name,
        'COMPLETENESS' as quality_dimension,
        count(*) as records_checked,
        sum(case when guest_id is not null then 1 else 0 end) as records_passed,
        sum(case when guest_id is null then 1 else 0 end) as records_failed
    from {{ ref('int_bookings_mapped') }}
    where is_hotel_mapped = true
    group by booking_date, source_system_code
),

stay_date_validity_checks as (
    select
        booking_date as check_date,
        source_system_code,
        'DQ_VALID_STAY_001' as rule_id,
        'Booking check-out date must not be before check-in date' as rule_name,
        'VALIDITY' as quality_dimension,
        count(*) as records_checked,
        sum(case when check_out_date >= check_in_date then 1 else 0 end) as records_passed,
        sum(case when check_out_date < check_in_date then 1 else 0 end) as records_failed
    from {{ ref('int_bookings_mapped') }}
    where is_hotel_mapped = true
    group by booking_date, source_system_code
),

all_checks as (
    select * from mapping_checks
    union all
    select * from guest_completeness_checks
    union all
    select * from stay_date_validity_checks
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
    case
        when quality_dimension = 'MAPPING_COVERAGE'
        then round(records_passed::numeric / nullif(records_checked, 0), 4)
        else null
    end as mapping_coverage_rate
from all_checks
