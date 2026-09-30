{{ config(materialized='table') }}

select
    md5(booking_id || '|DQ_VALID_STAY_001') as exception_id,
    current_timestamp as detected_at,
    booking_id as record_key,
    source_system_code,
    'BOOKING' as entity,
    cast(check_out_date as text) as invalid_value,
    'DQ_VALID_STAY_001' as rule_id,
    'Booking check-out date must not be before check-in date' as rule_name,
    'VALIDITY' as quality_dimension,
    'BLOCKING' as severity,
    'booking-data' as responsible_domain,
    'check_out_date' as field_name,
    'check_out_date is before check_in_date' as failure_reason,
    'OPEN' as exception_status
from {{ ref('int_bookings_mapped') }}
where is_hotel_mapped = true
  and check_out_date < check_in_date
