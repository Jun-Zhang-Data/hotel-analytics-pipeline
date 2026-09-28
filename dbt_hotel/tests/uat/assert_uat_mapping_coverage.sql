with mapping_result as (
    select
        sum(records_checked) as records_checked,
        sum(records_passed) as records_passed,
        sum(records_failed) as records_failed,
        round(sum(records_passed)::numeric / nullif(sum(records_checked), 0), 4) as coverage_rate
    from {{ ref('fct_data_quality_results') }}
    where rule_id = 'DQ_MAP_HOTEL_001'
)
select *
from mapping_result
where records_checked <> 6
   or records_passed <> 5
   or records_failed <> 1
   or coverage_rate <> 0.8333
