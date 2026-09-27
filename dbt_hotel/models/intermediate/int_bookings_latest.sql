with ranked as (
    select
        *,
        row_number() over (
            partition by booking_id
            order by source_updated_at desc, ingested_at desc
        ) as rn
    from {{ ref('stg_bookings') }}
)

select
    booking_id,
    hotel_id,
    guest_id,
    booking_date,
    check_in_date,
    check_out_date,
    booking_status,
    source_updated_at,
    ingested_at
from ranked
where rn = 1
