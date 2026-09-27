with bookings as (
    select
        booking_id,
        hotel_id,
        guest_id,
        booking_date,
        check_in_date,
        check_out_date,
        booking_status
    from {{ ref('int_bookings_latest') }}
),

hotels as (
    select
        hotel_id,
        hotel_name,
        city
    from {{ ref('stg_hotels') }}
),

payments as (
    select
        booking_id,
        total_payment
    from {{ ref('int_payments_by_booking') }}
)

select
    bookings.booking_id,
    bookings.hotel_id,
    hotels.hotel_name,
    hotels.city,
    bookings.guest_id,
    bookings.booking_date,
    bookings.check_in_date,
    bookings.check_out_date,
    bookings.booking_status,
    coalesce(payments.total_payment, 0) as total_payment,
    bookings.check_in_date - bookings.booking_date as booking_lead_days
from bookings
left join hotels
    on bookings.hotel_id = hotels.hotel_id
left join payments
    on bookings.booking_id = payments.booking_id
