# Exception Lifecycle Design

This document defines lifecycle semantics for structured data-quality exceptions. Exception detection remains deterministic in dbt models; human or operational disposition is stored separately as append-only operational metadata.

## Status model

Supported current statuses are:

- `OPEN` — detected and not yet dispositioned.
- `ACKNOWLEDGED` — reviewed and accepted for follow-up.
- `RESOLVED` — the underlying source/reference issue has been corrected or otherwise closed.
- `REPROCESSED` — the affected data has been reprocessed after correction and recovery has been verified.

`OPEN` is derived from the exception model itself. Other states are recorded as append-only actions in `ops.dq_exception_actions`.

## Design rules

Exception detection and lifecycle disposition are intentionally separated. dbt exception models answer “does this record currently violate a rule?”; the operational action log answers “what has an operator done about this exception?”. This avoids mutating generated analytical exception tables directly.

Lifecycle events are append-only. The current status is the latest action for an `exception_id`; when no action exists, the current status is `OPEN`. Repeated dbt builds can recreate analytical exception tables without erasing the operational action history.

A lifecycle action does not override trusted-data gating. A booking that still violates a blocking rule remains excluded from trusted facts even if its exception is acknowledged. Resolution and reprocessing are operational states, not a bypass of DQ logic.

## Operational command

Use `scripts/manage_dq_exception.py` to record a lifecycle action:

```bash
python scripts/manage_dq_exception.py \
  --exception-id <exception_id> \
  --status ACKNOWLEDGED \
  --actor data-team \
  --note "Investigating missing hotel mapping"
```

After the source/reference issue is corrected and affected data is rebuilt, record `RESOLVED` or `REPROCESSED` as appropriate.

## Reporting

`mart_exception_register` combines currently detected exceptions with the latest operational lifecycle action. `mart_exception_summary` aggregates the register by date, source, rule, quality dimension, and current status.

The action log is an operational audit trail, not a full ticketing/case-management system. The repository does not implement assignment queues, SLA timers, approvals, notifications, or a remediation UI.
