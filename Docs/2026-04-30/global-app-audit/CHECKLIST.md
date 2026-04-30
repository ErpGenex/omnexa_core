# Global Deep-Domain Checklist — 2026-04-30

Use this checklist to evaluate and harden **every** domain app to an “authentic enterprise depth” standard.

## 1) Domain model completeness

- [ ] Masters exist for the domain (types, categories, profiles, policies).
- [ ] Transactions exist for real execution (requests → approvals → execution → closure).
- [ ] Clear lifecycle states (Draft/Planned/In Progress/Completed/Cancelled) and transitions.
- [ ] Attachment/document strategy is consistent.
- [ ] Cross-company/branch rules are deterministic.

## 2) Workflow & controls

- [ ] Workflows (or validations) enforce approvals and segregation of duties.
- [ ] SLA/aging fields exist where relevant.
- [ ] Cancellation/rollback logic is safe and audited.

## 3) Reporting (minimum set)

- [ ] Register report
- [ ] Summary by status
- [ ] Trend report
- [ ] Exceptions report
- [ ] Compliance report
- [ ] Forecast report (where applicable)
- [ ] Risk register (where applicable)

## 4) Dashboards / command center

- [ ] Command Center API payload exists (`get_<domain>_command_center(...)`).
- [ ] Workspace includes links to new doctypes and reports.
- [ ] KPI charts (or at least number cards) exist for backlog/health distribution.

## 5) Integration readiness

- [ ] Ingestion APIs are idempotent and validate payloads.
- [ ] Outbound events exist for external connectors (n8n, webhooks, MQ).
- [ ] Dead-letter/retry strategy exists for failures.

## 6) Automation & schedulers

- [ ] Any scheduler job is behind feature flags.
- [ ] Jobs are bounded by limit/page size and safe on large datasets.
- [ ] Jobs write audit logs / status to a policy or log doctype.

## 7) Security / permissions / row-level access

- [ ] Permission Query Conditions exist (company/branch scoping).
- [ ] Doc events enforce branch context.
- [ ] Reports respect row-level access constraints.

## 8) Migrations & rollback safety

- [ ] All changes are additive (no destructive schema).
- [ ] Every derived field has a backfill patch.
- [ ] `DEPLOYMENT_GUIDE.md` exists.
- [ ] `ROLLBACK_GUIDE.md` exists.

## 9) Testing minimum bar

- [ ] 1 smoke test: imports, basic insert/submit/cancel.
- [ ] 1 business rule test: validation correctness.
- [ ] 1 migration/backfill test if patches exist.

