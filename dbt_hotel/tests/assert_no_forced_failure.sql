-- This singular test is normally empty and therefore passes.
-- CI deliberately sets force_reliability_failure=true to prove that a
-- downstream dbt failure is observable and that a clean rerun recovers.

{% if var('force_reliability_failure', false) %}
select 'forced reliability scenario failure' as failure_reason
{% else %}
select 'no failure' as failure_reason
where false
{% endif %}
