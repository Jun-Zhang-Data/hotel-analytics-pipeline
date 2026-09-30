select
    booking_id,
    sum(payment_amount) as total_payment,
    max(ingested_at) as latest_payment_ingested_at
from {{ ref('stg_payments') }}
group by booking_id
