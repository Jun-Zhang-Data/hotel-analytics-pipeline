select
    b.*
from {{ ref('stg_bookings') }} b
inner join {{ ref('stg_hotels') }} h
    on b.hotel_id = h.hotel_id
where b.booking_status in ('CONFIRMED', 'CANCELLED')
