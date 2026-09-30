{% macro incremental_watermark(model_name, source_name) %}
(
    select coalesce(
        max(last_processed_ingested_at),
        cast('1900-01-01 00:00:00' as timestamp)
    )
    from {{ source('ops', 'incremental_model_watermarks') }}
    where model_name = '{{ model_name }}'
      and source_name = '{{ source_name }}'
)
{% endmacro %}

{% macro changed_booking_keys(model_name) %}
(
    select distinct booking_id
    from {{ source('raw', 'bookings') }}
    where ingested_at > {{ incremental_watermark(model_name, 'bookings') }}

    union

    select distinct booking_id
    from {{ source('raw', 'payments') }}
    where booking_id is not null
      and ingested_at > {{ incremental_watermark(model_name, 'payments') }}
)
{% endmacro %}

{% macro advance_incremental_watermarks(model_name) %}
    insert into ops.incremental_model_watermarks (
        model_name,
        source_name,
        last_processed_ingested_at,
        updated_at
    )
    select
        '{{ model_name }}',
        'bookings',
        coalesce(max(ingested_at), cast('1900-01-01 00:00:00' as timestamp)),
        current_timestamp
    from raw.bookings
    on conflict (model_name, source_name)
    do update set
        last_processed_ingested_at = excluded.last_processed_ingested_at,
        updated_at = excluded.updated_at;

    insert into ops.incremental_model_watermarks (
        model_name,
        source_name,
        last_processed_ingested_at,
        updated_at
    )
    select
        '{{ model_name }}',
        'payments',
        coalesce(max(ingested_at), cast('1900-01-01 00:00:00' as timestamp)),
        current_timestamp
    from raw.payments
    on conflict (model_name, source_name)
    do update set
        last_processed_ingested_at = excluded.last_processed_ingested_at,
        updated_at = excluded.updated_at
{% endmacro %}

{% macro delete_affected_hotel_daily_partitions(model_name) %}
    delete from {{ this }} as target
    using (
        select distinct partition_date, partition_hotel_id
        from (
            select
                case when state.is_trusted then state.booking_date end as partition_date,
                case when state.is_trusted then state.hotel_id end as partition_hotel_id
            from {{ ref('int_booking_current_state') }} as state
            where state.booking_id in {{ changed_booking_keys(model_name) }}

            union

            select
                case when state.previous_is_trusted then state.previous_booking_date end,
                case when state.previous_is_trusted then state.previous_hotel_id end
            from {{ ref('int_booking_current_state') }} as state
            where state.booking_id in {{ changed_booking_keys(model_name) }}
        ) affected
        where partition_date is not null
          and partition_hotel_id is not null
    ) partitions
    where target.booking_date = partitions.partition_date
      and target.hotel_id = partitions.partition_hotel_id
{% endmacro %}
