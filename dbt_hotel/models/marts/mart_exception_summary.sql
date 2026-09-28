{{ config(materialized='table') }}

with all_exceptions as (
    select detected_at, source_system_code, rule_id, quality_dimension, exception_status
    from {{ ref('dq_unmapped_hotel_bookings') }}
    union all
    select detected_at, source_system_code, rule_id, quality_dimension, exception_status
    from {{ ref('dq_missing_guest_id') }}
    union all
    select detected_at, source_system_code, rule_id, quality_dimension, exception_status
    from {{ ref('dq_invalid_stay_dates') }}
)

select
    cast(detected_at as date) as detected_date,
    source_system_code,
    rule_id,
    quality_dimension,
    exception_status,
    count(*) as exception_count
from all_exceptions
group by
    cast(detected_at as date),
    source_system_code,
    rule_id,
    quality_dimension,
    exception_status
