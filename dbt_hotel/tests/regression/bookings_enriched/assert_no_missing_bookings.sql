with current_model as (
    select booking_id
    from {{ ref('int_bookings_enriched') }}
),

refactored_model as (
    select booking_id
    from {{ ref('int_bookings_enriched_refactored') }}
)

select
    current_model.booking_id
from current_model
left join refactored_model
    on current_model.booking_id = refactored_model.booking_id
where refactored_model.booking_id is null
