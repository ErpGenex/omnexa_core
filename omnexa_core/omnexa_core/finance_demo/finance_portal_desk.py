# Copyright (c) 2026, ErpGenEx
"""Finance portal desk API — KPIs, tables, workflow links per role journey."""

from __future__ import annotations

import frappe
from frappe.utils import cint

from omnexa_core.omnexa_core.finance_demo.finance_app_registry import get_logo_url
from omnexa_core.omnexa_core.finance_demo.finance_portal_registry import (
	ACCOUNTING_META,
	PORTAL_SPECS,
	VERTICAL_META,
	get_vertical_meta_for_page,
)


def _doctype_exists(doctype: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype))


def _safe_count(doctype: str, filters: dict | None = None) -> int:
	if not _doctype_exists(doctype):
		return 0
	try:
		return cint(frappe.db.count(doctype, filters or {}))
	except Exception:
		return 0


def _company_branch_filters(company: str | None, branch: str | None, doctype: str) -> dict:
	filters: dict = {}
	meta = frappe.get_meta(doctype) if _doctype_exists(doctype) else None
	if not meta:
		return filters
	if company and meta.get_field("company"):
		filters["company"] = company
	if branch and meta.get_field("branch"):
		filters["branch"] = branch
	return filters


def _standard_field(fieldname: str) -> bool:
	return fieldname in {"name", "modified", "creation", "owner", "docstatus"}


def _resolve_status_field(meta) -> str | None:
	for candidate in (
		"status",
		"run_status",
		"workflow_state",
		"decision_status",
		"lifecycle_stage",
		"case_status",
		"run_type",
	):
		if meta.get_field(candidate):
			return candidate
	return None


def _resolve_table_schema(doctype: str, fields: list[str], cols: list[tuple]) -> tuple[list[str], list[tuple]]:
	meta = frappe.get_meta(doctype)
	resolved_fields: list[str] = []
	seen: set[str] = set()

	for field in fields:
		actual = field
		if not _standard_field(field) and not meta.get_field(field):
			if field == "status":
				actual = _resolve_status_field(meta) or ""
			else:
				actual = ""
		if actual and actual not in seen:
			resolved_fields.append(actual)
			seen.add(actual)

	if not resolved_fields:
		resolved_fields = ["name", "modified"]

	resolved_cols: list[tuple] = []
	for field, label_ar, label_en in cols:
		actual = field
		if not _standard_field(field) and not meta.get_field(field):
			if field == "status":
				actual = _resolve_status_field(meta) or ""
			else:
				actual = ""
		if actual and actual in resolved_fields:
			resolved_cols.append((actual, label_ar, label_en))

	if not resolved_cols:
		resolved_cols = [("name", "الاسم", "Name"), ("modified", "التاريخ", "Date")]

	return resolved_fields, resolved_cols


def _workflow_servicing_kpis(app: str, company: str | None, branch: str | None, vmeta: dict) -> list[dict] | None:
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_vertical_specs import get_spec

		spec = get_spec(app)
		if not spec:
			return None
		dt = spec["case_doctype"]
		table = vmeta.get("table")
		if table and table != dt:
			return None
		if not _doctype_exists(dt):
			return None
		base = _company_branch_filters(company, branch, dt)
		kpis = [{"label_ar": "حالات", "label_en": "Cases", "value": _safe_count(dt, base)}]
		if frappe.get_meta(dt).get_field("workflow_state"):
			for ws, ar, en in (
				("Draft", "مسودة", "Draft"),
				("Pending Approval", "بانتظار الاعتماد", "Pending Approval"),
				("Disbursed", "مصروف", "Disbursed"),
				("Closed", "مغلقة", "Closed"),
			):
				f = dict(base)
				f["workflow_state"] = ws
				kpis.append({"label_ar": ar, "label_en": en, "value": _safe_count(dt, f)})
		return kpis
	except Exception:
		return None


def _kpi_rows(meta: dict, kpi_key: str, company: str | None, branch: str | None) -> list[dict]:
	out = []
	for item in meta.get(kpi_key, []):
		if len(item) == 3:
			doctype, label_ar, label_en = item
			filters = _company_branch_filters(company, branch, doctype)
		else:
			doctype, label_ar, label_en, status_filter = item
			filters = _company_branch_filters(company, branch, doctype)
			if status_filter:
				filters["status"] = status_filter
		out.append(
			{
				"label_ar": label_ar,
				"label_en": label_en,
				"value": _safe_count(doctype, filters),
			}
		)
	return out


def _table_payload(meta: dict, company: str | None, branch: str | None) -> dict:
	doctype = meta.get("table")
	if not doctype or not _doctype_exists(doctype):
		return {}
	default_fields = ["name", "modified"]
	default_cols = [("name", "الاسم", "Name"), ("modified", "التاريخ", "Date")]
	fields, table_cols = _resolve_table_schema(
		doctype,
		list(meta.get("table_fields") or default_fields),
		list(meta.get("table_cols") or default_cols),
	)
	filters = _company_branch_filters(company, branch, doctype)
	try:
		rows = frappe.get_all(
			doctype,
			filters=filters,
			fields=fields,
			limit_page_length=10,
			order_by="modified desc",
		)
	except Exception:
		rows = []
	columns = [{"field": f, "label_ar": ar, "label_en": en} for f, ar, en in table_cols]
	return {
		"columns": columns,
		"rows": rows,
		"table_title_ar": "آخر السجلات",
		"table_title_en": "Recent Records",
	}


