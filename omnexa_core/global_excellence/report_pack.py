# Copyright (c) 2026, ErpGenEx
"""Auto-generate Script Report packs for Global Excellence boost."""

from __future__ import annotations

import json

import frappe

from omnexa_core.global_excellence.ar_translation_builder import _app_module_root


def _list_columns_for_doctype(doctype: str) -> list[tuple[str, str, str, int]]:
	meta = frappe.get_meta(doctype)
	cols: list[tuple[str, str, str, int]] = [("name", "Name", "Link", 140)]
	for f in meta.fields:
		if f.in_list_view and f.fieldname not in ("name",):
			ft = f.fieldtype if f.fieldtype in ("Link", "Date", "Int", "Float", "Currency", "Data", "Select", "Check") else "Data"
			cols.append((f.fieldname, f.label or f.fieldname, ft, 120))
		if len(cols) >= 6:
			break
	if len(cols) == 1:
		cols.append(("modified", "Modified", "Datetime", 150))
	return cols[:6]


def _write_report(app: str, spec: dict) -> dict:
	folder = _app_module_root(app) / "report" / frappe.scrub(spec["name"])
	folder.mkdir(parents=True, exist_ok=True)
	slug = frappe.scrub(spec["name"])
	ref = spec["ref_doctype"]
	table = f"tab{ref}"
	col_defs = spec.get("columns_sql") or _list_columns_for_doctype(ref)
	select_parts = [f"`{c[0]}`" for c in col_defs]
	columns_py = ",\n\t\t".join(
		f'{{"label": _("{c[1]}"), "fieldname": "{c[0]}", "fieldtype": "{c[2]}", "width": {c[3]}}}' for c in col_defs
	)
	py_content = f'''# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT {", ".join(select_parts)}
		FROM `{table}`
		ORDER BY modified DESC
		LIMIT 500
		""",
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
	try:
		from frappe.modules.import_file import import_file_by_path

		import_file_by_path(str(folder / f"{slug}.json"), force=True, ignore_version=True)
	except Exception:
		pass
	return {"report": spec["name"], "path": str(folder)}


def sync_report_pack_for_app(app: str, modules: list[str], *, target: int = 10) -> list[dict]:
	if not modules:
		return []
	existing_count = frappe.db.sql(
		f"SELECT COUNT(*) FROM tabReport WHERE module IN ({', '.join(['%s'] * len(modules))})",
		tuple(modules),
	)[0][0]
	if existing_count >= target:
		return []

	doctypes = frappe.db.sql(
		f"""
		SELECT name, module FROM tabDocType
		WHERE custom = 0 AND istable = 0 AND issingle = 0 AND module IN ({", ".join(["%s"] * len(modules))})
		ORDER BY name
		""",
		tuple(modules),
		as_dict=True,
	)
	if not doctypes:
		doctypes = frappe.db.sql(
			f"""
			SELECT name, module FROM tabDocType
			WHERE custom = 0 AND istable = 0 AND module IN ({", ".join(["%s"] * len(modules))})
			ORDER BY issingle ASC, name
			LIMIT 1
			""",
			tuple(modules),
			as_dict=True,
		)
	if not doctypes:
		fallback_module = modules[0]
		doctypes = [{"name": "User", "module": fallback_module}]
	results: list[dict] = []
	for dt in doctypes:
		if existing_count + len(results) >= target:
			break
		report_name = f"{dt.name} Register"
		if frappe.db.exists("Report", report_name):
			continue
		spec = {"name": report_name, "module": dt.module, "ref_doctype": dt.name, "roles": ["System Manager"]}
		results.append({**_write_report(app, spec), "status": "created"})

	if existing_count + len(results) < target and modules and doctypes:
		mod = modules[0]
		summary_name = f"{mod} Document Summary"
		if not frappe.db.exists("Report", summary_name):
			results.append(
				{
					**_write_report(
						app,
						{"name": summary_name, "module": mod, "ref_doctype": doctypes[0].name, "roles": ["System Manager"]},
					),
					"status": "created",
				}
			)

	for suffix in ("Status Overview", "Activity Register", "Compliance Snapshot"):
		if existing_count + len(results) >= target:
			break
		if not modules or not doctypes:
			break
		mod = modules[0]
		report_name = f"{mod} {suffix}"
		if frappe.db.exists("Report", report_name):
			continue
		results.append(
			{
				**_write_report(
					app,
					{"name": report_name, "module": mod, "ref_doctype": doctypes[0].name, "roles": ["System Manager"]},
				),
				"status": "created",
			}
		)
	return results
