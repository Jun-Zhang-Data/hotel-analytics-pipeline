with current_model as (
    select
        count(*) as row_count,
        count(distinct booking_id) as booking_count,
        sum(total_payment) as total_payment,
        sum(booking_lead_days) as total_booking_lead_days
    from {{ ref('int_bookings_enriched') }}
),

refactored_model as (
    select
        count(*) as row_count,
        count(distinct booking_id) as booking_count,
        sum(total_payment) as total_payment,
        sum(booking_lead_days) as total_booking_lead_days
    from {{ ref('int_bookings_enriched_refactored') }}
)

select
    current_model.row_count as current_row_count,
    refactored_model.row_count as refactored_row_count,
    current_model.booking_count as current_booking_count,
    refactored_model.booking_count as refactored_booking_count,
    current_model.total_payment as current_total_payment,
    refactored_model.total_payment as refactored_total_payment,
    current_model.total_booking_lead_days as current_total_booking_lead_days,
    refactored_model.total_booking_lead_days as refactored_total_booking_lead_days
from current_model
cross join refactored_model
where current_model.row_count is distinct from refactored_model.row_count
   or current_model.booking_count is distinct from refactored_model.booking_count
   or current_model.total_payment is distinct from refactored_model.total_payment
   or current_model.total_booking_lead_days is distinct from refactored_model.total_booking_lead_days
