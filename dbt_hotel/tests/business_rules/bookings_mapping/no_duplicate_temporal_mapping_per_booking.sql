select
    booking_id,
    count(*) as mapping_matches
from {{ ref('int_bookings_mapped') }}
group by booking_id
having count(*) > 1
