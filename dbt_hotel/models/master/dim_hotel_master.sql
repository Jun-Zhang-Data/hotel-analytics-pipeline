select
    trim(hotel_id) as hotel_id,
    trim(hotel_name) as hotel_name,
    trim(city) as city,
    upper(trim(country_code)) as country_code,
    upper(trim(status)) as status,
    cast(effective_from as date) as effective_from,
    cast(nullif(cast(effective_to as text), '') as date) as effective_to
from {{ ref('master_hotels') }}
