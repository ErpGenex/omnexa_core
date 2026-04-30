# Ecosystem 99% Scorecard — 2026-04-30

## ما معنى “وصلنا 99%”؟

نعتبر المنظومة وصلت **99% من أقصى نضج Ecosystem** عندما تتحقق الشروط التالية **على كل التطبيقات** (وليس على 2–3 تطبيقات فقط):

### 1) Platform Standards (إلزامي)
- توحيد UX للتقارير (from/to date defaults + validation + naming conventions)
- Feature flags قياسية لكل engines الثقيلة (scheduler/predictive/monitoring…)
- Permission model موحّد (company/branch row-level + report safety)
- Docs: Deployment + Rollback لكل app enterprise

### 2) Domain Depth لكل تطبيق
- Masters + Transactions + Workflow + Execution + Close
- Automation + Alerts + Exceptions
- Report pack (Register/Summary/Trend/Exceptions/Compliance/Forecast)
- Command Center (KPI payload + workspace links)

### 3) Ops & Observability
- Job health, DLQ/retry, idempotency patterns
- Auditability for major operations
- Performance safety (limits/pagination/background jobs)

### 4) Quality & Migration Safety
- Additive schema only
- Backfill patches لكل derived fields
- Tests: smoke + critical rule + migration test

## النتيجة الحالية (حالة bench الحالية)

### A) Platform
- **Report date-range defaults**: تم بدء توحيدها مركزيًا عبر `omnexa_core` (Desk-level).
- باقي المعايير: موجودة جزئيًا ومتفاوتة بين التطبيقات.

### B) Domain leveling
المنظومة حاليًا قوية جدًا في بعض التطبيقات (Accounting/Core/Fixed Assets)، لكنها **غير متساوية** عبر جميع المجالات.

## Structure-based Baseline (مؤشر هيكلي محافظ)

> هذا المؤشر يقيس “عمق الهيكل” (Doctypes/Reports/Tests/APIs/Tasks/Patches)، وليس correctness التشغيلي.
> الهدف منه تحديد أين تحتاج المنظومة leveling سريع للوصول للـ99%.

أعلى التطبيقات حسب الإشارة الهيكلية:
- `omnexa_accounting` (أعلى تغطية Doctypes/Reports)
- `omnexa_core` (platform + workspaces + tests)
- `omnexa_fixed_assets` (تم رفعه إلى EAM Enterprise)

أضعف التطبيقات (Thin/Bridge/Bootstrap):
- `omnexa_theme_manager`, `omnexa_setup_intelligence`, `omnexa_n8n_bridge`, `omnexa_backup`, `omnexa_user_academy`

## ماذا يلزم للوصول لـ99% عمليًا؟

### المرحلة 1 (Platform Kit) — 1–2 أسابيع
- توحيد report UX بالكامل (تم بدءه)
- إنشاء “Command Center Contract” قياسي لكل app
- إدخال Outbox/DLQ/Retry patterns في core (قالب جاهز)
- إلزام feature flags + scheduler guards + audit logs

### المرحلة 2 (Domain Leveling) — 3–6 أسابيع
لكل app Tier B/C/D:
- إضافة Work Execution model حقيقي
- إضافة Alerting + Exceptions
- إضافة 6–12 تقارير قياسية
- إضافة Workspace links + command center payload
- رفع الاختبارات إلى الحد الأدنى

### المرحلة 3 (Ops & Quality) — 2–4 أسابيع
- Performance tests للأعمال الثقيلة
- migration/backfill tests
- مراقبة jobs وقياسات تشغيل

## مخرجات اليوم (Docs)

- `Docs/2026-04-30/global-app-audit/` (inventory + recommendations + checklist + metrics)
- هذا الملف يحدد شرط 99% وخطوات الوصول.

