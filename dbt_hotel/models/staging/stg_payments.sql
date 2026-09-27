select
    payment_id,
    booking_id,
    cast(amount as numeric) as payment_amount,
    upper(trim(currency)) as currency,
    cast(source_updated_at as timestamp) as source_updated_at,
    cast(ingested_at as timestamp) as ingested_at
from {{ source('raw', 'payments') }}
