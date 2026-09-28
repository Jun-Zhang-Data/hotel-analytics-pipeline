{{ config(materialized='table') }}

select
    daily.booking_date,
    daily.hotel_id,
    hotels.hotel_name,
    hotels.city,
    daily.total_bookings,
    daily.cancelled_bookings,
    daily.total_bookings - daily.cancelled_bookings as active_bookings,
    daily.total_revenue,
    round(daily.cancelled_bookings::numeric / nullif(daily.total_bookings, 0), 4) as cancellation_rate,
    round(daily.total_revenue::numeric / nullif(daily.total_bookings, 0), 2) as revenue_per_booking
from {{ ref('mart_hotel_daily') }} as daily
left join {{ ref('dim_hotels') }} as hotels
    on daily.hotel_id = hotels.hotel_id
