# ErpGenEx Apps Catalog — Detailed Description, Global Evaluation, and Licensing

Date: 2026-04-23
Source of truth for licensing/free status: live Marketplace catalog on site `erpgenex.local.site`.

## Evaluation Method

- Global evaluation score (0-100) combines: integration hooks, data model depth, reports, workspace readiness, tests, and operational wiring.
- Grade mapping: A+ (>=95), A (85-94), B (75-84), C (60-74), D (<60).
- Commercial status is taken from Marketplace (`price_type`, `is_free`).

## Subscription Pricing (Competitive Global) — Licensed Apps Only

Currency: USD (per company/site). Prices below are **per app** unless stated otherwise.

Discount logic (applied to the monthly equivalent):
- 1 month: 0%
- 3 months: 10%
- 6 months: 15%
- 12 months: 25%
- 24 months: 35%
- 36 months: 45%

### Pricing Tiers

- **Tier U (Utility / Ops)**: $29 / month
- **Tier V (Vertical Standard)**: $79 / month
- **Tier R (Regulated / Risk & Governance)**: $129 / month

### Plan Prices by Tier (USD)

| Tier | 1 month | 3 months | 6 months | 12 months | 24 months | 36 months |
|---|---:|---:|---:|---:|---:|---:|
| **U** | $29 | $78 | $148 | $261 | $452 | $574 |
| **V** | $79 | $213 | $403 | $711 | $1,232 | $1,565 |
| **R** | $129 | $348 | $658 | $1,161 | $2,012 | $2,555 |

> Note: totals above are rounded to whole USD for simplicity and to stay competitive globally.

### Tier Mapping (Licensed Apps)

- **Tier U**: `omnexa_backup`
- **Tier R**: `omnexa_alm`, `omnexa_credit_risk`, `omnexa_credit_engine`, `omnexa_finance_engine`, `omnexa_operational_risk`, `omnexa_sme_retail_finance`, `omnexa_consumer_finance`, `omnexa_vehicle_finance`, `omnexa_mortgage_finance`, `omnexa_factoring`, `omnexa_leasing_finance`, `omnexa_reporting_compliance`, `omnexa_statutory_audit`
- **Tier V**: all other apps marked **بترخيص (Licensed)** in this catalog (e.g. `omnexa_trading`, `omnexa_tourism`, `omnexa_construction`, `omnexa_healthcare`, `omnexa_education`, `omnexa_services`, `omnexa_car_rental`, `omnexa_agriculture`, `omnexa_engineering_consulting`, `omnexa_manufacturing`, `omnexa_restaurant`).

### Optional Bundle (Recommended for Sales Competitiveness)

- **ErpGenEx “Industries Bundle”** (all Tier V apps for a single company/site): **$299 / month**
- **ErpGenEx “Finance & Risk Bundle”** (all Tier R apps for a single company/site): **$399 / month**
- **ErpGenEx “All-in Bundle”** (Tier V + Tier R + Tier U): **$649 / month**

Bundles use the same 3/6/12/24/36 month discounts above.

## Applications Profile

### ERPGenEx Theme 0426
- App slug: `erpgenex_theme_0426`
- Detailed description: Enterprise Desk theme (ERPGenEx 0426) with optional business-theme-inspired polish.
- Activity domain: `ErpGenEx`
- Global evaluation: **14/100** — D (Foundational)
- Technical depth snapshot: doctypes=0, reports=0, workspaces=0, tests=0
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/erpgenex_theme_0426.git`

### ErpGenEx — Accounting
- App slug: `omnexa_accounting`
- Detailed description: Double-entry accounting for ErpGenEx (omnexa_accounting)
- Activity domain: `Accounting`
- Global evaluation: **100/100** — A+ (Global-Ready Strong)
- Technical depth snapshot: doctypes=56, reports=44, workspaces=1, tests=10
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_accounting.git`

