with exception_check as (
    select count(*) as exception_count
    from {{ ref('dq_unmapped_hotel_bookings') }}
    where record_key = 'B004'
),
trusted_check as (
    select count(*) as trusted_count
    from {{ ref('fct_bookings') }}
    where booking_id = 'B004'
)
select *
from exception_check
cross join trusted_check
where exception_count <> 1
   or trusted_count <> 0
