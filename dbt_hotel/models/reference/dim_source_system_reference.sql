select
    trim(source_system_code) as source_system_code,
    trim(source_system_name) as source_system_name,
    trim(system_type) as system_type,
    upper(trim(status)) as status
from {{ ref('ref_source_systems') }}
