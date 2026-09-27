select
    booking_id,
    sum(payment_amount) as total_payment
from {{ ref('stg_payments') }}
group by booking_id
