with bookings as (
    select * from {{ ref('int_bookings_latest') }}
),
active_mappings as (
    select
        source_system_code,
        source_hotel_code,
        hotel_id
    from {{ ref('map_hotel_source_to_canonical') }}
    where mapping_status = 'ACTIVE'
)
select
    bookings.booking_id,
    bookings.source_system_code,
    bookings.source_hotel_code,
    active_mappings.hotel_id,
    case when active_mappings.hotel_id is null then false else true end as is_hotel_mapped,
    bookings.guest_id,
    bookings.booking_date,
    bookings.check_in_date,
    bookings.check_out_date,
    bookings.booking_status,
    bookings.source_updated_at,
    bookings.ingested_at
from bookings
left join active_mappings
    on bookings.source_system_code = active_mappings.source_system_code
   and bookings.source_hotel_code = active_mappings.source_hotel_code