def _links_payload(meta: dict, app: str) -> list[dict]:
	links = []
	seen = set()
	for doctype, route in meta.get("links", []):
		if route in seen:
			continue
		seen.add(route)
		links.append(
			{
				"label_ar": doctype,
				"label_en": doctype,
				"route": route,
				"app": app,
				"logo_url": get_logo_url(app),
			}
		)
	return links


def _resolve_meta(page: str) -> tuple[dict, dict, str, str]:
	spec = PORTAL_SPECS.get(page)
	if not spec:
		frappe.throw(f"Unknown finance portal: {page}")
	app = spec["app"]
	vmeta = get_vertical_meta_for_page(page) or {}
	if app == "omnexa_accounting":
		if page == "accounting-close-dashboard":
			kpi_key = "kpis_close"
		else:
			kpi_key = "kpis_exec"
	else:
		kpi_key = "kpis_exec" if page.endswith("executive-dashboard") else "kpis_serv"
	return spec, vmeta, app, kpi_key


@frappe.whitelist()
def get_portal_dashboard(page: str, company: str | None = None, branch: str | None = None) -> dict:
	company = company or frappe.defaults.get_user_default("Company")
	branch = branch or frappe.defaults.get_user_default("Branch")
	spec, vmeta, app, kpi_key = _resolve_meta(page)
	# microfinance KPIs by lifecycle_stage (no legacy status field)
	if app == "omnexa_sme_microfinance" and kpi_key == "kpis_serv":
		kpis = []
		dt = "Microfinance Case"
		base = _company_branch_filters(company, branch, dt)
		kpis.append({"label_ar": "حالات", "label_en": "Cases", "value": _safe_count(dt, base)})
		for stage, ar, en in (
			("Origination", "منشأة", "Origination"),
			("Disbursement", "صرف", "Disbursement"),
			("Collection", "تحصيل", "Collection"),
			("Closed", "مغلقة", "Closed"),
		):
			f = dict(base)
			if _doctype_exists(dt) and frappe.get_meta(dt).get_field("lifecycle_stage"):
				f["lifecycle_stage"] = stage
			kpis.append({"label_ar": ar, "label_en": en, "value": _safe_count(dt, f)})
		# Workflow / SLA KPIs
		if _doctype_exists(dt) and frappe.get_meta(dt).get_field("workflow_state"):
			for ws, ar, en in (
				("Pending Approval", "بانتظار الاعتماد", "Pending Approval"),
				("Pending Verification", "بانتظار التحقق", "Pending Verification"),
			):
				f = dict(base)
				f["workflow_state"] = ws
				kpis.append({"label_ar": ar, "label_en": en, "value": _safe_count(dt, f)})
	elif kpi_key == "kpis_serv":
		wk = _workflow_servicing_kpis(app, company, branch, vmeta)
		kpis = wk if wk else _kpi_rows(vmeta, kpi_key, company, branch)
	elif app == "omnexa_sme_microfinance" and kpi_key == "kpis_exec":
		dt = "Microfinance Case"
		base = _company_branch_filters(company, branch, dt)
		kpis = [{"label_ar": "حالات", "label_en": "Cases", "value": _safe_count(dt, base)}]
		for stage, ar, en in (
			("Origination", "منشأة", "Origination"),
			("Disbursement", "محفظة نشطة", "Active Portfolio"),
			("Collection", "تحصيل", "Collection"),
			("Closed", "مغلقة", "Closed"),
		):
			f = dict(base)
			if frappe.get_meta(dt).get_field("lifecycle_stage"):
				f["lifecycle_stage"] = stage
			kpis.append({"label_ar": ar, "label_en": en, "value": _safe_count(dt, f)})
	else:
		kpis = _kpi_rows(vmeta, kpi_key, company, branch)
	from omnexa_core.omnexa_core.finance_demo.finance_workflow_journey import get_portal_journey_context

	journey = get_portal_journey_context(page)
	out = {
		"page": page,
		"app": app,
		"logo_url": get_logo_url(app),
		"kpis": kpis,
		"links": [],
		"workflow_steps": journey.get("workflow_steps") or [],
		"sidebar_nav": journey.get("sidebar_nav") or [],
		"case_doctype": journey.get("case_doctype"),
		"wizard_fields": journey.get("wizard_fields") or [],
		"brand": journey.get("brand"),
	}
	out.update(_table_payload(vmeta, company, branch))
	if app == "omnexa_sme_microfinance":
		try:
			from omnexa_sme_microfinance.mf_maturity import get_maturity_scores

			out["maturity"] = get_maturity_scores()
		except Exception:
			pass
	return out
