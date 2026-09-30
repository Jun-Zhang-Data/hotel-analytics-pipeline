{{ config(materialized='table') }}

with all_exceptions as (
    select
        exception_id,
        detected_at,
        record_key,
        source_system_code,
        entity,
        invalid_value,
        rule_id,
        rule_name,
        quality_dimension,
        severity,
        responsible_domain,
        field_name,
        failure_reason
    from {{ ref('dq_unmapped_hotel_bookings') }}

    union all

    select
        exception_id,
        detected_at,
        record_key,
        source_system_code,
        entity,
        invalid_value,
        rule_id,
        rule_name,
        quality_dimension,
        severity,
        responsible_domain,
        field_name,
        failure_reason
    from {{ ref('dq_missing_guest_id') }}

    union all

    select
        exception_id,
        detected_at,
        record_key,
        source_system_code,
        entity,
        invalid_value,
        rule_id,
        rule_name,
        quality_dimension,
        severity,
        responsible_domain,
        field_name,
        failure_reason
    from {{ ref('dq_invalid_stay_dates') }}
),

latest_actions as (
    select
        exception_id,
        action_status,
        actor,
        note,
        action_at,
        row_number() over (
            partition by exception_id
            order by action_at desc, action_id desc
        ) as rn
    from {{ source('ops', 'dq_exception_actions') }}
)

select
    e.exception_id,
    e.detected_at,
    e.record_key,
    e.source_system_code,
    e.entity,
    e.invalid_value,
    e.rule_id,
    e.rule_name,
    e.quality_dimension,
    e.severity,
    e.responsible_domain,
    e.field_name,
    e.failure_reason,
    coalesce(a.action_status, 'OPEN') as exception_status,
    a.actor as latest_action_actor,
    a.note as latest_action_note,
    a.action_at as latest_action_at
from all_exceptions e
left join latest_actions a
    on e.exception_id = a.exception_id
   and a.rn = 1
