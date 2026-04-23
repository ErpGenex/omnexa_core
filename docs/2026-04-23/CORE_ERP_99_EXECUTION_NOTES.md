# CORE ERP 99% Execution Notes

This implementation adds an executable baseline checker aligned with:

- `Docs/2026-04-23/CORE_ERP_99_READINESS_PLAN_AR.md`

## Added Components

- `omnexa_core/core_erp_readiness.py`
  - `get_core_erp_readiness_snapshot()` (whitelisted)
  - process-level structural checks (Procure-to-Pay, Inventory, O2C, Banking, GL, Payroll, Budgeting, Financial Statements)
  - must-pass matrix checks (Sales/Purchase/Payment/Payroll/Stock/Budget/Financial statements paths)
  - summary score (`readiness_score`) and go-live signal (`go_live_ready`)

- `tools/core_erp_readiness_snapshot.py`
  - CLI wrapper to run the readiness function through `bench execute`.

- `omnexa_core/tests/test_core_erp_readiness.py`
  - smoke test for output structure.

## Run

From bench root:

```bash
python apps/omnexa_core/tools/core_erp_readiness_snapshot.py --site erpgenex.local.site
```

## Notes

- `no_data` status means the transactional path is configured but not exercised yet with posted data.
- This checker is a baseline automation layer and should be used with full UAT and month-end close rehearsals.

