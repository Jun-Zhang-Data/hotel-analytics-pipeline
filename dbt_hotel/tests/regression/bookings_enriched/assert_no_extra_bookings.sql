with current_model as (
    select booking_id
    from {{ ref('int_bookings_enriched') }}
),

refactored_model as (
    select booking_id
    from {{ ref('int_bookings_enriched_refactored') }}
)

select
    refactored_model.booking_id
from refactored_model
left join current_model
    on refactored_model.booking_id = current_model.booking_id
where current_model.booking_id is null
