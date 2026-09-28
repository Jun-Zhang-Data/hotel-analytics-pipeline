select *
from {{ ref('int_bookings_mapped') }}
where is_hotel_mapped = true
  and guest_id is not null
  and check_out_date >= check_in_date
