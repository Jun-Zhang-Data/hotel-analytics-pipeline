# Hotel Analytics Pipeline

A **production-style local data engineering project** for hotel booking analytics, built with **PostgreSQL, dbt, Apache Airflow, Docker, and Python**.

The project demonstrates how raw operational hotel data can be transformed into reliable analytics-ready datasets through a layered ELT pipeline, automated data quality checks, workflow orchestration, and Git-based development practices.

## What this repository does

The pipeline processes hotel booking, hotel, and payment data and models it inside PostgreSQL using dbt.

The dbt project follows a layered analytics architecture:

- **Staging layer** cleans and standardizes raw source data.
- **Intermediate layer** handles booking deduplication, payment aggregation, and booking enrichment.
- **Core layer** produces reusable analytical entities such as booking facts and hotel dimensions.
- **Mart layer** creates business-facing aggregates, including daily hotel performance metrics.

## Data flow

```text
CSV source
→ Python ingestion
→ PostgreSQL raw tables
→ dbt staging
→ dbt intermediate
→ dbt fact/dimension models
→ dbt mart
```

Apache Airflow orchestrates the end-to-end workflow.

## Data quality and safe refactoring

The dbt project includes automated tests for data integrity and business rules, including:

- primary-key uniqueness
- required/non-null fields
- invalid booking date relationships
- negative payment amounts
- model-level data quality checks

The repository also demonstrates a safe SQL refactoring workflow.

The `int_bookings_enriched` model was refactored from a direct-join query into a clearer CTE-based structure that explicitly separates booking, hotel, and payment inputs. The business logic and output schema were intentionally kept unchanged.

Before the refactored version replaced the original model, automated regression tests compared the two implementations for:

- missing booking IDs
- extra booking IDs
- field-level parity
- aggregate-level parity

After parity was confirmed, the refactored logic was promoted into the production model, the temporary migration model and old-vs-new comparison tests were removed, and long-lived business invariant tests were retained.

This demonstrates a repeatable approach to changing transformation logic safely without relying only on manual SQL comparison.

## Pipeline orchestration

Apache Airflow orchestrates the local data workflow, while Docker Compose provides a reproducible development environment containing:

- PostgreSQL analytics warehouse
- Airflow metadata database
- Airflow scheduler
- Airflow webserver
- dbt project environment

The setup is designed to simulate common production data-platform patterns locally without claiming to be a fully deployed production infrastructure.

## Tech stack

**Python · SQL · PostgreSQL · dbt · Apache Airflow · Docker · Docker Compose · Git/GitHub**

## Engineering concepts demonstrated

- layered ELT architecture
- dimensional data modeling
- SQL transformations and refactoring
- dbt testing and regression testing
- business-rule validation
- workflow orchestration
- containerized local infrastructure
- environment-based configuration
- Git branching and pull-request workflows

## Scope

This project currently runs as a local, containerized analytics platform.

It follows several production-style engineering practices, but it does not yet include a fully deployed cloud production environment, CI/CD deployment pipeline, centralized monitoring, secrets management, or production-grade infrastructure orchestration.

## Start

```bash
docker compose up -d --build
```

Wait until the services are running.

## Generate sample source files

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project && python scripts/generate_data.py"
```

## Load raw

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project && python scripts/load_raw.py"
```

## Build DEV models

```bash
docker compose exec airflow-webserver bash -lc "cd /opt/project/dbt_hotel && dbt build --target dev --profiles-dir ."
```

## Inspect mart

```bash
docker compose exec warehouse psql -U analytics -d hotel -c "select * from analytics_dev.mart_hotel_daily order by booking_date, hotel_id;"
```

## Airflow UI

Open:

http://localhost:8080

Credentials:

- username: admin
- password: admin

Enable and trigger:

`hotel_analytics_pipeline`

## Stop

```bash
docker compose down
```

To remove local database volumes too:

```bash
docker compose down -v
```