### ErpGenEx — Agriculture
- App slug: `omnexa_agriculture`
- Detailed description: Agriculture vertical
- Activity domain: `Agriculture`
- Global evaluation: **78/100** — B (Good / Needs Hardening)
- Technical depth snapshot: doctypes=6, reports=4, workspaces=1, tests=2
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_agriculture.git`

### ErpGenEx — ALM
- App slug: `omnexa_alm`
- Detailed description: Asset and liability management vertical
- Activity domain: `Alm`
- Global evaluation: **100/100** — A+ (Global-Ready Strong)
- Technical depth snapshot: doctypes=9, reports=5, workspaces=2, tests=8
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_alm.git`

### ERPGENEX — Backup
- App slug: `omnexa_backup`
- Detailed description: Scheduled backups with local path, FTP, Google Drive, and email (omnexa_backup)
- Activity domain: `Backup`
- Global evaluation: **40/100** — D (Foundational)
- Technical depth snapshot: doctypes=1, reports=0, workspaces=0, tests=0
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_backup.git`

### ErpGenEx Car Rental
- App slug: `omnexa_car_rental`
- Detailed description: Global Car Rental and Fleet Management
- Activity domain: `Mobility`
- Global evaluation: **87/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=13, reports=8, workspaces=1, tests=1
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_car_rental.git`

### ErpGenEx — Construction
- App slug: `omnexa_construction`
- Detailed description: Construction management vertical
- Activity domain: `Construction`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=11, reports=6, workspaces=1, tests=4
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_construction.git`

### ErpGenEx — Consumer Finance
- App slug: `omnexa_consumer_finance`
- Detailed description: Consumer finance vertical
- Activity domain: `Finance`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=6, reports=5, workspaces=2, tests=6
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_consumer_finance.git`

### ERPGENEX — Core
- App slug: `omnexa_core`
- Detailed description: Core platform for ERPGENEX (omnexa_core)
- Activity domain: `Core`
- Global evaluation: **76/100** — B (Good / Needs Hardening)
- Technical depth snapshot: doctypes=7, reports=0, workspaces=12, tests=13
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_core.git`

### ErpGenEx — Credit Engine
- App slug: `omnexa_credit_engine`
- Detailed description: Shared credit engine services
- Activity domain: `Credit`
- Global evaluation: **100/100** — A+ (Global-Ready Strong)
- Technical depth snapshot: doctypes=8, reports=5, workspaces=2, tests=7
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_credit_engine.git`

### ErpGenEx — Credit Risk
- App slug: `omnexa_credit_risk`
- Detailed description: Credit risk and ORR vertical
- Activity domain: `Risk`
- Global evaluation: **94/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=8, reports=1, workspaces=2, tests=8
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_credit_risk.git`

### ErpGenEx — Customer Core
- App slug: `omnexa_customer_core`
- Detailed description: Shared customer core services
- Activity domain: `Customer`
- Global evaluation: **73/100** — C (Partial Readiness)
- Technical depth snapshot: doctypes=6, reports=3, workspaces=2, tests=1
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_customer_core.git`

### ErpGenEx — Education
- App slug: `omnexa_education`
- Detailed description: Education vertical
- Activity domain: `Education`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=19, reports=7, workspaces=1, tests=2
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_education.git`

### ErpGenEx — E-Invoice
- App slug: `omnexa_einvoice`
- Detailed description: Egypt e-Invoice and e-Receipt integrations
- Activity domain: `Einvoice`
- Global evaluation: **68/100** — C (Partial Readiness)
- Technical depth snapshot: doctypes=3, reports=0, workspaces=1, tests=4
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_einvoice.git`

### ErpGenEx — Engineering Consulting
- App slug: `omnexa_engineering_consulting`
- Detailed description: Engineering consulting vertical
- Activity domain: `Engineering`
- Global evaluation: **84/100** — B (Good / Needs Hardening)
- Technical depth snapshot: doctypes=7, reports=6, workspaces=1, tests=2
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_engineering_consulting.git`

### ErpGenEx — Experience
- App slug: `omnexa_experience`
- Detailed description: Public web, catalog, checkout, and booking for ErpGenEx (omnexa_experience)
- Activity domain: `Experience`
- Global evaluation: **63/100** — C (Partial Readiness)
- Technical depth snapshot: doctypes=7, reports=0, workspaces=1, tests=1
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_experience.git`

