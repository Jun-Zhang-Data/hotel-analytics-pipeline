{{ config(materialized='table') }}

select
    check_date,
    sum(records_checked) as records_checked,
    sum(records_passed) as records_passed,
    sum(records_failed) as records_failed,
    round(sum(records_passed)::numeric / nullif(sum(records_checked), 0), 4) as dq_pass_rate,
    round(
        sum(case when quality_dimension = 'MAPPING_COVERAGE' then records_passed else 0 end)::numeric
        / nullif(sum(case when quality_dimension = 'MAPPING_COVERAGE' then records_checked else 0 end), 0),
        4
    ) as mapping_coverage_rate
from {{ ref('fct_data_quality_results') }}
group by check_date
