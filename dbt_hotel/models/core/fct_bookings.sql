{{ config(materialized='view') }}

select
    booking_id,
    hotel_id,
    guest_id,
    booking_date,
    check_in_date,
    check_out_date,
    booking_status,
    total_payment as revenue,
    booking_lead_days
from {{ ref('int_booking_current_state') }}
where is_trusted = true
