# Data Contracts

The executable contract is `config/data_contracts.json`; `scripts/validate_source_contracts.py` enforces it before ingestion.

## Contract policy

A source change is **breaking** when a required column is missing or renamed, or when values cannot be parsed as the declared type. Breaking changes fail fast before raw ingestion and therefore before trusted dbt models are built.

An additional source column is **non-breaking** by default. It is reported as a warning and ignored until the contract and downstream models are intentionally updated.

Allowed-value violations are treated as breaking contract failures when an allow-list is defined. Business-domain exceptions that are valid structurally but fail trusted-data rules continue through ingestion and are handled by the dbt DQ/exception layer.

## Bookings contract

Required fields: `booking_id`, `source_system_code`, `source_hotel_code`, `guest_id`, `booking_date`, `check_in_date`, `check_out_date`, `status`, `source_updated_at`.

Declared types: booking/check-in/check-out dates are ISO dates; `source_updated_at` is a timestamp; identifiers/status are strings; `guest_id` is nullable. `status` currently allows `CONFIRMED` and `CANCELLED`.

## Payments contract

Required fields: `payment_id`, `booking_id`, `amount`, `currency`, `source_updated_at`.

Declared types: `amount` is numeric, `source_updated_at` is a timestamp, and identifiers/currency are strings.

## Change procedure

1. Reproduce the source change in a branch.
2. Run `python scripts/validate_source_contracts.py` and capture the failure.
3. Decide whether the change is backward-compatible, requires a mapping/normalization change, or requires downstream model changes.
4. Update `config/data_contracts.json` only together with the required ingestion/dbt/test changes.
5. Run CI and verify trusted outputs and DQ behavior.
6. Update this document, architecture notes, and any affected source-to-target mapping.

The contract gate protects structure and basic compatibility. It does not replace business DQ rules such as canonical hotel mapping, guest completeness, or stay-date validity.