### ErpGenEx — Factoring
- App slug: `omnexa_factoring`
- Detailed description: Factoring and discounting vertical
- Activity domain: `Factoring`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=7, reports=5, workspaces=2, tests=6
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_factoring.git`

### ErpGenEx — Finance Engine
- App slug: `omnexa_finance_engine`
- Detailed description: Shared finance engine services
- Activity domain: `Finance`
- Global evaluation: **94/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=10, reports=1, workspaces=2, tests=10
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_finance_engine.git`

### ErpGenEx — Fixed Assets
- App slug: `omnexa_fixed_assets`
- Detailed description: Fixed assets (IAS 16 / IFRS cost model: capitalization, depreciation, derecognition)
- Activity domain: `Fixed`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=15, reports=9, workspaces=1, tests=3
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_fixed_assets.git`

### ErpGenEx — Healthcare
- App slug: `omnexa_healthcare`
- Detailed description: Healthcare vertical
- Activity domain: `Healthcare`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=25, reports=7, workspaces=1, tests=3
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_healthcare.git`

### ErpGenEx — HR
- App slug: `omnexa_hr`
- Detailed description: HR management free core app
- Activity domain: `Hr`
- Global evaluation: **74/100** — C (Partial Readiness)
- Technical depth snapshot: doctypes=7, reports=8, workspaces=2, tests=0
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_hr.git`

### ErpGenEx Intelligence Core
- App slug: `omnexa_intelligence_core`
- Detailed description: Signals, predictions, recommendations, risk and benchmark engine
- Activity domain: `Intelligence`
- Global evaluation: **48/100** — D (Foundational)
- Technical depth snapshot: doctypes=4, reports=0, workspaces=0, tests=0
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_intelligence_core.git`

### ErpGenEx — Leasing Finance
- App slug: `omnexa_leasing_finance`
- Detailed description: Leasing finance vertical
- Activity domain: `Finance`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=9, reports=5, workspaces=1, tests=4
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_leasing_finance.git`

### ErpGenEx — Manufacturing
- App slug: `omnexa_manufacturing`
- Detailed description: Manufacturing vertical
- Activity domain: `Manufacturing`
- Global evaluation: **87/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=14, reports=9, workspaces=1, tests=1
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_manufacturing.git`

### ErpGenEx — Mortgage Finance
- App slug: `omnexa_mortgage_finance`
- Detailed description: Mortgage finance vertical
- Activity domain: `Finance`
- Global evaluation: **100/100** — A+ (Global-Ready Strong)
- Technical depth snapshot: doctypes=8, reports=5, workspaces=2, tests=6
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_mortgage_finance.git`

### ErpGenEx — Operational Risk
- App slug: `omnexa_operational_risk`
- Detailed description: Operational risk management vertical
- Activity domain: `Risk`
- Global evaluation: **100/100** — A+ (Global-Ready Strong)
- Technical depth snapshot: doctypes=10, reports=5, workspaces=2, tests=7
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_operational_risk.git`

### ErpGenEx — Projects PM
- App slug: `omnexa_projects_pm`
- Detailed description: Project management vertical
- Activity domain: `Projects`
- Global evaluation: **100/100** — A+ (Global-Ready Strong)
- Technical depth snapshot: doctypes=8, reports=6, workspaces=1, tests=5
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_projects_pm.git`

### ErpGenEx — Reporting Compliance
- App slug: `omnexa_reporting_compliance`
- Detailed description: Shared reporting and compliance services
- Activity domain: `Reporting`
- Global evaluation: **44/100** — D (Foundational)
- Technical depth snapshot: doctypes=0, reports=0, workspaces=0, tests=2
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_reporting_compliance.git`

