# Bench: تنزيل التطبيقات الجديدة مع `omnexa_core`  
# Bench: installing new apps alongside `omnexa_core`

**الغرض / Purpose:** ضبط أسلوب واحد لتنزيل أي تطبيق ErpGenEx جديد بحيث يُثبَّت **النواة أولاً** ثم باقي التطبيقات، وتجنّب أخطاء `required_apps` وترتيب الترحيل.

---

## 1) ترتيب `apps.txt` الموصى به

1. **`frappe`** — إطار العمل (إلزامي).  
2. **`omnexa_core`** — منصّة ErpGenEx المشتركة (يجب أن يسبق معظم تطبيقات `omnexa_*` الأخرى).  
3. بقية التطبيقات حسب الاعتماديات (مثلاً `omnexa_projects_pm` قبل تطبيقات تعتمد عليه في `required_apps`).

على مستودع الـ bench، حافظ على ملف `sites/apps.txt` بهذا المنطق بعد كل `bench get-app`.

**Recommended `apps.txt` order**

1. `frappe`  
2. `omnexa_core`  
3. Other apps by dependency (e.g. `omnexa_projects_pm` before apps that list it in `required_apps`).

---

## 2) أمر تنزيل قياسي لأي تطبيق جديد من GitHub

المنظمة: **`ErpGenex`** — الفرع الافتراضي للتطوير: **`develop`** (ما لم يُحدَّد غير ذلك).

```bash
cd /path/to/frappe-bench

# 1) النواة أولاً إن لم تكن موجودة
bench get-app https://github.com/ErpGenex/omnexa_core.git --branch develop

# 2) التطبيق الجديد (استبدل APP_NAME)
bench get-app https://github.com/ErpGenex/APP_NAME.git --branch develop

# 3) أضف اسم المجلد إلى sites/apps.txt بالترتيب الصحيح

# 4) تثبيت على الموقع
bench --site <site> install-app APP_NAME
bench --site <site> migrate
bench build --app APP_NAME
```

للتطبيقات التي تعتمد على النواة، ضع في **`hooks.py`**:

```python
required_apps = ["omnexa_core"]  # وأي تبعيات أخرى (مثل omnexa_projects_pm)
```

---

## 3) تطبيقات الاستخراج (Phase E) مثل `omnexa_eng_*`

هذه التطبيقات غالباً **`required_apps = ["omnexa_engineering_consulting"]`** أو تعتمد على النواة عبر التطبيق العمودي. تنزيلها:

```bash
bench get-app https://github.com/ErpGenex/omnexa_eng_workflow_engine.git --branch develop
# … ثم install-app حسب الحاجة على كل موقع
```

---

## 4) التحقق السريع بعد التنزيل

```bash
bench --site <site> list-apps
bench --site <site> migrate
bench run-tests --app omnexa_core   # اختياري
```

---

## 5) ما لا يغطيه هذا المستند

- مفاتيح SSH/Git على جهاز المطوّر، وصول CI، أو سياسات الفريق — إعداد بيئة خارج نطاق الكود.  
- إصدارات الإنتاج قد تستخدم فرعاً غير `develop` — يُحدَّد لكل إصدار.

**مرتبط بـ:** [README.md](../README.md) في `omnexa_core`.
