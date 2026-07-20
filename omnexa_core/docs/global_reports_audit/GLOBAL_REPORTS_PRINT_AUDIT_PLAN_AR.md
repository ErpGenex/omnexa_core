# خطة التدقيق والتحديث الشاملة لتقارير ErpGenEx

**التاريخ:** 2026-05-20  
**النطاق:** 46 تطبيقاً (بدون frappe) · **277** تقرير Script Report  
**التشيكليست الحي:** [REPORTS_PRINT_AUDIT_CHECKLIST.json](./REPORTS_PRINT_AUDIT_CHECKLIST.json)  
**المولّد الآلي:** `python3 scripts/ops/audit_reports_print_checklist.py [--merge]`

---

## 1) ملخص تنفيذي

| المؤشر | القيمة |
|--------|--------|
| إجمالي التقارير المثبتة | **277** |
| تطبيقات بها تقارير | **36** |
| تطبيقات بدون تقارير (متعمد/بنية) | **10** |
| نوع التقرير | **100% Script Report** |
| ربط Print Format على مستوى Report | **0%** (فجوة نظامية) |
| نظام طباعة موحّد موجود | **نعم** — `omnexa_core.global_print_design` |
| تقارير ناقصة في الكتالوج | **10** (انظر `missing_reports_catalog`) |

**الاستنتاج:** منطق التقارير والحقول **قوي في المحاسبة والأصول**، لكن **طباعة PDF/تصدير** غير موصولة بكل تقرير. المعيار الدولي مطبّق جزئياً عبر ضوابط التشغيل وليس عبر قوالب طباعة لكل تقرير.

---

## 2) إطار المعايير الدولية (مرجع التدقيق)

### 2.1 محاسبة وقوائم مالية

| المعيار | تطبيق في ErpGenEx | تقارير مرتبطة |
|---------|-------------------|---------------|
| **IAS 1** — عرض القوائم | ضوابط فترة + هيكل حسابات | Trial Balance, Balance Sheet, Income Statement |
| **IAS 7** — تدفقات نقدية | تقارير cash flow structured/indirect | Cash Flow * |
| **IAS 21** — عملات | حقول Currency في الأعمدة | GL, AR/AP aging, PMC rent roll |
| **IFRS 16** — عقود إيجار | PMC Lease Liability Schedule | property_mgmt |
| **IAS 16** — أصول ثابتة | سجل إهلاك، NBV، تأمين | fixed_assets (29 تقرير) |

مرجع: `Docs/OLDDOC/docs/Docs/Accounting_International_Reporting_Standards_MVP.md`

### 2.2 تدقيق ومراجعة

| المعيار | المتطلب |
|---------|----------|
| **ISA 230** | حفظ working papers |
| **ISA 700/705** | فصل مسودة عن رأي نهائي |
| **إخلاء مسؤولية** | كل مخرجات audit = artifact وليست رأياً قانونياً |

مرجع: `Docs/OLDDOC/docs/Docs/Statutory_Audit_Legal_Review_Report_Output_Disclaimer_MVP.md`

### 2.3 تنظيمي / ALM

| المعيار | المتطلب |
|---------|----------|
| **CBE / ALM** | سلم سيولة، IRRBB، stress |
| **BCBS 239** | بيانات قابلة للتدقيق + افتراضات محفوظة |

مرجع: `Docs/OLDDOC/docs/Docs/Fintech_ALM_Liquidity_IRRBB_Stress_and_CBE_Reports_MVP.md`

### 2.4 تشغيلي / قطاعي

| المعيار | قطاع |
|---------|------|
| **RICS / IPMS** | عقارات — rent roll, occupancy |
| **ISO 55000** | صيانة وأصول |
| **POS Z-Report** | تجزئة — تسوية وردية |

---

## 3) أبعاد التدقيق (16 بُعداً)

يُسجَّل لكل تقرير في JSON تحت `gaps[]`:

| ID | المجال | الوصف |
|----|--------|--------|
| PRINT-01 | طباعة | Print Format مخصص للتقرير (Jinja) |
| PRINT-02 | طباعة | Letter Head (شركة + ERPGENEX) |
| PRINT-03 | طباعة | A4، هوامش، ألوان الطباعة |
| PRINT-04 | طباعة | ترقيم صفحات + وقت الطباعة |
| PRINT-05 | طباعة | RTL عربي + خط Cairo |
| FIELD-01 | حقول | فلتر company إلزامي |
| FIELD-02 | حقول | فترة from/to أو as-of |
| FIELD-03 | حقول | أعمدة Currency |
| FIELD-04 | حقول | مجاميع / report_summary |
| FIELD-05 | حقول | فرع / consolidation |
| FIELD-06 | حقول | ترجمة `_()` أو أعمدة EN/AR |
| FIELD-07 | حقول | filters في JSON |
| FIELD-08 | حقول | ليس stub `return [], []` |
| STD-01 | معيار | ربط IAS/IFRS |
| STD-02 | معيار | إخلاء مسؤولية audit |
| STD-03 | معيار | قالب تنظيمي |
| STD-04 | معيار | KPI قطاعي |

