# Omnexa bench ops scripts (shipped in omnexa_core — أي سيرفر بعد bench update)

**سيرفر جديد:** `bench --site SITE migrate` يكفي — لا خطوات يدوية.  
راجع `../docs/GREENFIELD_SERVER_AR.md`.

```bash
# تحديث إنتاج (موصى به)
export SITE=your.production.site
bash apps/omnexa_core/omnexa_core/scripts/ops/deploy_external_server.sh

# تدقيق تقارير (اختياري — يكتب docs/global_reports_audit أو bench/Docs)
python3 apps/omnexa_core/omnexa_core/scripts/ops/audit_reports_print_checklist.py --merge

# إجبار execute يدوي (نادر)
FORCE_REPORT_EXECUTE=1 bash apps/omnexa_core/omnexa_core/scripts/ops/deploy_external_server.sh
```

| Script | Use |
|--------|-----|
| `deploy_external_server.sh` | pull + migrate + restart |
| `audit_reports_print_checklist.py` | JSON checklist |
| `deploy_report_print_html.py` | filesystem HTML only (dev) |
| `batch_wire_report_python.py` | dev wiring only |
