# Copyright (c) 2026, ErpGenEx
"""Safe gap fixes for Global Excellence Loop — detect → fix → verify."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import frappe

from omnexa_core.global_excellence.ar_translation_builder import _app_module_root, sync_all_missing_ar_csv, sync_app_ar_csv
from omnexa_core.global_excellence.system_discovery import _app_path, _modules_for_app
from omnexa_core.vertical_workcenter.registry import INFRASTRUCTURE_APP_REGISTRY

_STANDARD_BUSINESS_PERMS = [
	{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 1, "share": 1, "report": 1},
	{"role": "Desk User", "read": 1, "write": 1, "create": 1, "delete": 0, "export": 1, "print": 1, "report": 1},
]

_REPORT_SPECS: dict[str, list[dict]] = {
	"erpgenex_legal": [
		{
			"name": "Legal Case Register",
			"module": "ErpGenEx Legal",
			"ref_doctype": "Legal Case",
			"roles": ["System Manager", "Legal Manager", "Legal User"],
			"filters": [
				{"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "\nDraft\nActive\nSuspended\nClosed\nArchived"},
			],
			"columns_sql": [
				("name", "Name", "Link", 120),
				("case_title", "Case Title", "Data", 200),
				("legal_matter", "Legal Matter", "Link", 140),
				("court", "Court", "Link", 120),
				("status", "Status", "Data", 100),
				("filing_date", "Filing Date", "Date", 110),
			],
		},
		{
			"name": "Legal Matter Summary",
			"module": "ErpGenEx Legal",
			"ref_doctype": "Legal Matter",
			"roles": ["System Manager", "Legal Manager", "Legal User"],
			"filters": [],
			"columns_sql": [
				("name", "Name", "Link", 120),
				("matter_title", "Matter Title", "Data", 200),
				("legal_client", "Legal Client", "Link", 140),
				("practice_area", "Practice Area", "Link", 140),
				("status", "Status", "Data", 100),
			],
		},
		{
			"name": "Legal Appointment Summary",
			"module": "ErpGenEx Legal",
			"ref_doctype": "Legal Appointment",
			"roles": ["System Manager", "Legal Manager", "Legal User"],
			"filters": [
				{"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
				{"fieldname": "to_date", "label": "To Date", "fieldtype": "Date"},
			],
			"columns_sql": [
				("name", "Name", "Link", 120),
				("appointment_date", "Appointment Date", "Date", 120),
				("legal_client", "Legal Client", "Link", 140),
				("lawyer_profile", "Lawyer", "Link", 120),
				("status", "Status", "Data", 100),
			],
		},
	],
	"erpgenex_saas": [
		{
			"name": "SaaS Tenant Register",
			"module": "ERPGenex SaaS",
			"ref_doctype": "SaaS Tenant",
			"roles": ["System Manager"],
			"filters": [],
			"columns_sql": [
				("name", "Name", "Link", 140),
				("tenant_name", "Tenant Name", "Data", 180),
				("status", "Status", "Data", 100),
				("site_url", "Site URL", "Data", 200),
			],
		},
		{
			"name": "SaaS Application Summary",
			"module": "ERPGenex SaaS",
			"ref_doctype": "SaaS Application",
			"roles": ["System Manager"],
			"filters": [],
			"columns_sql": [
				("name", "Name", "Link", 140),
				("application_name", "Application Name", "Data", 180),
				("is_active", "Is Active", "Check", 80),
			],
		},
	],
	"omnexa_ai_employee": [
		{
			"name": "AI Agent Summary",
			"module": "Omnexa AI Employee",
			"ref_doctype": "AI Agent",
			"roles": ["System Manager"],
			"filters": [],
			"columns_sql": [
				("name", "Name", "Link", 140),
				("agent_name", "Agent Name", "Data", 180),
				("agent_role", "Agent Role", "Data", 120),
				("default_provider", "Default Provider", "Link", 140),
			],
		},
	],
	"omnexa_finance_engine": [
		{
			"name": "Finance Policy Register",
			"module": "Omnexa Finance Engine",
			"ref_doctype": "Finance Policy Version",
			"roles": ["System Manager", "Compliance Manager"],
			"filters": [],
			"columns_sql": [
				("name", "Name", "Link", 140),
				("policy_name", "Policy Name", "Data", 160),
				("policy_version", "Policy Version", "Data", 100),
				("status", "Status", "Data", 100),
				("effective_from", "Effective From", "Date", 110),
			],
		},
	],
	"omnexa_credit_risk": [
		{
			"name": "Credit Risk Policy Register",
			"module": "Omnexa Credit Risk",
			"ref_doctype": "Credit Risk Policy Version",
			"roles": ["System Manager", "Risk Manager"],
			"filters": [],
			"columns_sql": [
				("name", "Name", "Link", 140),
				("policy_name", "Policy Name", "Data", 160),
				("policy_version", "Policy Version", "Data", 100),
				("status", "Status", "Data", 100),
				("effective_from", "Effective From", "Date", 110),
			],
		},
	],
}


def _doctype_json_path(doctype: str) -> Path | None:
	for app in frappe.get_installed_apps():
		root = _app_path(app)
		if not root:
			continue
		for p in Path(root).rglob("*.json"):
			try:
				data = json.loads(p.read_text(encoding="utf-8"))
				if data.get("doctype") == "DocType" and data.get("name") == doctype:
					return p
			except Exception:
				continue
	return None


def fix_doctype_permissions_in_json(doctype: str, *, extra_roles: list[dict] | None = None) -> dict:
	path = _doctype_json_path(doctype)
	if not path or not path.is_file():
		return {"doctype": doctype, "status": "skipped", "reason": "json_not_found"}
	data = json.loads(path.read_text(encoding="utf-8"))
	if data.get("permissions"):
		return {"doctype": doctype, "status": "skipped", "reason": "already_has_permissions"}
	perms = list(extra_roles or _STANDARD_BUSINESS_PERMS)
	mod = data.get("module")
	if mod:
		sibling = frappe.db.sql(
			"""
			SELECT parent FROM `tabDocPerm`
			WHERE parent IN (SELECT name FROM `tabDocType` WHERE module = %s AND custom = 0)
			GROUP BY parent
			ORDER BY COUNT(*) DESC LIMIT 1
			""",
			mod,
		)
		if sibling:
			roles = frappe.get_all(
				"DocPerm",
				filters={"parent": sibling[0][0]},
				fields=["role", "read", "write", "create", "delete", "submit", "cancel", "export", "print", "email", "share", "report"],
			)
			if roles:
				perms = [{k: v for k, v in r.items() if k != "name"} for r in roles]

	data["permissions"] = perms
	path.write_text(json.dumps(data, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
	return {"doctype": doctype, "status": "fixed", "path": str(path), "perm_count": len(perms)}


def fix_permission_gaps_for_app(app: str) -> list[dict]:
	modules = _modules_for_app(app)
	if not modules:
		return []
	placeholders = ", ".join(["%s"] * len(modules))
	doctypes = frappe.db.sql(
		f"""
		SELECT name FROM `tabDocType`
		WHERE custom = 0 AND istable = 0 AND module IN ({placeholders})
		""",
		tuple(modules),
		as_dict=True,
	)
	results: list[dict] = []
	for row in doctypes:
		if not frappe.get_all("DocPerm", filters={"parent": row.name}, limit=1):
			results.append(fix_doctype_permissions_in_json(row.name))
	return results


def fix_all_permission_gaps() -> list[dict]:
	results: list[dict] = []
	for app in frappe.get_installed_apps():
		if not app.startswith(("omnexa_", "erpgenex_")):
			continue
		modules = _modules_for_app(app)
		if not modules:
			continue
		placeholders = ", ".join(["%s"] * len(modules))
		doctypes = frappe.db.sql(
			f"""
			SELECT name FROM `tabDocType`
			WHERE custom = 0 AND istable = 0 AND module IN ({placeholders})
			""",
			tuple(modules),
			as_dict=True,
		)
		for row in doctypes:
			perms = frappe.get_all("DocPerm", filters={"parent": row.name}, limit=1)
			if not perms:
				results.append(fix_doctype_permissions_in_json(row.name))
	return results


def _report_folder(app: str, report_name: str) -> Path | None:
	try:
		return _app_module_root(app) / "report" / frappe.scrub(report_name)
	except Exception:
		return None


def _write_script_report(app: str, spec: dict) -> dict:
	folder = _report_folder(app, spec["name"])
	if not folder:
		return {"app": app, "report": spec["name"], "status": "skipped", "reason": "no_folder"}
	folder.mkdir(parents=True, exist_ok=True)
	slug = frappe.scrub(spec["name"])
	ref = spec["ref_doctype"]
	table = f"tab{ref}"
	col_defs = spec.get("columns_sql") or [("name", "Name", "Link", 120)]
	select_parts = [f"`{c[0]}`" for c in col_defs]
	columns_py = ",\n\t\t".join(
		f'{{"label": _("{c[1]}"), "fieldname": "{c[0]}", "fieldtype": "{c[2]}", "width": {c[3]}}}' for c in col_defs
	)
	condition_lines = []
	for f in spec.get("filters") or []:
		fn = f["fieldname"]
		if f["fieldtype"] == "Date":
			op = ">=" if fn.startswith("from") else "<="
			condition_lines.append(f'\tif filters.get("{fn}"):\n\t\tconditions.append("{fn} {op} %({fn})s")')
		else:
			condition_lines.append(f'\tif filters.get("{fn}"):\n\t\tconditions.append("{fn} = %({fn})s")')

	py_content = f'''# Copyright (c) 2026, ErpGenEx
# Auto-generated by Global Excellence safe_gap_fixes

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {{}})
	conditions = ["1=1"]
{chr(10).join(condition_lines) if condition_lines else "\tpass"}
	where_clause = " AND ".join(conditions)
	data = frappe.db.sql(
		f"""
		SELECT {", ".join(select_parts)}
		FROM `{table}`
		WHERE {{where_clause}}
		ORDER BY modified DESC
		LIMIT 500
		""",
		filters,
		as_dict=True,
	)
	columns = [
		{columns_py}
	]
	return columns, data
'''
	json_data = {
		"add_total_row": 0,
		"columns": [],
		"disabled": 0,
		"doctype": "Report",
		"filters": spec.get("filters") or [],
		"is_standard": "Yes",
		"module": spec["module"],
		"name": spec["name"],
		"prepared_report": 0,
		"query": "",
		"ref_doctype": ref,
		"report_name": spec["name"],
		"report_type": "Script Report",
		"roles": [{"role": r} for r in spec.get("roles") or ["System Manager"]],
	}
	(folder / f"{slug}.py").write_text(py_content, encoding="utf-8")
	(folder / f"{slug}.json").write_text(json.dumps(json_data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
	return {"app": app, "report": spec["name"], "status": "created", "path": str(folder)}


def create_missing_reports() -> list[dict]:
	results: list[dict] = []
	for app, specs in _REPORT_SPECS.items():
		for spec in specs:
			if frappe.db.exists("Report", spec["name"]):
				results.append({"app": app, "report": spec["name"], "status": "exists"})
				continue
			results.append(_write_script_report(app, spec))
	return results


def apply_all_safe_gap_fixes(*, sync_translations: bool = True, fix_permissions: bool = True, create_reports: bool = True) -> dict:
	summary: dict = {
		"started_at": datetime.now().isoformat(timespec="seconds"),
		"translations": [],
		"permissions": [],
		"reports": [],
		"infrastructure_registry_count": len(INFRASTRUCTURE_APP_REGISTRY),
	}
	if sync_translations:
		summary["translations"] = sync_all_missing_ar_csv(write=True)
		from omnexa_core.global_excellence.ar_translation_builder import _read_existing_ar, _translations_dir

		for app in frappe.get_installed_apps():
			if not app.startswith(("omnexa_", "erpgenex_")):
				continue
			td = _translations_dir(app)
			if td and (td / "ar.csv").is_file():
				existing = _read_existing_ar(td / "ar.csv")
				if len(existing) < 20:
					summary["translations"].append(sync_app_ar_csv(app, write=True))
	if fix_permissions:
		summary["permissions"] = fix_all_permission_gaps()
	if create_reports:
		summary["reports"] = create_missing_reports()
	summary["completed_at"] = datetime.now().isoformat(timespec="seconds")
	return summary


@frappe.whitelist()
def run_safe_gap_fixes() -> dict:
	frappe.only_for("System Manager")
	result = apply_all_safe_gap_fixes()
	frappe.db.commit()
	return result


def sync_ar_csv_to_translation_doctype(*, max_rows_per_app: int = 500, upsert: bool = False) -> dict:
	"""Import ar.csv UI strings into tabTranslation (safe — UI labels only)."""
	from omnexa_core.global_excellence.ar_translation_builder import _read_existing_ar, _translations_dir

	stats = {"created": 0, "updated": 0, "skipped": 0, "apps": 0}
	for app in frappe.get_installed_apps():
		if not app.startswith(("omnexa_", "erpgenex_")):
			continue
		td = _translations_dir(app)
		if not td:
			continue
		ar_path = td / "ar.csv"
		if not ar_path.is_file():
			continue
		rows = _read_existing_ar(ar_path)
		count = 0
		for en, ar in rows.items():
			if not en or not ar or en == ar:
				stats["skipped"] += 1
				continue
			if count >= max_rows_per_app:
				break
			existing = frappe.db.get_value(
				"Translation", {"language": "ar", "source_text": en}, ["name", "translated_text"], as_dict=True
			)
			if existing:
				if upsert and existing.translated_text != ar:
					frappe.db.set_value("Translation", existing.name, "translated_text", ar)
					stats["updated"] += 1
				else:
					stats["skipped"] += 1
				count += 1
				continue
			doc = frappe.get_doc({"doctype": "Translation", "language": "ar", "source_text": en, "translated_text": ar})
			doc.insert(ignore_permissions=True)
			stats["created"] += 1
			count += 1
		stats["apps"] += 1
	frappe.db.commit()
	return stats


@frappe.whitelist()
def sync_platform_translations() -> dict:
	frappe.only_for("System Manager")
	return sync_ar_csv_to_translation_doctype()