---

## 4) نتائج الفحص التلقائي (عينة)

### نقاط قوة

- **omnexa_accounting (53):** Trial Balance, GL, AR/AP aging — company + فترة + Currency + branch.
- **omnexa_fixed_assets (29):** تغطية دورة حياة الأصل + تأمين + فندق.
- **erpgenex_property_mgmt:** PMC Rent Roll — company, as_of, aging buckets, currency.
- **omnexa_nursery:** نموذج ثنائي اللغة (`full_name_en` / `full_name_ar`).

### فجوات نظامية (كل التقارير)

1. **PRINT-01 / PRINT-02:** لا `print_format` ولا `letter_head` على سجل Report.
2. **FIELD-07:** أغلب التقارير `filters: []` في JSON — الفلاتر في Python فقط.
3. **تكرار مسارات:** بعض التطبيقات المالية تكرر `report/` في جذر التطبيق وداخل module.
4. **10 تطبيقات بلا تقارير:** theme, backup, n8n, intelligence, eng_* — توثيق أو إضافة governance report.

### تقارير ناقصة (يجب إضافتها)

| ID | التطبيق | التقرير | المعيار |
|----|---------|---------|---------|
| MISS-PMC-01 | property_mgmt | PMC Rent Aging | IPMS |
| MISS-ALM-01 | alm | ALM Liquidity Gap Ladder | CBE |
| MISS-ALM-02 | alm | IRRBB Sensitivity Summary | BCBS |
| MISS-ACC-01 | accounting | Notes to Financial Statements | IAS 1 |
| MISS-ACC-02 | accounting | Consolidated Financial Statements | IFRS 10 |
| MISS-AUD-01 | statutory_audit | Audit Working Paper Pack | ISA 230 |
| MISS-FA-01 | fixed_assets | IAS 16 Disclosure Schedule | IAS 16 |
| MISS-HR-01 | hr | Payroll Statutory Deductions | محلي |
| MISS-TRD-01 | trading | POS Z-Report Reconciliation | POS MVP |

الحالة الكاملة في `missing_reports_catalog` داخل JSON.

---

## 5) خطة التحديث على موجات

### الموجة W1 — محاسبة وتدقيق (حتى 2026-06-15)

**التطبيقات:** `omnexa_accounting`, `omnexa_statutory_audit`, `omnexa_reporting_compliance`

| # | مهمة | مخرج |
|---|------|------|
| W1-1 | وحدة `omnexa_core.report_print` — ربط Print Format + Letter Head لكل Report | API + patch |
| W1-2 | قوالب Jinja: Trial Balance, Balance Sheet, Income Statement, GL | 4 Print Formats |
| W1-3 | إخلاء مسؤولية ISA في تذييل تقارير audit | HTML block |
| W1-4 | إضافة MISS-ACC-01, MISS-ACC-02 | Script Reports |
| W1-5 | إعلان filters في JSON للتقارير المالية الـ Top 20 | JSON sync |

### الموجة W2 — أصول وعقارات وALM (حتى 2026-07-01)

**التطبيقات:** `omnexa_fixed_assets`, `erpgenex_property_mgmt`, `omnexa_alm`

| # | مهمة |
|---|------|
| W2-1 | MISS-PMC-01 Rent Aging + تحسين Rent Roll print |
| W2-2 | MISS-FA-01 IAS 16 disclosure |
| W2-3 | MISS-ALM-01/02 تقارير تنظيمية |
| W2-4 | Asset Insurance reports — print + AR labels |

### الموجة W3 — HR، فوترة، تجزئة (حتى 2026-07-15)

| # | مهمة |
|---|------|
| W3-1 | Payroll register print + MISS-HR-01 |
| W3-2 | ربط print formats einvoice (موجود) بتقارير omnexa_einvoice |
| W3-3 | MISS-TRD-01 Z-Report reconciliation |

### الموجة W4 — باقي القطاعات (حتى 2026-08-15)

