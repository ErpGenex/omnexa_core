# System Inventory (Global) — 2026-04-30

## Scope

All applications detected under `apps/omnexa_*` (excluding test dummy):
- `omnexa_accounting`, `omnexa_core`, `omnexa_fixed_assets`, `omnexa_hr`, `omnexa_intelligence_core`, …

## Objective inventory

See `STRUCTURE_METRICS.json` for objective counts by app:
- **DocTypes**
- **Reports**
- **Workspaces**
- **Patches**
- **Tests**
- **API files**
- **Scheduler task presence**

## Quick maturity tiers (structure-based)

These tiers reflect *structure depth signals* (not functional correctness). Use them to prioritize deep-dive review.

- **Tier A (Deep platform modules)**  
  - `omnexa_accounting` (very high DocType/report coverage)  
  - `omnexa_core` (platform glue, many workspaces, strong test count)  
  - `omnexa_fixed_assets` (now includes enterprise EAM stack)

- **Tier B (Domain modules with breadth)**  
  - `omnexa_healthcare`, `omnexa_tourism` (higher DocType/report counts)
  - `omnexa_vehicle_finance`, `omnexa_operational_risk`, `omnexa_finance_engine` (higher DocTypes + tests + APIs)

- **Tier C (Moderate domain modules)**  
  - `omnexa_trading`, `omnexa_manufacturing`, `omnexa_leasing_finance`, `omnexa_credit_engine`, `omnexa_factoring`, `omnexa_mortgage_finance`

- **Tier D (Thin / bootstrap / integration apps)**  
  - `omnexa_setup_intelligence`, `omnexa_backup`, `omnexa_user_academy`, `omnexa_n8n_bridge`, `omnexa_intelligence_core` (few doctypes/reports; mostly API/bridge or setup logic)

## Global architecture observations

- **Most apps are packaged consistently** (`README.md`, `pyproject.toml`, `license.txt`), suggesting a standardized scaffold.
- **The dominant “depth signal” is DocTypes+Reports**, but **several apps have low test coverage** which increases regression risk.
- Many domain apps show **reports without dashboards/charts**, indicating an opportunity for a unified KPI layer and “command center” pattern.

