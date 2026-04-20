# اختبار الترخيص والتجربة — ErpGenex (Omnexa)

## 1. لماذا لا يظهر «تفعيل المفتاح» في الماركت بليس؟

إذا كان في **`site_config.json`**:

```json
"omnexa_marketplace_bundle_mode": 1
```

فكل التطبيقات تُعرَض كـ **`licensed_bundle`** ويُخفى زر التفعيل/الشراء.

### لرؤية الحالة الحقيقية (تجربة، ترخيص، انتهاء)

أضف أحد الخيارين:

```json
"omnexa_marketplace_show_real_license_status": 1
```

أو فعّل **`developer_mode`** على الموقع (مناسب لبيئة التطوير فقط).

بعدها أعد تحميل صفحة **ErpGenEx Marketplace** — ستظهر أعمدة الحالة الفعلية وأزرار **Activate Key** للتطبيقات غير المجانية حسب المنطق الحالي.

---

## 2. مدة التجربة

بدون مفتاح JWT صالح، التطبيقات **غير المجانية** تدخل في **تجربة `TRIAL_DAYS`** (افتراضياً **7 أيام**) من أول تحقق يُسجَّل لكل تطبيق.

القيمة في الكود: `omnexa_core/omnexa_core/omnexa_license.py` → `TRIAL_DAYS`.

---

## 3. مفتاح مطوّر للاختبار (بدون JWT)

يُخزَّن المفتاح في **`omnexa_licenses_json`** عبر «Activate Key» أو `site_config` → `omnexa_licenses`.

### أ) القيمة الافتراضية في الكود (للتطوير فقط)

سلسلة ثابتة في الكود: **`26101975sayed`** (انظر `DEVELOPER_BYPASS_CODE` في `omnexa_license.py`).

عند وضعها كقيمة ترخيص لتطبيق **`omnexa_*`**، يُعامل التطبيق كـ **`licensed_dev_override`** طالما لم تُستبدل بمنطق آخر.

> **تحذير أمني:** غيّر هذه القيمة في الإنتاج أو اعتمد فقط على `omnexa_developer_license_keys` في الإعدادات.

### ب) إعدادات أوضح للإنتاج

في **`site_config.json`**:

```json
"omnexa_developer_license_keys": ["your-secret-one", "your-secret-two"]
```

أو مفتاح واحد:

```json
"omnexa_developer_bypass_code": "your-secret"
```

أي قيمة تطابق المفتاح المُدخل في «Activate Key» تمنح **`licensed_dev_override`**.

---

## 4. ترخيص JWT حقيقي (زمني)

1. جهّز زوج RSA ووقّع JWT بخوارزمية **RS256** (أو ES256) يتضمن **`exp`** ويفضّل **`app`** = اسم التطبيق (`omnexa_tourism` …).
2. ضع **المفتاح العام** في:

   - `omnexa_license_public_key_pem`، أو  
   - `omnexa_license_public_keys_by_kid` إذا استخدمت **`kid`** في ترويسة JWT.

3. ضع سلسلة JWT (أو مفتاح `ERPGX1-...` حسب التنسيق المدعوم) في `omnexa_licenses` أو عبر واجهة التفعيل.

---

## 5. إلغاء الترخيص من الماركت بليس

لمستخدمي **System Manager**: زر **Revoke / Reset trial** يستدعي `revoke_app_license`:

- إزالة المفتاح المخزّن للتطبيق.
- اختيارياً **إعادة ضبط عدّاد التجربة** ليبدأ أسبوع جديد من «أول لمسة» (للتطبيقات غير المجانية؛ للتطبيقات المجانية يُسمح فقط بإعادة ضبط التجربة إن طُبّق ذلك على الموقع).

بعد الإزالة، مع **`omnexa_license_enforce`**، قد يُمنع استخدام التطبيق حتى يُفعَّل مفتاح جديد أو تعود التجربة حسب السياسة.

---

## 6. مراجع

- `omnexa_core/omnexa_core/omnexa_license.py`
- `omnexa_core/omnexa_core/marketplace.py` (`get_marketplace_catalog`, `revoke_app_license`, `activate_app_license`)