### ErpGenEx Restaurant
- App slug: `omnexa_restaurant`
- Detailed description: Global Restaurant and Cafe Management
- Activity domain: `Restaurant`
- Global evaluation: **82/100** — B (Good / Needs Hardening)
- Technical depth snapshot: doctypes=16, reports=6, workspaces=1, tests=0
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_restaurant.git`

### ErpGenEx — Services
- App slug: `omnexa_services`
- Detailed description: Services vertical
- Activity domain: `Services`
- Global evaluation: **87/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=15, reports=5, workspaces=1, tests=1
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_services.git`

### ErpGenEx Setup Intelligence
- App slug: `omnexa_setup_intelligence`
- Detailed description: Live setup state analyzer and dynamic checklists
- Activity domain: `Setup`
- Global evaluation: **40/100** — D (Foundational)
- Technical depth snapshot: doctypes=1, reports=0, workspaces=0, tests=0
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_setup_intelligence.git`

### ErpGenEx — SME Retail Finance
- App slug: `omnexa_sme_retail_finance`
- Detailed description: SME and retail finance vertical
- Activity domain: `Finance`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=7, reports=5, workspaces=1, tests=6
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_sme_retail_finance.git`

### ErpGenEx — Statutory Audit
- App slug: `omnexa_statutory_audit`
- Detailed description: Statutory audit vertical
- Activity domain: `Statutory`
- Global evaluation: **78/100** — B (Good / Needs Hardening)
- Technical depth snapshot: doctypes=5, reports=3, workspaces=1, tests=2
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_statutory_audit.git`

### ErpGenEx Theme Manager
- App slug: `omnexa_theme_manager`
- Detailed description: Desk workspace to upload, import, and switch company Desk themes safely (Experience Tenant Theme).
- Activity domain: `Theme`
- Global evaluation: **26/100** — D (Foundational)
- Technical depth snapshot: doctypes=0, reports=0, workspaces=0, tests=0
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_theme_manager.git`

### ErpGenEx — Tourism
- App slug: `omnexa_tourism`
- Detailed description: Tourism vertical
- Activity domain: `Tourism`
- Global evaluation: **92/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=25, reports=13, workspaces=1, tests=2
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_tourism.git`

### ErpGenEx — Trading
- App slug: `omnexa_trading`
- Detailed description: Trading and POS vertical
- Activity domain: `Trading`
- Global evaluation: **87/100** — A (Global-Ready)
- Technical depth snapshot: doctypes=18, reports=8, workspaces=1, tests=1
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_trading.git`

### ErpGenEx User Academy
- App slug: `omnexa_user_academy`
- Detailed description: Free in-app guides and tutorials for end users
- Activity domain: `User`
- Global evaluation: **40/100** — D (Foundational)
- Technical depth snapshot: doctypes=2, reports=0, workspaces=0, tests=0
- Commercial model: **مجاني (Free)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_user_academy.git`

### ErpGenEx — Vehicle Finance
- App slug: `omnexa_vehicle_finance`
- Detailed description: Vehicle finance vertical
- Activity domain: `Finance`
- Global evaluation: **100/100** — A+ (Global-Ready Strong)
- Technical depth snapshot: doctypes=11, reports=5, workspaces=2, tests=6
- Commercial model: **بترخيص (Licensed)**
- Marketplace repo: `https://github.com/ErpGenex/omnexa_vehicle_finance.git`

## Executive Totals

- Total apps in catalog: 38
- Free apps: 13
- Licensed apps: 25
- A+/A apps (>=85): 22
- B apps (75-84): 5
- C/D apps (<75): 11

## Launch Recommendation

- Customer launch set should prioritize A+/A apps first.
- Any C/D app should require explicit remediation plan before broad rollout.
- Commercial decision (free/licensed) should remain anchored to Marketplace policy and legal packaging.
