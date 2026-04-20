# ErpGenex — وصف النظام الشامل وتقييم مواءمة المعايير العالمية

**الإصدار:** 1.0  
**آخر تحديث للبيانات:** بناءً على محتوى الـ bench الحالي (`sites/apps.txt` + `hooks.py` لكل تطبيق).  
**ملاحظة جوهرية:** هذا المستند **وصفي وهندسي**. التقييم أدناه يعبّر عن **مواءمة تصميمية ووظيفية** مع ممارسات أنظمة ERP العالمية (SAP S/4HANA، Oracle Fusion، Microsoft Dynamics 365، Odoo Enterprise) ولا يُعد شهادة تدقيق خارجية (SOC، ISO 27001، إلخ) ما لم تُجرَ عمليات اعتماد منفصلة.

---

## 1. الهوية والغرض

**ErpGenex** منصة ERP مبنية على **Frappe Framework** (Python، MariaDB، Redis، JavaScript) وتُوزَّع كحزم تطبيقات (`apps`) تحت علامة **Omnexa / ErpGenEx**. الهدف: تغطية **محاسبة ومالية وتشغيل وقطاعات عمودية** مع طبقات مشتركة (عميل، ائتمان، تقارير، ذكاء، امتثال محلي مثل الفاتورة الإلكترونية في مصر).

---

## 2. البنية التقنية للمنصة

| الطبقة | المكوّن | الدور |
|--------|---------|--------|
| منصة التشغيل | **Frappe** | إطار الويب، Desk، DocTypes، الصلاحيات، الجدولة، الـ API |
| نواة المنتج | **omnexa_core** | منصة ErpGenex: ترخيص، سوق تطبيقات، تخطيط مكاتب عمل، تكاملات، بوابة تصميم Desk |
| محاسبة أساسية | **omnexa_accounting** | محاسبة مزدوجة القيد ضمن نموذج ErpGenex |
| محركات مشتركة | **omnexa_finance_engine**, **omnexa_credit_engine**, **omnexa_customer_core** | خدمات مالية وائتمان وعميل موحّدة للقطاعات |
| امتثال وتقارير | **omnexa_reporting_compliance**, **omnexa_einvoice**, **omnexa_statutory_audit** | تقارير، امتثال، فوترة إلكترونية مصر |
| قطاعات عمودية | بقية تطبيقات `omnexa_*` | صناعات، خدمات، رعاية صحية، تمويل، إلخ |
| تجربة المستخدم | **erpgenex_theme_0426**, **omnexa_theme_manager** | سمة Desk ومزوّد تبديل السمات |
| ذكاء وتشغيل | **omnexa_intelligence_core**, **omnexa_setup_intelligence** | إشارات، توصيات، تحليل حالة الإعداد |
| تجربة الويب العامة | **omnexa_experience** | كتالوج، حجز، واجهات عامة حسب الوصف |
| حماية البيانات | **omnexa_backup** | جدولة نسخ احتياطي (محلي، FTP، Drive، بريد) |

**ملاحظة على هذا الـ bench:** قائمة `apps.txt` لا تتضمن **ERPNext** كحزمة مستقلة؛ التطبيقات المذكورة هنا هي ما يُثبَّت فعلياً في البيئة المرجعية للتوثيق.

---

## 3. جدول التطبيقات المثبتة (حسب `sites/apps.txt`)

