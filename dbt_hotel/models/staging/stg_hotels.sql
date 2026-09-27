select
    hotel_id,
    trim(hotel_name) as hotel_name,
    trim(city) as city,
    cast(source_updated_at as timestamp) as source_updated_at,
    cast(ingested_at as timestamp) as ingested_at
from {{ source('raw', 'hotels') }}
