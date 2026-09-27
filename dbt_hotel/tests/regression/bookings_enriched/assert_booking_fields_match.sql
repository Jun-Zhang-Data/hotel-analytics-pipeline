with current_model as (
    select *
    from {{ ref('int_bookings_enriched') }}
),

refactored_model as (
    select *
    from {{ ref('int_bookings_enriched_refactored') }}
)

select
    current_model.booking_id
from current_model
inner join refactored_model
    on current_model.booking_id = refactored_model.booking_id
where current_model.hotel_id is distinct from refactored_model.hotel_id
   or current_model.hotel_name is distinct from refactored_model.hotel_name
   or current_model.city is distinct from refactored_model.city
   or current_model.guest_id is distinct from refactored_model.guest_id
   or current_model.booking_date is distinct from refactored_model.booking_date
   or current_model.check_in_date is distinct from refactored_model.check_in_date
   or current_model.check_out_date is distinct from refactored_model.check_out_date
   or current_model.booking_status is distinct from refactored_model.booking_status
   or current_model.total_payment is distinct from refactored_model.total_payment
   or current_model.booking_lead_days is distinct from refactored_model.booking_lead_days
