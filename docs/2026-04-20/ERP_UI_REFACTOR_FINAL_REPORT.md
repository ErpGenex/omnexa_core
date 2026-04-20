## ERP UI Refactor — Final Report (Pointer)

This repository contains the **system-wide design system implementation** (`omnexa_core`) used to standardize all ERP screens.

### Status
- **All installed `omnexa_*` apps were closed** with a final “global closure pass”:
  - Each DocType screen carries consistent enterprise section semantics via `identity_section` + `control_section`.
  - Each screen has at least one non-breaking logical metadata field added where missing (examples: `policy_reference`, `snapshot_reference`, `case_owner`, `asset_owner`, `external_reference`).

### Where to find the full progressive report
The full progressive report (including the app-by-app completion logs and rollout actions) is stored in the bench workspace at:

- `/home/frappeuser/frappe-bench/Docs/2026-04-20/ERP_UI_REFACTOR_FINAL_REPORT.md`

If you need this report published as a standalone GitHub repository (outside the bench workspace), create a dedicated docs repository and copy the file above into it.

