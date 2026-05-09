# ERPGENEX Core (`omnexa_core`)

[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-2ea44f?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![ERP System](https://img.shields.io/badge/ERP-System-1f6feb?style=for-the-badge)](#)
[![SaaS Ready](https://img.shields.io/badge/SaaS-Ready-8250df?style=for-the-badge)](#)

Core platform for ERPGENEX: workspace orchestration, app lifecycle management, licensing flow, integration extensibility, and enterprise desk experience on top of Frappe.

## Why ERPGENEX Core

- Unified control layer for modular ERP applications.
- Marketplace-driven install/update/uninstall workflow.
- Multi-app onboarding and workspace synchronization.
- Integration-ready architecture with hook-based extension points.
- Designed for production operations and SaaS deployment models.

## UI Preview

Add your UI screenshots under `screenshot/` with the names below and they will render automatically.

![ERPGENEX Dashboard](./screenshot/ui-dashboard.png)
![ERPGENEX Marketplace](./screenshot/ui-marketplace.png)
![ERPGENEX Workspace](./screenshot/ui-workspace.png)
![ERPGENEX Integrations](./screenshot/ui-integrations.png)

## تطبيقات جديدة على الـ bench (مع النواة أولاً)

راجع **[docs/BENCH_NEW_APPS.md](docs/BENCH_NEW_APPS.md)** — ترتيب `apps.txt`، أوامر `bench get-app` القياسية لـ GitHub `ErpGenex/*`، وربط `required_apps` مع **`omnexa_core`**.

## Installation

### Option A: Docker (recommended for fast bootstrapping)

Use your existing Frappe/ERPNext Docker stack, then install `omnexa_core` into the running bench:

```bash
# inside your dockerized bench container
cd /home/frappe/frappe-bench
bench get-app https://github.com/ErpGenex/omnexa_core.git --branch develop
bench --site <your-site> install-app omnexa_core
bench --site <your-site> migrate
```

### Option B: Script / Bench CLI

For VM or bare-metal environments:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/ErpGenex/omnexa_core.git --branch develop
bench --site <your-site> install-app omnexa_core
bench --site <your-site> migrate
```

## Post-Install

- Open Desk and verify ERPGENEX workspaces are visible.
- Confirm app dependencies are fetched and installed.
- Run smoke checks for onboarding, marketplace, and reports.

## Contributing

This app uses `pre-commit` for formatting and linting.

```bash
cd apps/omnexa_core
pre-commit install
```

Enabled checks:

- `ruff`
- `eslint`
- `prettier`
- `pyupgrade`

## License

MIT
