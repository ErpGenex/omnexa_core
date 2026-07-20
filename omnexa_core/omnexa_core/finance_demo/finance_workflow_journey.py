# Copyright (c) 2026, ErpGenEx
"""Enterprise finance workflow journey — 12 screens, wizard, sidebar nav (AR/EN)."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_core.omnexa_core.finance_demo.finance_app_registry import FINANCE_APP_REGISTRY, get_registry_entry
from omnexa_core.omnexa_core.finance_demo.finance_portal_registry import PORTAL_SPECS, get_vertical_meta_for_page
from omnexa_core.omnexa_core.finance_demo.finance_vertical_specs import VERTICAL_BPE_SPECS

# 12 enterprise screens (image 2 + workflow document)
ENTERPRISE_WORKFLOW_STEPS: list[dict] = [
	{
		"key": "registration",
		"step": 1,
		"label_en": "Application Registration",
		"label_ar": "تسجيل طلب التمويل",
		"icon": "📝",
		"role_en": "Registration Officer",
		"role_ar": "مسؤول التسجيل"
	},
	{
		"key": "doc_verification",
		"step": 2,
		"label_en": "Document Verification",
		"label_ar": "فحص المستندات",
		"icon": "📄",
		"role_en": "Verification Officer",
		"role_ar": "مسؤول التحقق"
	},
	{
		"key": "credit_bureau",
		"step": 3,
		"label_en": "Credit Bureau Inquiry",
		"label_ar": "الاستعلام الائتماني",
		"icon": "📊",
		"role_en": "Credit Officer",
		"role_ar": "مسؤول ائتمان"
	},
	{
		"key": "field_visit",
		"step": 4,
		"label_en": "Field Visit",
		"label_ar": "الزيارة الميدانية",
		"icon": "📍",
		"role_en": "Field Officer",
		"role_ar": "مسؤول ميداني"
	},
	{
		"key": "financial_analysis",
		"step": 5,
		"label_en": "Financial Analysis",
		"label_ar": "التحليل المالي",
		"icon": "📈",
		"role_en": "Financial Analyst",
		"role_ar": "محلل مالي"
	},
	{
		"key": "credit_recommendation",
		"step": 6,
		"label_en": "Credit Recommendation",
		"label_ar": "توصية الائتمان",
		"icon": "✅",
		"role_en": "Credit Analyst",
		"role_ar": "محلل ائتمان"
	},
	{
		"key": "credit_committee",
		"step": 7,
		"label_en": "Credit Committee",
		"label_ar": "لجنة الائتمان",
		"icon": "👥",
		"role_en": "Committee Member",
		"role_ar": "عضو اللجنة"
	},
	{
		"key": "final_approval",
		"step": 8,
		"label_en": "Final Approval",
		"label_ar": "الموافقة النهائية",
		"icon": "🏛️",
		"role_en": "Approval Authority",
		"role_ar": "جهة الاعتماد"
	},
	{
		"key": "contract_disbursement",
		"step": 9,
		"label_en": "Contract & Disbursement",
		"label_ar": "التعاقد والصرف",
		"icon": "💰",
		"role_en": "Disbursement Officer",
		"role_ar": "مسؤول الصرف"
	},
	{
		"key": "repayment_schedule",
		"step": 10,
		"label_en": "Repayment Schedule",
		"label_ar": "جدول الأقساط",
		"icon": "📅",
		"role_en": "Contract Officer",
		"role_ar": "مسؤول العقود"
	},
	{
		"key": "collections",
		"step": 11,
		"label_en": "Collections & Payment",
		"label_ar": "التحصيل والسداد",
		"icon": "💳",
		"role_en": "Collection Officer",
		"role_ar": "مسؤول التحصيل"
	},
	{
		"key": "reports",
		"step": 12,
		"label_en": "Executive Reports",
		"label_ar": "التقارير التنفيذية",
		"icon": "📋",
		"role_en": "Executive",
		"role_ar": "تنفيذي"
	},
]

WORKFLOW_STATE_TO_STEP: dict[str, int] = {
	"Draft": 0,
	"Submitted": 1,
	"Assigned": 2,
	"In Progress": 3,
	"Pending Review": 4,
	"Pending Approval": 6,
	"Approved": 7,
	"Completed": 9,
	"Closed": 10,
	"Returned": 3,
	"Rejected": 6,
	"Escalated": 6,
	"Cancelled": 0
	}

# Interactive screen content per enterprise stage (AR/EN).
WORKFLOW_STAGE_SCREENS: dict[str, dict] = {
	"registration": {
		"screen_type": "form",
		"desc_ar": "إنشاء طلب تمويل جديد — بيانات العميل والمنتج والمبلغ.",
		"desc_en": "Create a new finance application — customer, product and amount.",
		"fields": [
			{"fieldname": "product", "label_ar": "نوع التمويل", "label_en": "Finance Product", "fieldtype": "Select"
	},
			{"fieldname": "customer", "label_ar": "اسم العميل", "label_en": "Customer Name", "fieldtype": "Data"
	},
			{"fieldname": "amount", "label_ar": "المبلغ المطلوب", "label_en": "Requested Amount", "fieldtype": "Currency"
	},
			{"fieldname": "term", "label_ar": "المدة (شهر)", "label_en": "Term (Months)", "fieldtype": "Int"
	},
		],
		"actions": [{"key": "wizard", "label_ar": "➕ تسجيل طلب", "label_en": "➕ New Application", "primary": 1}]
	},
	"doc_verification": {
		"screen_type": "documents",
		"desc_ar": "رفع المستندات الإلزامية وتسجيل بياناتها (رقم قومي، سجل تجاري، بطاقة ضريبية، حساب بنكي) للمراجعة والاعتماد.",
		"desc_en": "Upload mandatory documents with metadata (National ID, CR, Tax Card, Bank Account) for review and approval.",
		"actions": [
			{"key": "approve_step", "label_ar": "✓ اعتماد المرحلة", "label_en": "✓ Complete Verification", "primary": 1
	},
			{"key": "open_case", "label_ar": "فتح السجل", "label_en": "Open Record"
	},
		]},
	"credit_bureau": {
		"screen_type": "score",
		"desc_ar": "استعلام مكتب ائتماني — النقاط والالتزامات.",
		"desc_en": "Credit bureau inquiry — score and liabilities.",
		"metrics": [
			{"label_ar": "النقاط", "label_en": "Score", "value": "742"
	},
			{"label_ar": "التصنيف", "label_en": "Grade", "value": "Good / جيد"
	},
			{"label_ar": "الالتزامات الشهرية", "label_en": "Monthly Obligations", "value": "4,200"},
		],
		"decisions": [
			{"value": "suitable", "label_ar": "مناسب", "label_en": "Suitable"
	},
			{"value": "conditional", "label_ar": "مناسب بشروط", "label_en": "Conditional"
	},
			{"value": "unsuitable", "label_ar": "غير مناسب", "label_en": "Unsuitable"
	},
		],
		"actions": [{"key": "next", "label_ar": "→ الزيارة الميدانية", "label_en": "→ Field Visit", "primary": 1}]
	},
	"field_visit": {
		"screen_type": "field",
		"desc_ar": "زيارة ميدانية — الموقع والصور والتوصية.",
		"desc_en": "Field visit — location, photos and recommendation.",
		"fields": [
			{"fieldname": "visit_date", "label_ar": "تاريخ الزيارة", "label_en": "Visit Date", "fieldtype": "Date"
	},
			{"fieldname": "location", "label_ar": "الموقع", "label_en": "Location", "fieldtype": "Data"
	},
			{"fieldname": "activity", "label_ar": "النشاط", "label_en": "Activity", "fieldtype": "Data"
	},
		],
		"decisions": [
			{"value": "recommended", "label_ar": "موصى به", "label_en": "Recommended"
	},
			{"value": "conditional", "label_ar": "بشروط", "label_en": "Conditional"
	},
			{"value": "not_recommended", "label_ar": "غير موصى", "label_en": "Not Recommended"
	},
		],
		"actions": [{"key": "next", "label_ar": "→ التحليل المالي", "label_en": "→ Financial Analysis", "primary": 1}]
	},
	"financial_analysis": {
		"screen_type": "analysis",
		"desc_ar": "تحليل الدخل ونسبة الدين والتدفق النقدي.",
		"desc_en": "Income, debt ratio and cash flow analysis.",
		"metrics": [
			{"label_ar": "الدخل الشهري", "label_en": "Monthly Income", "value": "12,000"},
			{"label_ar": "نسبة الدين", "label_en": "Debt Ratio", "value": "34.7%"
	},
			{"label_ar": "مستوى المخاطر", "label_en": "Risk Level", "value": "Low / منخفض"
	},
		],
		"actions": [{"key": "next", "label_ar": "→ توصية الائتمان", "label_en": "→ Credit Recommendation", "primary": 1}]
	},
	"credit_recommendation": {
		"screen_type": "decision",
		"desc_ar": "توصية محلل الائتمان — اعتماد أو رفض أو شروط.",
		"desc_en": "Credit analyst recommendation — approve, reject or conditions.",
		"decisions": [
			{"value": "approve", "label_ar": "اعتماد", "label_en": "Approve"
	},
			{"value": "conditional", "label_ar": "اعتماد بشروط", "label_en": "Approve with Conditions"
	},
			{"value": "reject", "label_ar": "رفض", "label_en": "Reject"
	},
		],
		"actions": [{"key": "next", "label_ar": "→ لجنة الائتمان", "label_en": "→ Credit Committee", "primary": 1}]
	},
	"credit_committee": {
		"screen_type": "committee",
		"desc_ar": "تصويت أعضاء اللجنة ومحضر القرار.",
		"desc_en": "Committee votes and decision minutes.",
		"table_cols": [
			("member", "العضو", "Member"),
			("role", "الدور", "Role"),
			("vote", "التصويت", "Vote"),
		],
		"table_rows": [
			{"member": "Member A", "role": "Chair", "vote": "Approve"
	},
			{"member": "Member B", "role": "Risk", "vote": "Approve"
	},
			{"member": "Member C", "role": "Credit", "vote": "Conditional"
	},
		],
		"actions": [{"key": "next", "label_ar": "→ الموافقة النهائية", "label_en": "→ Final Approval", "primary": 1}]
	},
	"final_approval": {
		"screen_type": "approval",
		"desc_ar": "الاعتماد النهائي وحدود المنحة المعتمدة.",
		"desc_en": "Final approval and approved facility limits.",
		"metrics": [
			{"label_ar": "المبلغ المعتمد", "label_en": "Approved Amount", "value": "—"
	},
			{"label_ar": "المدة", "label_en": "Term", "value": "—"
	},
			{"label_ar": "القسط الشهري", "label_en": "Monthly Installment", "value": "—"
	},
		],
		"actions": [{"key": "next", "label_ar": "→ التعاقد والصرف", "label_en": "→ Contract & Disbursement", "primary": 1}]
	},
	"contract_disbursement": {
		"screen_type": "checklist",
		"desc_ar": "توقيع العقد وتنفيذ الصرف.",
		"desc_en": "Contract signing and disbursement execution.",
		"checklist": [
			{"id": "contract", "label_ar": "عقد التمويل", "label_en": "Finance Contract"
	},
			{"id": "schedule", "label_ar": "جدول الأقساط", "label_en": "Repayment Schedule"
	},
			{"id": "promissory", "label_ar": "سند لأمر", "label_en": "Promissory Note"
	},
		],
		"fields": [
			{"fieldname": "iban", "label_ar": "IBAN", "label_en": "IBAN", "fieldtype": "Data"
	},
			{"fieldname": "amount", "label_ar": "مبلغ الصرف", "label_en": "Disbursement Amount", "fieldtype": "Currency"
	},
		],
		"actions": [{"key": "disburse", "label_ar": "💰 تنفيذ الصرف", "label_en": "💰 Execute Disbursement", "primary": 1}]
	},
	"repayment_schedule": {
		"screen_type": "schedule",
		"desc_ar": "جدول الأقساط — أصل + ربح + حالة السداد.",
		"desc_en": "Repayment schedule — principal, profit and status.",
		"table_cols": [
			("inst", "#", "#"),
			("due", "الاستحقاق", "Due"),
			("total", "الإجمالي", "Total"),
			("status", "الحالة", "Status"),
		],
		"table_rows": [
			{"inst": "1", "due": "2027-01-01", "total": "1,200", "status": "Paid"
	},
			{"inst": "2", "due": "2027-02-01", "total": "1,200", "status": "Due"
	},
			{"inst": "3", "due": "2027-03-01", "total": "1,200", "status": "Future"
	},
		],
		"actions": [{"key": "next", "label_ar": "→ التحصيل", "label_en": "→ Collections", "primary": 1}]
	},
	"collections": {
		"screen_type": "payment",
		"desc_ar": "تحصيل الأقساط — طرق الدفع والسداد الجزئي.",
		"desc_en": "Installment collection — payment methods and partial pay.",
		"metrics": [
			{"label_ar": "الرصيد المOutstanding", "label_en": "Outstanding", "value": "—"
	},
			{"label_ar": "المستحق", "label_en": "Due Now", "value": "—"
	},
		],
		"fields": [
			{"fieldname": "pay_amount", "label_ar": "مبلغ السداد", "label_en": "Payment Amount", "fieldtype": "Currency"
	},
		],
		"actions": [{"key": "collect", "label_ar": "💳 تأكيد السداد", "label_en": "💳 Confirm Payment", "primary": 1}]
	},
	"reports": {
		"screen_type": "reports",
		"desc_ar": "تقارير المحفظة والاعتماد والتحصيل.",
		"desc_en": "Portfolio, approval and collection executive reports.",
		"metrics": [
			{"label_ar": "إجمالي الطلبات", "label_en": "Applications", "value": "—"
	},
			{"label_ar": "نسبة الاعتماد", "label_en": "Approval Rate", "value": "—"
	},
			{"label_ar": "حجم المحفظة", "label_en": "Portfolio", "value": "—"
	},
		],
		"actions": [{"key": "open_list", "label_ar": "📋 قائمة الحالات", "label_en": "📋 Case List", "primary": 1}]}
	}


def get_enterprise_workflow_steps() -> list[dict]:
	return [dict(s) for s in ENTERPRISE_WORKFLOW_STEPS]


def _nav_item(*, label_ar: str, label_en: str, route: str, icon: str = "•") -> dict:
	return {"label_ar": label_ar, "label_en": label_en, "route": route, "icon": icon
	}


def _case_list_route(doctype: str) -> str:
	return f"List/{doctype}"


def _case_new_route(doctype: str) -> str:
	return f"Form/{doctype}/new"


def _app_nav(app: str, page: str) -> list[dict]:
	"""Rich sidebar nav per app — no duplicate routes."""
	spec = get_registry_entry(app) or {}
	exec_page = spec.get("exec_page") or ""
	serv_page = spec.get("serv_page") or ""
	is_exec = page.endswith("executive-dashboard") or page == "accounting-close-dashboard"
	bpe = VERTICAL_BPE_SPECS.get(app) or {}
	case_dt = bpe.get("case_doctype") or ""
	brand = bpe.get("brand") or app
	nav: list[dict] = []

	if is_exec and exec_page:
		nav.append(_nav_item(label_ar="لوحة تنفيذية", label_en="Executive", route=f"/app/{exec_page}", icon="📊"))
	if serv_page and not is_exec:
		nav.append(_nav_item(label_ar="بوابة الخدمة", label_en="Servicing", route=f"/app/{serv_page}", icon="🛠️"))
	elif serv_page and is_exec:
		nav.append(_nav_item(label_ar="بوابة الخدمة", label_en="Servicing", route=f"/app/{serv_page}", icon="🛠️"))

	if case_dt and frappe.db.exists("DocType", case_dt):
		nav.append(_nav_item(label_ar="قائمة الحالات", label_en="Case List", route=_case_list_route(case_dt), icon="📋"))
		if not is_exec:
			nav.append(_nav_item(label_ar="طلب جديد", label_en="New Application", route="#wizard", icon="➕"))

	vmeta = {}
	for p, ps in PORTAL_SPECS.items():
		if ps.get("app") == app:
			vmeta = get_vertical_meta_for_page(p) or {}
			break
	seen: set[str] = {n["route"] for n in nav}
	for _label, route in vmeta.get("links") or []:
		if route in seen or route.startswith("Workspaces/"):
			continue
		if route.startswith("List/") and case_dt and route == _case_list_route(case_dt):
			continue
		if route.startswith("Form/") and "new" in route:
			continue
		seen.add(route)
		nav.append(_nav_item(label_ar=_label, label_en=_label, route=route, icon="🔗"))

	if is_exec:
		nav.append(_nav_item(label_ar="التقارير", label_en="Reports", route="#step-reports", icon="📈"))
	else:
		nav.append(_nav_item(label_ar="مسار العمل", label_en="Workflow", route="#step-registration", icon="🔄"))

	return nav


def get_portal_journey_context(page: str) -> dict:
	spec = PORTAL_SPECS.get(page)
	if not spec:
		return {}
	app = spec["app"]
	bpe = VERTICAL_BPE_SPECS.get(app) or {}
	return {
		"workflow_steps": get_enterprise_workflow_steps(),
		"sidebar_nav": _app_nav(app, page),
		"case_doctype": bpe.get("case_doctype"),
		"brand": bpe.get("brand") or app,
		"wizard_fields": _wizard_fields(app)
	}


def _wizard_fields(app: str) -> list[dict]:
	bpe = VERTICAL_BPE_SPECS.get(app) or {}
	dt = bpe.get("case_doctype")
	if not dt or not frappe.db.exists("DocType", dt):
		return []
	fields: list[dict] = []
	label_field = bpe.get("seed_label_field") or "name"
	meta = frappe.get_meta(dt)
	if meta.get_field(label_field):
		fields.append(
			{
				"fieldname": label_field,
				"label_en": meta.get_label(label_field),
				"label_ar": meta.get_label(label_field),
				"fieldtype": meta.get_field(label_field).fieldtype,
				"reqd": 1
	}
		)
	for fn, ar, en in (
		("customer_name", "اسم العميل", "Customer Name"),
		("principal", "مبلغ التمويل", "Finance Amount"),
		("term_months", "المدة (شهر)", "Term (Months)"),
		("member_count", "عدد الأعضاء", "Member Count"),
	):
		if meta.get_field(fn) and fn != label_field:
			fields.append(
				{
					"fieldname": fn,
					"label_en": en,
					"label_ar": ar,
					"fieldtype": meta.get_field(fn).fieldtype,
					"reqd": meta.get_field(fn).reqd
	}
			)
	if meta.get_field("company"):
		fields.append({"fieldname": "company", "label_en": "Company", "label_ar": "الشركة", "fieldtype": "Link", "reqd": 0
	})
	if meta.get_field("branch"):
		fields.append({"fieldname": "branch", "label_en": "Branch", "label_ar": "الفرع", "fieldtype": "Link", "reqd": 0
	})
	return fields


@frappe.whitelist()
def create_case_from_wizard(app: str, data: str | dict | None = None) -> dict:
	"""Create a new finance case from portal wizard (Draft)."""
	import json

	bpe = VERTICAL_BPE_SPECS.get(app) or {}
	dt = bpe.get("case_doctype")
	if not dt or not frappe.db.exists("DocType", dt):
		frappe.throw(_("Case DocType not configured for {0}").format(app))
	payload = json.loads(data) if isinstance(data, str) else dict(data or {})
	doc = frappe.new_doc(dt)
	for key, val in payload.items():
		if frappe.get_meta(dt).get_field(key) and val not in (None, ""):
			doc.set(key, val)
	label_field = bpe.get("seed_label_field")
	if label_field and not doc.get(label_field):
		doc.set(label_field, f"{bpe.get('seed_prefix', 'Demo')} {frappe.generate_hash(length=4)}")
	if doc.meta.get_field("company") and not doc.get("company"):
		doc.company = frappe.defaults.get_user_default("Company")
	if doc.meta.get_field("branch") and not doc.get("branch"):
		doc.branch = frappe.defaults.get_user_default("Branch")
	if doc.meta.get_field("lifecycle_stage") and not doc.get("lifecycle_stage"):
		doc.lifecycle_stage = "Origination"
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_borrower_documents import ensure_case_document_slots

		ensure_case_document_slots(dt, doc.name, app)
	except Exception:
		pass
	return {"ok": True, "doctype": dt, "name": doc.name, "route": f"Form/{dt}/{doc.name}"
	}


@frappe.whitelist()
def get_case_journey_detail(doctype: str, name: str) -> dict:
	from omnexa_core.omnexa_core.finance_demo.finance_stage_gate import get_progress_tracker

	tracker = get_progress_tracker(doctype, name)
	steps = get_enterprise_workflow_steps()
	current = WORKFLOW_STATE_TO_STEP.get(tracker.get("current_stage") or "Draft", 0)
	for idx, step in enumerate(steps):
		if idx < current:
			step["status"] = "Completed"
		elif idx == current:
			step["status"] = "In Progress"
		else:
			step["status"] = "Waiting"
	tracker["enterprise_steps"] = steps
	return tracker


def _case_summary(doctype: str | None, name: str | None) -> dict | None:
	if not doctype or not name or not frappe.db.exists(doctype, name):
		return None
	doc = frappe.get_doc(doctype, name)
	out = {"doctype": doctype, "name": name, "workflow_state": getattr(doc, "workflow_state", None) or "Draft"}
	for fn in ("customer_name", "group_name", "principal", "term_months", "lifecycle_stage", "risk_band"):
		if doc.meta.get_field(fn):
			out[fn] = doc.get(fn)
	return out


@frappe.whitelist()
def get_workflow_stage_screen(app: str, step_key: str, case_name: str | None = None) -> dict:
	"""Return interactive screen payload for one of the 12 enterprise workflow stages."""
	bpe = VERTICAL_BPE_SPECS.get(app) or {}
	dt = bpe.get("case_doctype")
	step = next((s for s in ENTERPRISE_WORKFLOW_STEPS if s["key"] == step_key), None)
	if not step:
		frappe.throw(_("Unknown workflow stage: {0}").format(step_key))
	screen = dict(WORKFLOW_STAGE_SCREENS.get(step_key) or {})
	screen["step"] = step
	screen["app"] = app
	screen["case_doctype"] = dt
	screen["case"] = _case_summary(dt, case_name)
	screen["workflow_steps"] = get_enterprise_workflow_steps()

	# Enrich metrics from selected case when possible.
	if screen.get("case") and screen.get("metrics"):
		case = screen["case"]
		for m in screen["metrics"]:
			if m.get("value") == "—" and case.get("principal") and "Amount" in m.get("label_en", ""):
				m["value"] = str(case.get("principal"))

	if screen.get("screen_type") == "reports" and dt and frappe.db.exists("DocType", dt):
		total = frappe.db.count(dt)
		screen["metrics"] = [
			{"label_ar": "إجمالي الطلبات", "label_en": "Applications", "value": total
	},
			{"label_ar": "مسودة", "label_en": "Draft", "value": frappe.db.count(dt, {"workflow_state": "Draft"}) if frappe.get_meta(dt).get_field("workflow_state") else 0
	},
			{"label_ar": "معتمد", "label_en": "Approved", "value": frappe.db.count(dt, {"workflow_state": "Approved"}) if frappe.get_meta(dt).get_field("workflow_state") else 0
	},
		]

	# Borrower complete file actions (PDF / Excel / Report) when a case is selected.
	if screen.get("case") and screen["case"].get("name"):
		extra = [
			{"key": "print_dossier", "label_ar": "📄 ملف المقترض PDF", "label_en": "📄 Borrower File PDF", "primary": 0
	},
			{"key": "print_dossier_preview", "label_ar": "🖨️ طباعة الملف", "label_en": "🖨️ Print File", "primary": 0
	},
			{"key": "export_dossier_excel", "label_ar": "📊 تصدير Excel", "label_en": "📊 Export Excel", "primary": 0
	},
			{"key": "open_dossier_report", "label_ar": "📋 تقرير شامل", "label_en": "📋 Full Report", "primary": 0
	},
		]
		existing = {a.get("key") for a in screen.get("actions") or []}
		screen["actions"] = list(screen.get("actions") or []) + [a for a in extra if a["key"] not in existing]

	return screen
