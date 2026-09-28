select
    source_system_code,
    source_hotel_code,
    count(*) as active_mapping_count
from {{ ref('map_hotel_source_to_canonical') }}
where mapping_status = 'ACTIVE'
group by source_system_code, source_hotel_code
having count(*) > 1
