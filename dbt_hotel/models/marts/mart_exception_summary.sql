{{ config(materialized='table') }}

select
    cast(detected_at as date) as detected_date,
    source_system_code,
    rule_id,
    quality_dimension,
    exception_status,
    count(*) as exception_count
from {{ ref('mart_exception_register') }}
group by
    cast(detected_at as date),
    source_system_code,
    rule_id,
    quality_dimension,
    exception_status
