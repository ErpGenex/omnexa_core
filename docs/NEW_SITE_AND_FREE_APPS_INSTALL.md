# دليل إنشاء موقع جديد وتثبيت تطبيقات ErpGenex المجانية (بالترتيب الملزم)

**الغرض:** إنشاء موقع Frappe جديد على الـ bench وتفعيل كل التطبيقات المعرّفة كـ **مجانية** في `omnexa_core` (`FREE_APPS`) مع احترام ترتيب **`required_apps`** في كل تطبيق حتى لا يفشل `bench install-app`.

**المرجع البرمجي لقائمة المجانية:**  
`omnexa_core/omnexa_core/omnexa_license.py` → `FREE_APPS`  
يمكن إضافة تطبيقات أخرى عبر `site_config`: `omnexa_marketplace_free_apps`.

---

## 1. المتطلبات المسبقة

- Bench يعمل، وقاعدة بيانات MariaDB، Redis، Node، Python حسب إصدار Frappe المستخدم.
- مستودعات التطبيقات موجودة تحت `frappe-bench/apps/` (مثلاً بعد `bench get-app` من GitHub منظمة ErpGenex).
- تنفيذ الأوامر كمستخدم يملك صلاحية كتابة على مجلد الـ bench.

---

## 2. إنشاء الموقع

استبدل `SITE_NAME` باسم النطاق الكامل للموقع (مثل `erp.example.com`).

```bash
cd /path/to/frappe-bench

bench new-site SITE_NAME \
  --db-root-password YOUR_DB_ROOT_PASSWORD \
  --admin-password YOUR_ADMIN_PASSWORD
```

اختياري: تثبيت التطبيقات أثناء الإنشاء (غير موصى به لمجموعة ErpGenex الكبيرة؛ يفضّل التحكم بالترتيب يدوياً كما بالأسفل):

```bash
# بديل: موقع فارغ ثم install-app بالترتيب (الموصى به)
bench new-site SITE_NAME --no-setup-db   # إن كان سير العمل لديكم يستخدم خيارات أخرى، اتبعوا سياسة bench لديكم
```

إن كان `new-site` لديكم بدون `--no-setup-db`، يكفي إنشاء الموقع ثم المتابعة من القسم 4.

---

## 3. إعدادات الموقع الموصى بها (قبل أو بعد التثبيت)

في `sites/SITE_NAME/site_config.json` (أو عبر `bench config set-common-config` للقيم المشتركة):

```json
{
  "omnexa_platform": "erpgenex"
}
```

- بدون `omnexa_platform` = `erpgenex` قد تُرفض التحقق من ترخيص تطبيقات `omnexa_*` غير المجانية؛ التطبيقات المدرجة في `FREE_APPS` تعمل كـ `licensed_free` بغض النظر عند التحقق من المنصة بعد تجاوز فحص المنصة لمسار التطبيقات المجانية — يُنصح بضبط القيمة أعلاه لبيئات ErpGenex الإنتاجية.

لتفعيل رقابة الترخيص على التطبيقات **غير** المجانية (اختياري):

```json
{
  "omnexa_platform": "erpgenex",
  "omnexa_license_enforce": 1
}
```

---

## 4. الترتيب الملزم لتثبيت التطبيقات المجانية على الموقع

الترتيب مبني على **`required_apps`** في `hooks.py` لكل تطبيق. أي انحراف قد يسبب فشل التثبيت أو استيراد نماذج غير مكتمل.

