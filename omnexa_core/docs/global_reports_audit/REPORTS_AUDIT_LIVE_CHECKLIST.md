# تقرير التدقيق الحي — ErpGenEx Reports (مكتمل)

**آخر تحديث:** 2026-05-21  
**الموقع:** `erpgenex.local.site`

## الحالة النهائية

| المؤشر | القيمة |
|--------|--------|
| إجمالي التقارير | **286** |
| `audit_status: passed` | **286 / 286** |
| `pending` | **0** |
| فلاتر JSON فارغة (ErpGenEx) | **0** |
| قوالب طباعة HTML (ERPGENEX marker) | **340+ ملف** |
| Letter Head على التقارير (DB) | مُطبَّق عبر `link_erpgenex_report_print_assets` |

## ما تم إنجازه في هذه الجولة

1. **مزامنة فلاتر جميع التطبيقات** — `sync_all_erpgenex_report_json_filters` (W2/W3/W4) بدون استثناء تطبيقات يدوية إلا عند وجود فلاتر مسبقة.
2. **طباعة موحدة** — نشر HTML لـ 80+ تقرير إضافي + ربط Letter Head لـ 31 تقرير على الموقع.
3. **تمديد `batch_wire_report_python`** — ربط ALM، Compliance، Fixed Assets، Property (17 ملف) مع `prepare_filters` / `sql_conditions`.
4. **إصلاحات دقيقة** — `Failed Control Tests` (فلتر Fail)، `ALM NII EVE` (`run_date`)، `Access Control Summary` (فلتر شركة اختياري).
5. **قائمة التدقيق** — تصحيح PRINT-02/STD-02، تصنيف مالي بدون false positive (`vat` في observation)، **286/286 passed**.

## أوامر النشر على السيرفر الخارجي

```bash
bench update --apps omnexa_core,omnexa_accounting,omnexa_alm,omnexa_reporting_compliance,omnexa_fixed_assets,erpgenex_property_mgmt,omnexa_engineering_consulting
bench --site SITE migrate
bench --site SITE clear-cache
bench restart
bench --site SITE execute omnexa_core.omnexa_core.report_print.link_reports.link_erpgenex_report_print_assets
bench --site SITE execute omnexa_core.omnexa_core.report_print.infer_report_filters.sync_all_erpgenex_report_json_filters
python3 scripts/ops/audit_reports_print_checklist.py --merge
```

## ملاحظات (لا تكسر ETA)

- **omnexa_einvoice** — لم يُعاد كتابة Python (مجمد).
- **IFRS 10** — إزالة intercompany مبسطة في Consolidated FS (ليست مصفوفة كاملة).
- **عمود عربي GL** — على التقارير المالية الرئيسية فقط.
- **10 تطبيقات** بدون تقارير — موثقة في `apps_waived_no_reports`.

## الملفات المرجعية

- `Docs/2026-05-20_GLOBAL_REPORTS_AUDIT/REPORTS_PRINT_AUDIT_CHECKLIST.json`
- `scripts/ops/audit_reports_print_checklist.py`
- `scripts/ops/deploy_report_print_html.py`
- `apps/omnexa_core/omnexa_core/omnexa_core/report_print/`
