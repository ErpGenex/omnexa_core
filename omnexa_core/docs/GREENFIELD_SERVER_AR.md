# سيرفر ErpGenEx جديد — بدون خطوات يدوية إضافية

كل ما يلزم للتقارير والطباعة والفلاتر يُطبَّق **تلقائياً** عند:

```bash
bench --site SITE migrate
```

عبر `omnexa_core.install.after_migrate` → `run_site_hardening_after_app_changes()`:

- طباعة موحدة + Letter Head
- فلاتر JSON للتقارير
- Workspaces، dashboards، branding (حسب الإصدار)

---

## 1) سيرفر إنتاج موجود (تحديث فقط)

```bash
cd ~/frappe-bench
export SITE=your.production.site

bench update --reset
# أو: bench update --apps omnexa_core  (إذا حدّثت omnexa_core فقط)

bench --site $SITE migrate
bench --site $SITE clear-cache
bench restart
```

**لا حاجة** لـ `bench execute` يدوياً بعد `migrate` (ما لم يكن إصدار `omnexa_core` قديماً جداً).

اختياري — تدقيق التقارير:

```bash
python3 apps/omnexa_core/omnexa_core/scripts/ops/audit_reports_print_checklist.py --merge
```

أو السكربت الكامل:

```bash
export SITE=your.production.site
bash apps/omnexa_core/omnexa_core/scripts/ops/deploy_external_server.sh
```

---

## 2) سيرفر / موقع جديد من الصفر

1. تثبيت Frappe bench + Python/Node حسب [Frappe docs](https://frappeframework.com/docs).
2. إنشاء bench وموقع.
3. تثبيت **omnexa_core** فقط على الموقع — يثبّت بقية الـ stack تلقائياً (`install_required_site_apps`):

```bash
bench get-app https://github.com/ErpGenex/omnexa_core
bench --site SITE install-app omnexa_core
```

4. تأكد أن بقية التطبيقات في `sites/apps.txt` (مرجع: `docs/ERPGENEX_STACK_APPS.txt` داخل omnexa_core).

```bash
bench --site SITE migrate
bench build
bench restart
```

---

## 3) ما الموجود داخل repo `omnexa_core`

| المسار | الغرض |
|--------|--------|
| `omnexa_core/report_print/` | قوالب HTML + ربط Letter Head + مزامنة فلاتر |
| `omnexa_core/scripts/ops/` | سكربتات deploy / audit (اختيارية) |
| `omnexa_core/docs/global_reports_audit/` | قائمة التدقيق JSON + MD |
| `omnexa_core/docs/ERPGENEX_STACK_APPS.txt` | قائمة التطبيقات المرجعية |
| `patches/` | ترحيلات DB بعد كل `migrate` |

---

## 4) متغيرات بيئة (اختيارية)

| المتغير | الافتراضي | المعنى |
|---------|-----------|--------|
| `OMNEXA_AUTO_INSTALL_SITE_APPS` | `1` | تثبيت تطبيقات الـ stack على الموقع |
| `OMNEXA_AUTO_GET_APPS` | `1` | `bench get-app` للتطبيقات الناقصة |

---

## 5) تحقق سريع بعد النشر

- Desk → **Trial Balance** أو **Trading Sales Summary** → فلاتر Company / Dates.
- **Menu → Print** → ترويسة ERPGENEX.
- `bench --site SITE execute omnexa_core.omnexa_core.report_print.link_reports.link_erpgenex_report_print_assets`  
  يجب أن يعيد `html_skipped` عالياً (طبيعي بعد أول migrate).

---

**GitHub:** https://github.com/ErpGenex/omnexa_core  
**آخر موجة:** تقارير 286/286 + فلاتر + طباعة موحدة (2026-05-21).
