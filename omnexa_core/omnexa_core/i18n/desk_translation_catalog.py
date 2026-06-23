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
	# --- Real estate vertical (Property Management / RE Development / RE Marketing) ---
	"📊 Dashboards": "📊 لوحات المعلومات",
	"🏢 Portfolio": "🏢 المحفظة العقارية",
	"📋 Leasing": "📋 التأجير",
	"💰 Owner & CAM": "💰 المالك والمصاريف المشتركة",
	"🏗️ Projects": "🏗️ المشاريع",
	"📐 BOQ & inventory": "📐 جدول الكميات والمخزون",
	"✅ Handover": "✅ التسليم",
	"🎯 CRM": "🎯 إدارة العملاء",
	"💰 Commissions": "💰 العمولات",
	"Executive Dashboard": "لوحة المدير التنفيذية",
	"Operating Scenarios": "سيناريوهات التشغيل",
	"Field PWA": "تطبيق الميدان",
	"Sales Portal": "بوابة المبيعات",
	"Property": "عقار",
	"Unit": "وحدة",
	"Management Agreement": "اتفاقية إدارة",
	"Leasing Mandate": "تفويض تأجير",
	"Rental Contract": "عقد إيجار",
	"Rent Billing Run": "تشغيل فوترة الإيجار",
	"Escalation Rule": "قاعدة تصعيد الإيجار",
	"Owner Statement": "كشف حساب المالك",
	"CAM Budget": "ميزانية المصاريف المشتركة",
	"Rent Roll": "سجل الإيجارات",
	"Occupancy": "الإشغال",
	"Rent Aging": "أعمار الإيجارات",
	"IFRS 16 Liability": "التزام الإيجار IFRS 16",
	"Development Project": "مشروع تطوير",
	"Land Parcel": "قطعة أرض",
	"Development Budget": "ميزانية التطوير",
	"BOQ": "جدول الكميات",
	"Unit Inventory": "مخزون الوحدات",
	"Subcontract": "مقاول باطن",
	"Handover Package": "حزمة التسليم",
	"Permit Milestone": "معلم التصريح",
	"Project EV": "القيمة المكتسبة للمشروع",
	"Sales Lead": "عميل محتمل",
	"Unit Reservation": "حجز وحدة",
	"Sales Booking": "حجز بيع",
	"Commission Schedule": "جدول العمولات",
	"Payment Plan Item": "بند خطة السداد",
	"Campaign ROI": "عائد الحملة",
	"Commission Accrual": "استحقاق العمولات",
	"PMC Property": "عقار",
	"PMC Property Unit": "وحدة عقارية",
	"PMC Management Agreement": "اتفاقية إدارة",
	"PMC Leasing Mandate": "تفويض تأجير",
	"PMC Owner Statement": "كشف حساب المالك",
	"PMC Rental Contract Register": "سجل عقود الإيجار",
	"PMC Rent Billing Register": "سجل فوترة الإيجار",
	"PMC Owner Statement Register": "سجل كشوف الملاك",
	"PMC Management Fee Summary": "ملخص رسوم الإدارة",
	"PMC Rent Roll": "سجل الإيجارات",
	"PMC Occupancy Summary": "ملخص الإشغال",
	"PMC Rent Aging": "أعمار الإيجارات",
	"PMC Lease Liability Schedule": "جدول التزام الإيجار IFRS 16",
	"RE BOQ": "جدول كميات التطوير",
	"RE Unit Inventory": "مخزون وحدات التطوير",
	"RE Subcontract Commitment": "التزام مقاول باطن",
	"RE Handover Package": "حزمة التسليم",
	"RE Permit Milestone": "معلم التصريح",
	"RE Project EV": "القيمة المكتسبة للمشروع",
	"RE Unit Inventory Overview": "نظرة عامة على مخزون الوحدات",
	"Property Sales Lead": "عميل مبيعات عقارية",
	"Property Sales Booking Register": "سجل حجوزات البيع",
	"Unit Reservation Register": "سجل حجز الوحدات",
	"Development Project Register": "سجل مشاريع التطوير",
	"Sales Commission Accrual": "استحقاق عمولات المبيعات",
	"Sales Commission Schedule": "جدول عمولات المبيعات",
	"Portfolio & asset registry": "المحفظة وسجل الأصول",
	"Leasing & occupancy (IFRS 16 / IPSAS rent)": "التأجير والإشغال (IFRS 16 / IPSAS)",
	"CAM & recoveries": "المصاريف المشتركة والاستردادات",
	"Billing & collections": "الفوترة والتحصيل",
	"Owner reporting & trust accounting": "تقارير الملاك والحسابات الائتمانية",
	"Cross-module operations": "عمليات متكاملة",
	"Land & project charter": "الأرض وميثاق المشروع",
	"Design & quantities (BOQ)": "التصميم والكميات (جدول الكميات)",
	"Budget & cost control": "الميزانية وضبط التكلفة",
	"Unit inventory & sales readiness": "مخزون الوحدات وجاهزية البيع",
	"Handover & defects (snagging)": "التسليم والعيوب",
	"Lead acquisition & qualification": "اكتساب العملاء وتأهيلهم",
	"Reservations & unit holds": "الحجوزات وحجز الوحدات",
	"Bookings & registration": "الحجوزات والتسجيل",
	"Inventory & development context": "المخزون وسياق التطوير",
	"Maintenance — service requests": "الصيانة — طلبات الخدمة",
	"RE unit inventory (sales)": "مخزون وحدات البيع",
	"Rental contract register": "سجل عقود الإيجار",
	"Rent billing register": "سجل فوترة الإيجار",
	"Reservation register": "سجل الحجوزات",
	"Sales booking register": "سجل حجوزات البيع",
	"Unit inventory overview": "نظرة عامة على مخزون الوحدات",
	"Development project register": "سجل مشاريع التطوير",
	"Erpgenex Property Mgmt": "إدارة العقارات",
	"Erpgenex Realestate Dev": "التطوير العقاري",
	"Erpgenex Realestate Sales": "التسويق العقاري",
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
	paren = re.match(r"^(.+?)\s*\((.+)\)\s*$", raw)
	if paren:
		main = translate_desk_label(paren.group(1).strip())
		inner = translate_desk_label(paren.group(2).strip())
		if main != paren.group(1).strip() or inner != paren.group(2).strip():
			return f"{main} ({inner})"
	if " — " in raw:
		parts = [translate_desk_label(p.strip()) for p in raw.split(" — ") if p.strip()]
		joined = " — ".join(parts)
		if joined != raw:
			return joined
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
