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
		"role_ar": "مسؤول التسجيل",
	},
	{
		"key": "doc_verification",
		"step": 2,
		"label_en": "Document Verification",
		"label_ar": "فحص المستندات",
		"icon": "📄",
		"role_en": "Verification Officer",
		"role_ar": "مسؤول التحقق",
	},
	{
		"key": "credit_bureau",
		"step": 3,
		"label_en": "Credit Bureau Inquiry",
		"label_ar": "الاستعلام الائتماني",
		"icon": "📊",
		"role_en": "Credit Officer",
		"role_ar": "مسؤول ائتمان",
	},
	{
		"key": "field_visit",
		"step": 4,
		"label_en": "Field Visit",
		"label_ar": "الزيارة الميدانية",
		"icon": "📍",
		"role_en": "Field Officer",
		"role_ar": "مسؤول ميداني",
	},
	{
		"key": "financial_analysis",
		"step": 5,
		"label_en": "Financial Analysis",
		"label_ar": "التحليل المالي",
		"icon": "📈",
		"role_en": "Financial Analyst",
		"role_ar": "محلل مالي",
	},
	{
		"key": "credit_recommendation",
		"step": 6,
		"label_en": "Credit Recommendation",
		"label_ar": "توصية الائتمان",
		"icon": "✅",
		"role_en": "Credit Analyst",
		"role_ar": "محلل ائتمان",
	},
	{
		"key": "credit_committee",
		"step": 7,
		"label_en": "Credit Committee",
		"label_ar": "لجنة الائتمان",
		"icon": "👥",
		"role_en": "Committee Member",
		"role_ar": "عضو اللجنة",
	},
	{
		"key": "final_approval",
		"step": 8,
		"label_en": "Final Approval",
		"label_ar": "الموافقة النهائية",
		"icon": "🏛️",
		"role_en": "Approval Authority",
		"role_ar": "جهة الاعتماد",
	},
	{
		"key": "contract_disbursement",
		"step": 9,
		"label_en": "Contract & Disbursement",
		"label_ar": "التعاقد والصرف",
		"icon": "💰",
		"role_en": "Disbursement Officer",
		"role_ar": "مسؤول الصرف",
	},
	{
		"key": "repayment_schedule",
		"step": 10,
		"label_en": "Repayment Schedule",
		"label_ar": "جدول الأقساط",
		"icon": "📅",
		"role_en": "Contract Officer",
		"role_ar": "مسؤول العقود",
	},
	{
		"key": "collections",
		"step": 11,
		"label_en": "Collections & Payment",
		"label_ar": "التحصيل والسداد",
		"icon": "💳",
		"role_en": "Collection Officer",
		"role_ar": "مسؤول التحصيل",
	},
	{
		"key": "reports",
		"step": 12,
		"label_en": "Executive Reports",
		"label_ar": "التقارير التنفيذية",
		"icon": "📋",
		"role_en": "Executive",
		"role_ar": "تنفيذي",
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
	"Cancelled": 0,
}


def get_enterprise_workflow_steps() -> list[dict]:
	return [dict(s) for s in ENTERPRISE_WORKFLOW_STEPS]


def _nav_item(*, label_ar: str, label_en: str, route: str, icon: str = "•") -> dict:
	return {"label_ar": label_ar, "label_en": label_en, "route": route, "icon": icon}


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

	ws = spec.get("workspace")
	if ws and frappe.db.exists("Workspace", ws):
		ws_route = f"/app/{frappe.scrub(ws)}"
		if ws_route not in seen:
			nav.append(_nav_item(label_ar=f"مساحة {brand}", label_en=f"{brand} Workspace", route=ws_route, icon="🏦"))

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
		"wizard_fields": _wizard_fields(app),
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
				"reqd": 1,
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
					"reqd": meta.get_field(fn).reqd,
				}
			)
	if meta.get_field("company"):
		fields.append({"fieldname": "company", "label_en": "Company", "label_ar": "الشركة", "fieldtype": "Link", "reqd": 0})
	if meta.get_field("branch"):
		fields.append({"fieldname": "branch", "label_en": "Branch", "label_ar": "الفرع", "fieldtype": "Link", "reqd": 0})
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
	return {"ok": True, "doctype": dt, "name": doc.name, "route": f"Form/{dt}/{doc.name}"}


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
