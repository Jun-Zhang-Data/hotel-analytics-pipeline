select
    booking_id,
    total_payment
from {{ ref('int_bookings_enriched') }}
where total_payment < 0
