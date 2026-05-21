# Omnexa bench ops scripts

Run from **frappe-bench** root.

```bash
# Full external deploy (after git pull)
export SITE=your.production.site
bash apps/omnexa_core/omnexa_core/scripts/ops/deploy_external_server.sh

# Reports audit checklist only (writes Docs/ on bench)
python3 apps/omnexa_core/omnexa_core/scripts/ops/audit_reports_print_checklist.py --merge
```

`bench execute` for print/filters is included in `deploy_external_server.sh`.
