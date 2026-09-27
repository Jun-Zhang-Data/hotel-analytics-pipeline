select
    booking_id,
    booking_date,
    check_in_date
from {{ ref('int_bookings_enriched') }}
where booking_date > check_in_date