| الترتيب | التطبيق | سبب الترتيب (اعتماديات) |
|--------|---------|---------------------------|
| 1 | `frappe` | مثبت مع الموقع افتراضياً — لا يُعاد تثبيته عادة |
| 2 | `omnexa_core` | نواة ErpGenex؛ مطلوبة لبقية تطبيقات `omnexa_*` |
| 3 | `omnexa_accounting` | يتطلب `omnexa_core` |
| 4 | `omnexa_hr` | يتطلب `omnexa_core` فقط (يمكن تثبيته بعد المحاسبة بأمان) |
| 5 | `omnexa_projects_pm` | يتطلب `omnexa_core` فقط |
| 6 | `omnexa_einvoice` | يتطلب `omnexa_core` فقط |
| 7 | `omnexa_customer_core` | يتطلب `omnexa_core` + `omnexa_accounting` |
| 8 | `omnexa_fixed_assets` | يتطلب `omnexa_core` + `omnexa_accounting` |
| 9 | `omnexa_experience` | يتطلب `omnexa_core` + `omnexa_accounting` |
| 10 | `omnexa_setup_intelligence` | **ليس داخل `FREE_APPS`** لكنه **إلزامي** قبل `omnexa_intelligence_core` (حقل `required_apps` في `omnexa_intelligence_core`) |
| 11 | `omnexa_intelligence_core` | يتطلب `omnexa_setup_intelligence` |
| 12 | `erpgenex_theme_0426` | لا يعرّف `required_apps` على التطبيق؛ يُفضّل بعد `omnexa_core` لضمان تحميل سمات Desk بشكل متسق |

**ملاحظة عن `omnexa_setup_intelligence`:**  
إن أردتم اعتباره «مجانياً» من ناحية الترخيص أيضاً، أضيفوه إلى `omnexa_marketplace_free_apps` في `site_config.json`:

```json
{
  "omnexa_marketplace_free_apps": ["omnexa_setup_intelligence"]
}
```

أو يُرجى تحديث قائمة `FREE_APPS` في الكود لاحقاً لتشمله رسمياً.

---

## 5. أوامر التثبيت (نسخ ولصق)

استبدل `SITE_NAME` ومسار الـ bench:

```bash
cd /path/to/frappe-bench

APPS_ORDER=(
  omnexa_core
  omnexa_accounting
  omnexa_hr
  omnexa_projects_pm
  omnexa_einvoice
  omnexa_customer_core
  omnexa_fixed_assets
  omnexa_experience
  omnexa_setup_intelligence
  omnexa_intelligence_core
  erpgenex_theme_0426
)

for app in "${APPS_ORDER[@]}"; do
  bench --site SITE_NAME install-app "$app"
done

bench --site SITE_NAME migrate
bench build
bench --site SITE_NAME clear-cache
```

- إذا كان التطبيق **غير موجود** على الـ bench، نفّذوا أولاً من جذر الـ bench:  
  `bench get-app https://github.com/ErpGenex/<app>.git`  
  (أو مسار المستودع الفعلي لديكم) **قبل** حلقة `install-app`.

---

## 6. التحقق السريع

```bash
bench --site SITE_NAME list-apps
```

تأكدوا أن كل التطبيقات أعلاه تظهر في القائمة.

داخل Desk: افتحوا **ErpGenex Marketplace** وتحققوا من أن حالة الترخيص للتطبيقات المجانية تظهر كـ **licensed_free** (أو ما يعادلها في الواجهة).

---

## 7. أعطال شائعة

| العرض | الإجراء |
|--------|---------|
| فشل `install-app` لـ `omnexa_intelligence_core` | ثبّتوا `omnexa_setup_intelligence` أولاً (الخطوة 10). |
| فشل `omnexa_customer_core` / `fixed_assets` / `experience` | ثبّتوا `omnexa_accounting` بعد `omnexa_core`. |
| رسالة منصة غير ErpGenex | عيّنوا `omnexa_platform` = `erpgenex` في `site_config.json`. |
| أصول Desk لا تتغير | بعد `erpgenex_theme_0426` نفّذوا `bench build --app erpgenex_theme_0426` ثم مسح كاش. |

---

## 8. صيانة هذا الدليل

عند تغيير `FREE_APPS` أو `required_apps` في أي تطبيق، حدّثوا جدول القسم 4 ومصفوفة `APPS_ORDER` في القسم 5 في نفس التذكرة أو PR.

---

**مرجع ذي صلة:** [وصف المنصة والتطبيقات](./ERPGENEX_SYSTEM_OVERVIEW.md)
