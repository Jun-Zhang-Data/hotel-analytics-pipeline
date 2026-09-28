{{ config(materialized='table') }}

select
    md5(booking_id || '|DQ_COMP_GUEST_001') as exception_id,
    current_timestamp as detected_at,
    booking_id as record_key,
    source_system_code,
    guest_id as invalid_value,
    'DQ_COMP_GUEST_001' as rule_id,
    'Booking guest_id must be present' as rule_name,
    'COMPLETENESS' as quality_dimension,
    'guest_id' as field_name,
    'Required guest_id is missing' as failure_reason,
    'OPEN' as exception_status
from {{ ref('int_bookings_mapped') }}
where is_hotel_mapped = true
  and guest_id is null
