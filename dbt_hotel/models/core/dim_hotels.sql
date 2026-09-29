select
    hotel_id,
    hotel_name,
    city
from {{ ref('dim_hotel_master') }}
