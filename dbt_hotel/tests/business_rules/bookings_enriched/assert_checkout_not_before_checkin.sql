select
    booking_id,
    check_in_date,
    check_out_date
from {{ ref('int_bookings_enriched') }}
where check_out_date < check_in_date
