# ADR 003 — Validate source contracts before ingestion

## Status
Accepted

## Context
A missing/renamed required column or incompatible source type should be detected before data reaches trusted models. Business DQ exceptions should remain distinct from technical schema incompatibility.

## Decision
Maintain executable source contracts in `config/data_contracts.json` and run `scripts/validate_source_contracts.py` before raw ingestion in Airflow and CI. Missing required columns, incompatible declared types, and configured allow-list violations are blocking. Additional columns are warnings by default.

## Alternatives considered
Relying only on downstream dbt failures would detect some changes later and with less direct error messages. Automatically accepting all schema evolution would risk silent semantic drift. Treating every additional column as breaking would create unnecessary operational noise.

## Consequences
Breaking source changes fail fast with an explicit compatibility error. Structurally valid records that fail business rules still enter raw data and are handled by the existing DQ/exception framework. Contract changes now require coordinated code, tests, and documentation updates.
