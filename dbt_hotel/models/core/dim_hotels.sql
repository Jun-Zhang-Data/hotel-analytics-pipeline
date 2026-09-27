select
    hotel_id,
    hotel_name,
    city
from {{ ref('stg_hotels') }}
