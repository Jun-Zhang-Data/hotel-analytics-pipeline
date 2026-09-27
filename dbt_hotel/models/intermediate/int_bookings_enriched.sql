select
    b.booking_id,
    b.hotel_id,
    h.hotel_name,
    h.city,
    b.guest_id,
    b.booking_date,
    b.check_in_date,
    b.check_out_date,
    b.booking_status,
    coalesce(p.total_payment, 0) as total_payment,
    b.check_in_date - b.booking_date as booking_lead_days
from {{ ref('int_bookings_latest') }} b
left join {{ ref('stg_hotels') }} h
    on b.hotel_id = h.hotel_id
left join {{ ref('int_payments_by_booking') }} p
    on b.booking_id = p.booking_id
