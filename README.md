# Hotel Analytics Pipeline

Small production-style analytics engineering project.

## Flow

CSV source
→ Python ingestion
→ PostgreSQL raw
→ dbt staging
→ dbt intermediate
→ fact/dimension
→ mart

Airflow orchestrates the end-to-end run.

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

hotel_analytics_pipeline

## Stop

```bash
docker compose down
```

To remove local database volumes too:

```bash
docker compose down -v
```