- 27 تطبيقاً قطاعياً: تطبيق قالب طباعة موحّد + مراجعة FIELD-* + `ar.csv`.
- تطبيقات بدون تقارير: قرار «لا يلزم» أو تقرير governance واحد.

---

## 6) هندسة الطباعة المقترحة (حل جذري)

```
omnexa_core/
  report_print/
    __init__.py
    link_report_print_format.py   # يربط كل Report بـ ERPGENEX Report - {name}
    templates/
      report_base.html            # extends global CSS
      financial_table.html
      audit_disclaimer.html
```

**سلوك:**

1. عند `migrate` / `after_migrate`: لكل Report عام → إنشاء Print Format `ERPGENEX Report - {Report Name}`.
2. زر Print في Query Report يستخدم القالب تلقائياً.
3. Letter Head: شركة المستخدم + تذييل ERPGENEX Global.
4. تقارير audit تضيف snippet `audit_disclaimer.html`.

**لا يمس:** تكامل مصر ETA / ZATCA المجمد — فقط تقارير omnexa_einvoice العامة.

---

## 7) تشيكليست حي — طريقة التحديث

### توليد / تحديث من الكود

```bash
cd ~/frappe-bench
python3 scripts/ops/audit_reports_print_checklist.py          # مسح كامل
python3 scripts/ops/audit_reports_print_checklist.py --merge  # يحفظ audit_status و notes اليدوية
```

### عند إضافة تقرير جديد

1. أنشئ `report/{name}/{name}.json|py|js`.
2. شغّل المولّد أعلاه — يُضاف التقرير تلقائياً تحت `apps.{app}.reports`.
3. راجع `gaps[]` — صفّرها تدريجياً حتى `audit_status: "passed"`.
4. إن كان التقرير **مطلوباً بالمعيار** وغير موجود: أضف صفاً في `missing_reports_catalog` ثم أنشئه وغيّر `status` إلى `implemented`.

### حقول حالة كل تقرير في JSON

```json
{
  "audit_status": "pending | in_review | passed | waived",
  "gaps": ["PRINT-01", "FIELD-03"],
  "notes": "مراجعة UAT 2026-06-01",
  "assigned_to": "optional"
}
```

### ملخص التقدم (يُحدَّث من السكربت)

راجع `summary` في JSON:

- `total_reports`
- `pending`
- `missing_catalog_count`

---

## 8) توزيع التقارير حسب التطبيق (مرجع سريع)

| التطبيق | العدد | الموجة |
|---------|------:|--------|
| omnexa_accounting | 53 | W1 |
| omnexa_fixed_assets | 29 | W2 |
| omnexa_tourism | 16 | W4 |
| omnexa_engineering_consulting | 14 | W4 |
| omnexa_nursery | 11 | W4 |
| omnexa_hr | 9 | W3 |
| omnexa_manufacturing | 9 | W4 |
| omnexa_car_rental | 8 | W4 |
| omnexa_trading | 8 | W3 |
| erpgenex_property_mgmt | 4 | W2 |
| omnexa_reporting_compliance | 4 | W1 |
| omnexa_statutory_audit | 3 | W1 |
| … | … | W4 |

التفاصيل الكاملة لكل تقرير (278 سطر تطبيق × تقارير) في **JSON فقط** لتفادي تضخم Markdown.

---

## 9) معايير القبول (Definition of Done) لتقرير واحد

- [ ] `audit_status = passed` في JSON
- [ ] جميع gaps ذات أولوية **critical/high** مغلقة أو `waived` مع تبرير في `notes`
- [ ] Print PDF: A4، header شركة، footer ERPGENEX، ترقيم صفحات
- [ ] فلاتر: company + period (+ branch إن وُجد)
- [ ] أعمدة مالية: Currency حيث يلزم
- [ ] `_()` أو EN/AR للعناوين
- [ ] اختبار وحدة أو execute على site UAT ببيانات حقيقية
- [ ] `ar.csv` محدّث للتطبيق
- [ ] مُدرج في Workspace المناسب

---

## 10) الخطوة التالية الموصى بها

1. **الموافقة على الموجات W1–W4.**
2. تنفيذ **W1-1** (وحدة ربط الطباعة) — يغلق PRINT-01/02 لـ 277 تقرير دفعة واحدة.
3. مراجعة يدوية لـ **Top 30** تقريراً (محاسبة + PMC + FA) ضد المعايير.
4. إضافة **10 تقارير ناقصة** من الكتالوج.

---

*آخر توليد للتشيكليست: شغّل `audit_reports_print_checklist.py` — التاريخ في `meta.generated_on`.*
