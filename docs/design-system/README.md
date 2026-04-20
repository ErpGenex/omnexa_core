# ErpGenex Design System — فهرس التوثيق

| الملف | الغرض |
|-------|--------|
| [PLAN.md](./PLAN.md) | مراحل التسليم، طبقة التطبيق العالمي مقابل تخصيص النماذج، معايير النجاح |
| [CHECKLIST.md](./CHECKLIST.md) | تشيكليست مراجعة كل شاشة قبل الاعتماد |
| [TOKENS.md](./TOKENS.md) | مسافات، طباعة، ألوان دلالية متزامنة مع CSS |
| [reference/README.md](./reference/README.md) | مكان وضع المرجع البصري (`sales-invoice-target.png`) |

**التطبيق في الكود:**  
`hooks.py` → `app_include_css`, `app_include_js` للمحسّن العالمي فقط؛ لا يُكرّر في كل تطبيق ما لم يكن تصرفاً استثنائياً.