| # | المعرف (`app_name`) | العنوان المعروض | الوصف المختصر |
|---|---------------------|------------------|----------------|
| 1 | frappe | Frappe Framework | إطار ويب كامل (Python، JS، MariaDB، Redis، Node) |
| 2 | omnexa_setup_intelligence | Omnexa Setup Intelligence | محلل حالة إعداد حي وقوائم تحقق ديناميكية |
| 3 | omnexa_reporting_compliance | ErpGenEx — Reporting Compliance | خدمات تقارير وامتثال مشتركة |
| 4 | omnexa_construction | ErpGenEx — Construction | قطاع الإنشاءات |
| 5 | omnexa_healthcare | ErpGenEx — Healthcare | قطاع الرعاية الصحية |
| 6 | omnexa_projects_pm | ErpGenEx — Projects PM | إدارة مشاريع |
| 7 | omnexa_statutory_audit | ErpGenEx — Statutory Audit | تدقيق قانوني / statutory |
| 8 | omnexa_vehicle_finance | ErpGenEx — Vehicle Finance | تمويل مركبات |
| 9 | omnexa_engineering_consulting | ErpGenEx — Engineering Consulting | استشارات هندسية |
| 10 | omnexa_leasing_finance | ErpGenEx — Leasing Finance | تمويل إيجاري |
| 11 | omnexa_finance_engine | ErpGenEx — Finance Engine | محرك مالي مشترك |
| 12 | omnexa_trading | ErpGenEx — Trading | تجارة ونقاط بيع |
| 13 | omnexa_einvoice | ErpGenEx — E-Invoice | تكامل الفاتورة والإيصال الإلكترونيين (مصر) |
| 14 | omnexa_restaurant | Omnexa Restaurant | مطاعم ومقاهي |
| 15 | omnexa_education | ErpGenEx — Education | تعليم |
| 16 | omnexa_theme_manager | Omnexa Theme Manager | رفع واستيراد وتبديل سمات Desk |
| 17 | erpgenex_theme_0426 | ERPGenEx Theme 0426 | سمة Desk مؤسسية (0426) |
| 18 | omnexa_factoring | ErpGenEx — Factoring | فوترة وتخصيم |
| 19 | omnexa_car_rental | Omnexa Car Rental | تأجير سيارات وأساطيل |
| 20 | omnexa_customer_core | ErpGenEx — Customer Core | نواة عميل مشتركة |
| 21 | omnexa_services | ErpGenEx — Services | قطاع الخدمات |
| 22 | omnexa_consumer_finance | ErpGenEx — Consumer Finance | تمويل استهلاكي |
| 23 | omnexa_alm | ErpGenEx — ALM | إدارة الأصول والخصوم ALM |
| 24 | omnexa_agriculture | ErpGenEx — Agriculture | زراعة |
| 25 | omnexa_mortgage_finance | ErpGenEx — Mortgage Finance | تمويل عقاري |
| 26 | omnexa_experience | ErpGenEx — Experience | ويب عام، كتالوج، دفع، حجز |
| 27 | omnexa_intelligence_core | Omnexa Intelligence Core | إشارات، تنبؤات، توصيات، مخاطر، معايير |
| 28 | omnexa_credit_engine | ErpGenEx — Credit Engine | محرك ائتمان مشترك |
| 29 | omnexa_tourism | ErpGenEx — Tourism | سياحة |
| 30 | omnexa_hr | ErpGenEx — HR | موارد بشرية (نواة مجانية حسب الوصف) |
| 31 | omnexa_fixed_assets | ErpGenEx — Fixed Assets | أصول ثابتة (IAS 16 / IFRS نموذج التكلفة) |
| 32 | omnexa_accounting | ErpGenEx — Accounting | محاسبة مزدوجة القيد لـ ErpGenEx |
| 33 | omnexa_manufacturing | ErpGenEx — Manufacturing | تصنيع |
| 34 | omnexa_core | ERPGENEX — Core | منصة ErpGenex الأساسية |
| 35 | omnexa_credit_risk | ErpGenEx — Credit Risk | مخاطر ائتمان و ORR |
| 36 | omnexa_operational_risk | ErpGenEx — Operational Risk | مخاطر تشغيلية |
| 37 | omnexa_sme_retail_finance | ErpGenEx — SME Retail Finance | تمويل SME وتجزئة |
| 38 | omnexa_backup | ERPGENEX — Backup | نسخ احتياطي مجدول متعدد الوجهات |

