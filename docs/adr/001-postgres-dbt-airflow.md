# ADR 001 — Keep PostgreSQL + dbt + Airflow as the core stack

## Status
Accepted

## Context
The existing project already separates ingestion, transformation/testing, orchestration, and analytical serving. The production-grade upgrade needs to demonstrate reliability and ownership, not tool expansion.

## Decision
Keep PostgreSQL as the local warehouse, dbt for transformation/testing/governed analytical logic, and Airflow for orchestration/retry/task boundaries.

## Alternatives considered
Adding Kafka/Kubernetes/cloud orchestration would increase operational surface area without solving a demonstrated requirement in this portfolio-scale project. Replacing dbt with Python/SQL orchestration would collapse transformation/testing responsibilities into a less explicit layer.

## Consequences
The project remains locally reproducible and the reliability work is visible in code, tests, metadata, and runbooks. It does not claim distributed or cloud-scale production characteristics.
