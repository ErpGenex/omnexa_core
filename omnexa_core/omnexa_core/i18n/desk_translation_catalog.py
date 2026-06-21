# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Global Desk / workspace Arabic labels — familiar ERP & vertical concepts."""

from __future__ import annotations

import re

# Workspace titles & Card Break sections (all verticals)
WORKSPACE_GLOBAL_AR: dict[str, str] = {
	"Finance Group": "المجموعة المالية",
	"Finance Workcenter": "مركز عمل المالية",
	"Accounting": "المحاسبة",
	"E-Invoice": "الفاتورة الإلكترونية",
	"Governance": "الحوكمة",
	"Settings": "الإعدادات",
	"Healthcare": "الرعاية الصحية",
	"Trading": "التجارة",
	"Restaurant": "المطاعم",
	"Manufacturing": "التصنيع",
	"Construction": "المقاولات",
	"HR": "الموارد البشرية",
	"Projects PM": "إدارة المشاريع",
	"Car Rental": "تأجير السيارات",
	"Tourism": "السياحة",
	"Agriculture": "الزراعة",
	"Services": "الخدمات",
	"Education": "التعليم",
	"Fixed Assets": "الأصول الثابتة",
	"Asset Insurance": "تأمين الأصول",
	"Property Management": "إدارة العقارات",
	"RE Development": "التطوير العقاري",
	"RE Marketing": "التسويق العقاري",
	"Engineering Consulting": "الاستشارات الهندسية",
	"CRM": "إدارة العملاء",
	"Audit": "التدقيق",
	"Finance Engine": "محرك التمويل",
	"Credit Engine": "محرك الائتمان",
	"Credit Risk": "مخاطر الائتمان",
	"ALM": "إدارة الأصول والخصوم",
	"Consumer Finance": "التمويل الاستهلاكي",
	"Vehicle Finance": "تمويل المركبات",
	"Mortgage Finance": "التمويل العقاري",
	"Factoring": "التخصيم",
	"SME Retail Finance": "تمويل المنشآت والتجزئة",
	"SME Microfinance": "التمويل متناهي الصغر",
	"Leasing Finance": "التمويل التأجيري",
	"Operational Risk": "المخاطر التشغيلية",
	"Sell": "المبيعات",
	"Buy": "المشتريات",
	"Stock": "المخزون",
	"📊 Dashboards & portals": "📊 لوحات المعلومات والبوابات",
	"📊 Dashboards & Portals": "📊 لوحات المعلومات والبوابات",
	"🏢 Organization": "🏢 التنظيم والإعداد",
	"🏢 Organization & Setup": "🏢 التنظيم والإعداد",
	"🏢 Portfolio": "🏢 المحفظة",
	"📋 Operations": "📋 العمليات",
	"📋 Commercial": "📋 التجاري",
	"🚚 Field operations": "🚚 العمليات الميدانية",
	"💰 Finance & ERP": "💰 المالية · ERP",
	"💰 Billing · Finance · ERP": "💰 الفوترة · المالية · ERP",
	"📈 Reports": "📈 التقارير",
	"📊 Analytics": "📊 التحليلات",
	"🛡️ Compliance": "🛡️ الامتثال",
	"🔗 Integration": "🔗 التكامل",
	"📦 Inventory & Supply": "📦 المخزون والتوريد",
	"👥 HR & Users": "👥 الموارد البشرية والمستخدمون",
	"General Ledger": "دفتر الأستاذ العام",
	"Trial Balance": "ميزان المراجعة",
	"Accounts Receivable": "الذمم المدينة",
	"Accounts Payable": "الذمم الدائنة",
	"Profit and Loss": "الأرباح والخسائر",
	"Balance Sheet": "الميزانية العمومية",
	"Sales Register": "سجل المبيعات",
	"Purchase Register": "سجل المشتريات",
	"Governance Overview": "نظرة عامة على الحوكمة",
	"Customer": "العميل",
	"Supplier": "المورد",
	"Sales Invoice": "فاتورة مبيعات",
	"Purchase Invoice": "فاتورة شراء",
	"Payment Entry": "سند قبض/صرف",
	"Journal Entry": "قيد يومية",
	"GL Account": "حساب GL",
	"Chart of Accounts": "دليل الحسابات",
	"Cost Center": "مركز التكلفة",
	"Company": "الشركة",
	"Branch": "الفرع",
	"Item": "الصنف",
	"Warehouse": "المستودع",
	"Workspaces": "مساحات العمل",
	"Workspace": "مساحة العمل",
	"List": "قائمة",
	"Form": "نموذج",
	"Report": "تقرير",
	"Dashboard": "لوحة معلومات",
	"Desk": "المكتب",
}

_EN_ALLOW = re.compile(
	r"\b(?:FHIR|ICD|SNOMED|DRG|LOINC|HL7|EDI|X12|NPHIES|DICOM|ERP|ALM|CRM|POS|GL|AP|AR|IFRS|ISO|KPI|OTP|SMS|URL|API|JSON|CSV|PDF|SKU|UOM|MRN|ICU|OPD|IPD|ADT|LIS|EMR|MPI|PHI|CDS|CAPA|CSSD|QMS|RCM|NPI|UDI|GS1|WHO|CT|MR|MG|NM|XR|US|OT|HR|PM|SSO|PACS|CAD|EDI)\b"
)


def _has_untranslated_english(text: str) -> bool:
	cleaned = _EN_ALLOW.sub("", text)
	return bool(re.search(r"[A-Za-z]{3,}", cleaned))


def translate_desk_label(text: str) -> str:
	if not text:
		return text
	raw = text.strip()
	if raw in WORKSPACE_GLOBAL_AR:
		return WORKSPACE_GLOBAL_AR[raw]
	if " · " in raw or " / " in raw or " & " in raw:
		sep = " · " if " · " in raw else " / " if " / " in raw else " & "
		parts = [translate_desk_label(p.strip()) for p in raw.split(sep) if p.strip()]
		joined = sep.join(parts)
		if joined != raw and not _has_untranslated_english(joined):
			return joined
	return raw


def build_global_desk_messages(lang: str | None = None) -> dict[str, str]:
	lang = (lang or "en").lower()
	if not lang.startswith("ar"):
		return {}
	messages: dict[str, str] = {}
	for en, ar in WORKSPACE_GLOBAL_AR.items():
		if en and ar and ar != en:
			messages[en] = ar
	return messages