**المجموع في القائمة:** 38 تطبيقاً (يشمل **frappe** كأساس).

---

## 4. تجميع منطقي للتطبيقات (للعرض التنظيمي وليس تبعية تثبيت)

- **النواة والتشغيل:** `omnexa_core`, `omnexa_backup`, `omnexa_setup_intelligence`  
- **المحاسبة والأصول:** `omnexa_accounting`, `omnexa_fixed_assets`  
- **المحركات المشتركة:** `omnexa_finance_engine`, `omnexa_credit_engine`, `omnexa_customer_core`, `omnexa_reporting_compliance`  
- **التمويل والمخاطر:** `omnexa_consumer_finance`, `omnexa_vehicle_finance`, `omnexa_mortgage_finance`, `omnexa_leasing_finance`, `omnexa_sme_retail_finance`, `omnexa_factoring`, `omnexa_alm`, `omnexa_credit_risk`, `omnexa_operational_risk`  
- **القطاعات التشغيلية:** `omnexa_manufacturing`, `omnexa_trading`, `omnexa_services`, `omnexa_projects_pm`, `omnexa_construction`, `omnexa_engineering_consulting`, `omnexa_agriculture`, `omnexa_healthcare`, `omnexa_education`, `omnexa_tourism`, `omnexa_restaurant`, `omnexa_car_rental`  
- **الامتثال والتدقيق:** `omnexa_einvoice`, `omnexa_statutory_audit`  
- **الذكاء:** `omnexa_intelligence_core`  
- **التجربة والواجهة:** `omnexa_experience`, `omnexa_theme_manager`, `erpgenex_theme_0426`  

---

## 5. تقييم مواءمة المعايير العالمية (إطار مرجعي)

يُقيَّم كل محور من **1** (ضعيف) إلى **5** (قريب جداً من ممارسات قادة السوق)، مع تعليق موجز. الأرقام **تقديرية** تعكس البنية والوثائق الظاهرة في المستودع وليست نتيجة اختبار حمولة أو تدقيق أمني شامل.

### 5.1 الهندسة المعمارية والتعددية (Modularity)

| المعيار | الدرجة | ملاحظة |
|---------|--------|--------|
| فصل التطبيقات حسب مجال (bounded contexts) | **5** | تطبيقات عمودية ومحركات مشتركة واضحة |
| إمكانية التوسع عبر تطبيقات جديدة | **5** | نموذج Frappe + hooks + marketplace في `omnexa_core` |
| تكرار منطقي محتمل بين عموديات | **3** | يتطلب حوكمة مستمرة لتجنب ازدواجية |

**متوسط تقريبي:** **4.3 / 5**

### 5.2 المحاسبة والامتثال المالي

| المعيار | الدرجة | ملاحظة |
|---------|--------|--------|
| محاسبة مزدوجة ومسار تدقيق | **4** | `omnexa_accounting` + تقارير امتثال |
| معايير دولية للأصول | **4** | IFRS / IAS 16 مذكورة في وصف الأصول الثابتة |
| فوترة إلكترونية محلية | **4** | `omnexa_einvoice` — حسب السوق (مصر) |

**متوسط تقريبي:** **4 / 5**

### 5.3 إدارة المخاطر والتمويل

| المعيار | الدرجة | ملاحظة |
|---------|--------|--------|
| تغطية عموديات تمويل متعددة | **5** | مجموعة واسعة من منتجات التمويل |
| عمق مقارنة بأنظمة مصرفية متخصصة | **3** | يعتمد على نضج كل عمودي واختبار السيناريوهات |

**متوسط تقريبي:** **4 / 5**

### 5.4 التشغيل والقطاعات (HR، مشاريع، تصنيع، إلخ)

