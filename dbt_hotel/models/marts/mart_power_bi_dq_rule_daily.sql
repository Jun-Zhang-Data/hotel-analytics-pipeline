{{ config(materialized='table') }}

select
    check_date,
    source_system_code,
    rule_id,
    rule_name,
    quality_dimension,
    records_checked,
    records_passed,
    records_failed,
    pass_rate,
    mapping_coverage_rate
from {{ ref('fct_data_quality_results') }}
