select
    booking_id,
    upper(trim(source_system_code)) as source_system_code,
    trim(source_hotel_code) as source_hotel_code,
    guest_id,
    cast(booking_date as date) as booking_date,
    cast(check_in_date as date) as check_in_date,
    cast(check_out_date as date) as check_out_date,
    upper(trim(status)) as booking_status,
    cast(source_updated_at as timestamp) as source_updated_at,
    cast(ingested_at as timestamp) as ingested_at
from {{ source('raw', 'bookings') }}
