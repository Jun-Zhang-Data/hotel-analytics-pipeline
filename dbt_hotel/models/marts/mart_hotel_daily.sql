{{ config(
    materialized='incremental',
    unique_key=['booking_date', 'hotel_id'],
    incremental_strategy='delete+insert',
    pre_hook="{{ delete_affected_hotel_daily_partitions('mart_hotel_daily') }}",
    post_hook=[
        "{{ advance_incremental_watermark('mart_hotel_daily', 'bookings') }}",
        "{{ advance_incremental_watermark('mart_hotel_daily', 'payments') }}"
    ]
) }}

{% if is_incremental() %}
with affected_partitions as (
    select distinct partition_date, partition_hotel_id
    from (
        select
            case when state.is_trusted then state.booking_date end as partition_date,
            case when state.is_trusted then state.hotel_id end as partition_hotel_id
        from {{ ref('int_booking_current_state') }} as state
        where state.booking_id in {{ changed_booking_keys('mart_hotel_daily') }}

        union

        select
            case when state.previous_is_trusted then state.previous_booking_date end,
            case when state.previous_is_trusted then state.previous_hotel_id end
        from {{ ref('int_booking_current_state') }} as state
        where state.booking_id in {{ changed_booking_keys('mart_hotel_daily') }}
    ) impacted
    where partition_date is not null
      and partition_hotel_id is not null
),

trusted_bookings as (
    select fact.*
    from {{ ref('fct_bookings') }} as fact
    inner join affected_partitions as partitions
        on fact.booking_date = partitions.partition_date
       and fact.hotel_id = partitions.partition_hotel_id
)

select
    booking_date,
    hotel_id,
    count(*) as total_bookings,
    sum(case when booking_status = 'CANCELLED' then 1 else 0 end) as cancelled_bookings,
    sum(revenue) as total_revenue
from trusted_bookings
group by booking_date, hotel_id

{% else %}

select
    booking_date,
    hotel_id,
    count(*) as total_bookings,
    sum(case when booking_status = 'CANCELLED' then 1 else 0 end) as cancelled_bookings,
    sum(revenue) as total_revenue
from {{ ref('fct_bookings') }}
group by booking_date, hotel_id

{% endif %}
