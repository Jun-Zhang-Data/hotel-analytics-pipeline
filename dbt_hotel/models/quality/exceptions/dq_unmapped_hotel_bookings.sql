{{ config(materialized='table') }}

select
    md5(booking_id || '|DQ_MAP_HOTEL_001') as exception_id,
    current_timestamp as detected_at,
    booking_id as record_key,
    source_system_code,
    source_hotel_code as invalid_value,
    'DQ_MAP_HOTEL_001' as rule_id,
    'Booking hotel code must map to an active canonical hotel' as rule_name,
    'MAPPING_COVERAGE' as quality_dimension,
    'source_hotel_code' as field_name,
    'No active source-to-canonical hotel mapping found' as failure_reason,
    'OPEN' as exception_status
from {{ ref('int_bookings_mapped') }}
where is_hotel_mapped = false
