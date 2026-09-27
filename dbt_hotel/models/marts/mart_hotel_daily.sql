select
    booking_date,
    hotel_id,
    count(*) as total_bookings,
    sum(case when booking_status = 'CANCELLED' then 1 else 0 end) as cancelled_bookings,
    sum(revenue) as total_revenue
from {{ ref('fct_bookings') }}
group by booking_date, hotel_id