| المعيار | الدرجة | ملاحظة |
|---------|--------|--------|
| تغطية قطاعية عريضة | **5** | من زراعة إلى صحة إلى مطاعم |
| عمق كل قطاع مقابل حلول متخصصة | **3–4** | يختلف حسب التطبيق؛ يحتاج خارطة نضج لكل عمودي |

**متوسط تقريبي:** **4 / 5**

### 5.5 الذكاء والتحليلات

| المعيار | الدرجة | ملاحظة |
|---------|--------|--------|
| وجود طبقة intelligence مركزية | **4** | `omnexa_intelligence_core` |
| نضج ML/AI قابل للمقارنة بمنصات تحليلات رائدة | **3** | يعتمد على البيانات والنماذج المفعّلة فعلياً |

**متوسط تقريبي:** **3.5 / 5**

### 5.6 تجربة المستخدم والتصميم المؤسسي

| المعيار | الدرجة | ملاحظة |
|---------|--------|--------|
| سمة وتخصيص Desk | **4** | ثيم + مدير سمات |
| نظام تصميم موحّد للمعاملات | **3–4** | جارٍ التنفيذ عبر `docs/design-system` و CSS/JS العالمي في `omnexa_core` |

**متوسط تقريبي:** **3.7 / 5**

### 5.7 الأمن، الاستمرارية، والعمليات

| المعيار | الدرجة | ملاحظة |
|---------|--------|--------|
| نسخ احتياطي متعدد الوجهات | **4** | `omnexa_backup` |
| ترخيص وبوابات طلب | **4** | `license_gate` في `omnexa_core` |
| SOC2 / ISO كوثائق جاهزة | **غير مذكور** | يتطلب برنامج اعتماد منفصل |

**متوسط تقريبي:** **4 / 5** (مع تحفظ على الاعتمادات الرسمية)

### 5.8 الخلاصة التجميعية (تقديرية)

| المحور | وزن مقترح | متوسط المحور |
|--------|------------|--------------|
| الهندسة | 20% | 4.3 |
| محاسبة وامتثال | 20% | 4.0 |
| تمويل ومخاطر | 15% | 4.0 |
| قطاعات تشغيل | 20% | 4.0 |
| ذكاء وتحليلات | 10% | 3.5 |
| UX مؤسسي | 10% | 3.7 |
| أمن واستمرارية | 5% | 4.0 |

**المتوسط المرجح التقريبي:** **~4.0 / 5** كـ **مواءمة مع ممارسات ERP العالمية** على مستوى التصميم والتغطية الوظيفية، مع فجوة طبيعية في **الاعتمادات الرسمية** و**عمق كل عمودي** حتى تُستكمل خرائط نضج واختبارات قبول لكل سوق.

---

## 6. مؤشرات للوصول إلى «أعلى تقييم عالمي» (خارطة طريق)

1. **وثائق لكل عمودي:** نطاق ISO/المعايير المستهدفة، سيناريوهات قبول، فصل «جاهز للإنتاج» عن «تجريبي».  
2. **اختبارات تلقائية واختبارات قبول مستخدم** لمسارات المعاملات الحرجة.  
3. **إكمال نظام التصميم** على كل الشاشات الحرجة (انظر `docs/design-system/`).  
4. **برنامج أمن وامتثال:** سياسات بيانات، تدقيق صلاحيات، سجلات تدقيق (يتماشى مع توقعات العملاء المؤسسيين).  
5. **أداء وقابلية التوسع:** اختبار حمل، فهرسة قواعد البيانات، مراقبة للإنتاج.

---

## 7. مراجع داخلية

- [نظام التصميم — الخطة والتشيكليست](./design-system/README.md)  
- [رموز التصميم](./design-system/TOKENS.md)

---

**صيانة المستند:** عند إضافة/إزالة تطبيق من `sites/apps.txt`، حدّث الجدول في القسم 3 والتجميع في القسم 4، وراجع درجات القسم 5 إذا تغيّر نطاق المنتج جوهرياً.
