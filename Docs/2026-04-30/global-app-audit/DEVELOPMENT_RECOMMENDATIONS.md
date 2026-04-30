# Development Recommendations (Global) — 2026-04-30

## What “authentic enterprise depth” means (standard)

For each domain app, target the following minimum set:

- **Data model**: Masters + transactions + reference tables + lifecycle states
- **Work execution**: end-to-end operational flow (create → approve → execute → close)
- **Accounting linkage**: where needed, deterministic posting rules and reconciliation paths
- **Analytics**: at least 6–12 reports (register, trend, exceptions, compliance, forecasting)
- **Dashboards**: KPI summaries + status distribution + backlog/aging where relevant
- **Automation**: scheduler jobs, alerts, rule engines (feature-flag guarded)
- **Integration readiness**: ingestion APIs + outbound events + idempotency keys
- **Testing**: unit tests + migration tests + backward-compat tests
- **Migration safety**: additive only; patches for backfills; rollback plan

## Cross-app improvements (high impact, low risk)

### 1) Global report UX standardization
- **Goal**: unify date filter behavior, defaults, labels, and validation patterns.
- **Action**: enforce from/to date filters and default “Today” globally, plus consistent filter naming.

### 2) Global KPI framework
- **Goal**: every app should expose a “Command Center” payload (counts, aging, risk).
- **Action**: standardize `get_<domain>_command_center(company, branch)` pattern.

### 3) Feature flags everywhere
- **Goal**: protect advanced engines (predictive, schedulers, condition monitoring) to avoid surprises on production sites.
- **Action**: ensure all scheduled tasks and heavy computations are behind flags.

### 4) Migration discipline & rollback playbooks
- **Goal**: any schema evolution must ship with patch + rollback steps.
- **Action**: require `docs/DEPLOYMENT_GUIDE.md` and `docs/ROLLBACK_GUIDE.md` per enterprise module.

### 5) Testing minimum bar
- **Goal**: every app has at least:
  - 1 smoke test
  - 1 critical business rule test
  - 1 migration/backfill test if patches exist

## App-by-app prioritized next actions (structure-guided)

### Tier A
- **omnexa_accounting**
  - Expand dashboard charts/KPIs layer (reports exist; dashboards are thin).
  - Add scheduler-driven risk monitors (AR aging, inventory pressure) behind feature flags.
- **omnexa_core**
  - Continue centralizing cross-cutting concerns (report defaults, workspace sync, security guards).
  - Add “platform compatibility tests” to prevent breakages across dependent apps.
- **omnexa_fixed_assets**
  - Build UI pages for Command Center / Condition Monitoring / Scheduling board (data layer exists).
  - Add inspection execution UX (mobile-first forms) and deep work order lifecycle analytics.

### Tier B
- **omnexa_healthcare / omnexa_tourism / omnexa_vehicle_finance / omnexa_operational_risk**
  - Convert “reports-only” insights into dashboards + exception alerts.
  - Add domain-specific scheduler jobs (daily risk/compliance checks).
  - Increase unit/integration tests for critical workflows.

### Tier C
- **omnexa_trading / omnexa_manufacturing / omnexa_leasing_finance / omnexa_credit_engine / omnexa_factoring / omnexa_mortgage_finance**
  - Validate end-to-end flows exist (masters → transactions → postings → reports).
  - Add a “domain command center payload” API for each.
  - Add patch + backfill safety for any schema evolution.

### Tier D
- **omnexa_n8n_bridge**
  - Add reliability: idempotency keys, retry policy, dead-letter management, and tests.
- **omnexa_setup_intelligence**
  - Expand “setup quality gates” and standardize module enablement flags.
- **omnexa_intelligence_core**
  - Ensure operational resilience: missing-table guards (already seen), migrations, feature flags.
- **omnexa_user_academy**
  - Add onboarding workspaces and minimal report pack to justify module.

