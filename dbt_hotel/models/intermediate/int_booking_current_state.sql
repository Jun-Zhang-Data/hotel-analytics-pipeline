{{ config(
    materialized='incremental',
    unique_key='booking_id',
    incremental_strategy='delete+insert',
    post_hook=[
        "{{ advance_incremental_watermark('int_booking_current_state', 'bookings') }}",
        "{{ advance_incremental_watermark('int_booking_current_state', 'payments') }}"
    ]
) }}

with bookings as (
    select
        booking_id,
        source_system_code,
        source_hotel_code,
        hotel_id,
        is_hotel_mapped,
        guest_id,
        booking_date,
        check_in_date,
        check_out_date,
        booking_status,
        source_updated_at,
        ingested_at
    from {{ ref('int_bookings_mapped') }}

    {% if is_incremental() %}
    where booking_id in {{ changed_booking_keys('int_booking_current_state') }}
    {% endif %}
),

hotels as (
    select
        hotel_id,
        hotel_name,
        city
    from {{ ref('dim_hotel_master') }}
),

payments as (
    select
        booking_id,
        total_payment,
        latest_payment_ingested_at
    from {{ ref('int_payments_by_booking') }}
),

{% if is_incremental() %}
previous_state as (
    select
        booking_id,
        booking_date as previous_booking_date,
        hotel_id as previous_hotel_id,
        is_trusted as previous_is_trusted
    from {{ this }}
),
{% else %}
previous_state as (
    select
        cast(null as text) as booking_id,
        cast(null as date) as previous_booking_date,
        cast(null as text) as previous_hotel_id,
        cast(null as boolean) as previous_is_trusted
    where false
),
{% endif %}

current_state as (
    select
        bookings.booking_id,
        bookings.source_system_code,
        bookings.source_hotel_code,
        bookings.hotel_id,
        hotels.hotel_name,
        hotels.city,
        bookings.guest_id,
        bookings.booking_date,
        bookings.check_in_date,
        bookings.check_out_date,
        bookings.booking_status,
        coalesce(payments.total_payment, 0) as total_payment,
        bookings.check_in_date - bookings.booking_date as booking_lead_days,
        bookings.is_hotel_mapped,
        (
            bookings.is_hotel_mapped = true
            and bookings.guest_id is not null
            and bookings.check_out_date >= bookings.check_in_date
        ) as is_trusted,
        bookings.source_updated_at as booking_source_updated_at,
        bookings.ingested_at as booking_ingested_at,
        payments.latest_payment_ingested_at,
        greatest(
            bookings.ingested_at,
            coalesce(payments.latest_payment_ingested_at, bookings.ingested_at)
        ) as change_detected_at,
        previous_state.previous_booking_date,
        previous_state.previous_hotel_id,
        coalesce(previous_state.previous_is_trusted, false) as previous_is_trusted,
        current_timestamp as processed_at
    from bookings
    left join hotels
        on bookings.hotel_id = hotels.hotel_id
    left join payments
        on bookings.booking_id = payments.booking_id
    left join previous_state
        on bookings.booking_id = previous_state.booking_id
)

select *
from current_state
