select
    trim(source_system_code) as source_system_code,
    trim(source_hotel_code) as source_hotel_code,
    trim(hotel_id) as hotel_id,
    upper(trim(mapping_status)) as mapping_status,
    cast(effective_from as date) as effective_from,
    cast(nullif(cast(effective_to as text), '') as date) as effective_to
from {{ ref('map_hotel_source_codes') }}
