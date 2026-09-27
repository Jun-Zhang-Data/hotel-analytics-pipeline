select
    b.*
from {{ ref('stg_bookings') }} b
left join {{ ref('stg_hotels') }} h
    on b.hotel_id = h.hotel_id
where
    h.hotel_id is null
    or b.booking_status not in ('CONFIRMED', 'CANCELLED')
