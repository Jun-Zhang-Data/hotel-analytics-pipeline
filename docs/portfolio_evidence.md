# Portfolio Evidence and Safe Claims

This file lists claims that are directly supported by implemented repository functionality.

## Safe project summary

Built a containerized hotel analytics pipeline using PostgreSQL, dbt, Apache Airflow, Docker, Python, and GitHub Actions, with governed master/reference data, source-to-canonical hotel mappings, structured data-quality exceptions, DQ KPI marts, source-to-target mapping, automated UAT tests, and Power BI-ready reporting models.

## Safe CV / LinkedIn bullets

- Built a layered PostgreSQL/dbt analytics pipeline for hotel booking and payment data, orchestrated with Apache Airflow and validated through GitHub Actions CI.
- Implemented canonical hotel master data, source-system reference data, and source-to-canonical hotel mappings with dbt relationship, uniqueness, lifecycle-status, and active-mapping controls.
- Added mapping, completeness, and validity data-quality rules with structured exception tables that prevent failed records from entering trusted booking facts.
- Developed DQ KPI models for records checked, passed, failed, pass rate, mapping coverage, and exception counts by date, source, and rule.
- Documented source-to-target mappings and automated Given/When/Then UAT scenarios with CI-backed acceptance evidence.
- Built Power BI-ready operational and data-quality marts for hotel performance, DQ monitoring, and exception reporting.
- Demonstrated regression testing for safe SQL refactoring by comparing old and refactored transformation outputs before promotion.

## Evidence map

| Capability | Repository evidence |
|---|---|
| Master data | `dbt_hotel/models/master/dim_hotel_master.sql` |
| Source-system reference data | `dbt_hotel/models/reference/dim_source_system_reference.sql` |
| Source-to-canonical mapping | `dbt_hotel/models/master/map_hotel_source_to_canonical.sql` |
| Active-mapping uniqueness control | `dbt_hotel/tests/business_rules/master_data/assert_unique_active_hotel_mapping.sql` |
| Mapping exception | `dbt_hotel/models/quality/exceptions/dq_unmapped_hotel_bookings.sql` |
| Completeness exception | `dbt_hotel/models/quality/exceptions/dq_missing_guest_id.sql` |
| Validity exception | `dbt_hotel/models/quality/exceptions/dq_invalid_stay_dates.sql` |
| DQ KPI fact | `dbt_hotel/models/quality/fct_data_quality_results.sql` |
| DQ reporting marts | `dbt_hotel/models/marts/mart_dq_daily.sql`, `mart_dq_by_source.sql`, `mart_exception_summary.sql`, `mart_power_bi_dq_rule_daily.sql` |
| Operational BI mart | `dbt_hotel/models/marts/mart_power_bi_hotel_daily.sql` |
| Source-to-target mapping | `docs/source_to_target_mapping.csv` |
| UAT | `docs/uat_test_cases.md` and `dbt_hotel/tests/uat/` |
| Power BI reporting contract | `docs/power_bi_reporting_contract.md` |
| Orchestration | `airflow/dags/hotel_pipeline.py` |
| CI | `.github/workflows/dbt-ci.yml` |

## Claims to avoid

Do not claim that the repository includes:
- a Power BI `.pbix` dashboard
- Power BI Service deployment or refresh configuration
- Azure or Microsoft Fabric implementation
- enterprise MDM software
- a human case-management interface for exception remediation
- a fully deployed production cloud platform

Use wording such as `Power BI-ready marts` rather than `Power BI dashboard`, and `structured exception outputs` rather than `full exception lifecycle management`.
