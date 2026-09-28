with expected as (
    select unnest(array['B001','B002','B003']) as booking_id
),
missing_from_trusted as (
    select expected.booking_id
    from expected
    left join {{ ref('fct_bookings') }} trusted
      on expected.booking_id = trusted.booking_id
    where trusted.booking_id is null
)
select * from missing_from_trusted
