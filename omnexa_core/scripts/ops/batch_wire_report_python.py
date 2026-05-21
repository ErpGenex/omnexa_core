#!/usr/bin/env python3
"""Rewrite static Script Reports to honor Desk filters (W4 completion)."""

from __future__ import annotations

import json
import re
from pathlib import Path

def _find_bench_root() -> Path:
	p = Path(__file__).resolve().parent
	for _ in range(12):
		if (p / "sites" / "apps.txt").is_file():
			return p
		if p.parent == p:
			break
		p = p.parent
	raise SystemExit("Cannot find frappe-bench root (missing sites/apps.txt)")


BENCH = _find_bench_root()
# Hand-maintained or frozen — do not auto-rewrite Python
WIRE_SKIP_APPS = frozenset(
	{
		"omnexa_accounting",
		"omnexa_einvoice",
	}
)

IMPORT_BLOCK = """from frappe import _

from omnexa_core.omnexa_core.report_print.report_query_filters import (
\tget_all_filters,
\tpolicy_version_filters,
\tprepare_filters,
\tsql_conditions,
)
"""

GOVERNANCE_APPS = {
	"Consumer Finance Policy Version": ("omnexa_consumer_finance", "Consumer Finance Audit Snapshot"),
	"Credit Policy Version": ("omnexa_credit_engine", None),
	"Credit Risk Policy Version": ("omnexa_credit_risk", None),
	"Factoring Policy Version": ("omnexa_factoring", None),
	"Finance Policy Version": ("omnexa_finance_engine", None),
	"Mortgage Finance Policy Version": ("omnexa_mortgage_finance", None),
	"Operational Risk Policy Version": ("omnexa_operational_risk", None),
	"SME Retail Finance Policy Version": ("omnexa_sme_retail_finance", None),
	"Vehicle Finance Policy Version": ("omnexa_vehicle_finance", None),
}


def _extract_columns_block(text: str) -> str | None:
	m = re.search(r"def _columns\(\):.*?return\s+(\[.*?\])", text, re.DOTALL)
	if m:
		return m.group(1)
	m = re.search(r"def execute\(filters=None\):.*?columns\s*=\s*(\[.*?\])", text, re.DOTALL)
	if m:
		return m.group(1)
	return None


def _extract_sql(text: str) -> tuple[str, str, str] | None:
	m = re.search(
		r"frappe\.db\.sql\(\s*[\"']{3}(.*?)[\"']{3}\s*,",
		text,
		re.DOTALL,
	)
	if not m:
		return None
	sql = m.group(1)
	from_m = re.search(r"from\s+`tab([^`]+)`", sql, re.I)
	if not from_m:
		return None
	doctype = from_m.group(1)
	group_m = re.search(r"group\s+by\s+(.+?)(?:\s+order\s+by|\s*$)", sql, re.I | re.DOTALL)
	order_m = re.search(r"order\s+by\s+(.+?)(?:\s*$)", sql, re.I | re.DOTALL)
	select_m = re.search(r"select\s+(.+?)\s+from", sql, re.I | re.DOTALL)
	if not select_m:
		return None
	return doctype, select_m.group(1).strip(), (group_m.group(1).strip() if group_m else "1"), (
		order_m.group(1).strip() if order_m else "1"
	)


def _governance_py(policy_doctype: str, app: str, snap_doctype: str | None) -> str:
	snap_line = ""
	if snap_doctype:
		snap_line = f'\tsnaps = frappe.db.count("{snap_doctype}")\n\tcolumns[-1] = {{"label": _("Snapshots"), "fieldname": "snapshots", "fieldtype": "Int", "width": 100}}\n'
	else:
		snap_line = "\tsnaps = 0\n"
	return f'''# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
{IMPORT_BLOCK}


def execute(filters=None):
\tfilters = prepare_filters(filters)
\textra = policy_version_filters(filters)
\tcolumns = [
\t\t{{"label": _("App"), "fieldname": "app", "fieldtype": "Data", "width": 180}},
\t\t{{"label": _("Policies Total"), "fieldname": "policies_total", "fieldtype": "Int", "width": 120}},
\t\t{{"label": _("Pending"), "fieldname": "pending", "fieldtype": "Int", "width": 90}},
\t\t{{"label": _("Approved"), "fieldname": "approved", "fieldtype": "Int", "width": 90}},
\t\t{{"label": _("Rejected"), "fieldname": "rejected", "fieldtype": "Int", "width": 90}},
\t]
{snap_line}
\tbase = extra or {{}}
\tpol_total = frappe.db.count("{policy_doctype}", base or None)
\tpending = frappe.db.count("{policy_doctype}", {{**base, "status": "PENDING_APPROVAL"}})
\tapproved = frappe.db.count("{policy_doctype}", {{**base, "status": "APPROVED"}})
\trejected = frappe.db.count("{policy_doctype}", {{**base, "status": "REJECTED"}})
\trow = {{
\t\t"app": "{app}",
\t\t"policies_total": pol_total,
\t\t"pending": pending,
\t\t"approved": approved,
\t\t"rejected": rejected,
\t}}
\tif snaps:
\t\trow["snapshots"] = snaps
\treturn columns, [row]
'''


def _sql_py(columns: str, doctype: str, select: str, group: str, order: str, extra_where: str = "") -> str:
	extra_lines = ""
	if extra_where:
		extra_lines = f'\tconditions = ["{extra_where}"] + conditions\n'
	return f'''# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
{IMPORT_BLOCK}


def execute(filters=None):
\tcolumns = {columns}
\tfilters = prepare_filters(filters)
\tconditions, params = sql_conditions(filters, "{doctype}", date_field="creation", company=True, branch=True)
{extra_lines}\trows = frappe.db.sql(
\t\tf"""
\t\tSELECT
\t\t\t{select}
\t\tFROM `tab{doctype}`
\t\tWHERE {{' AND '.join(conditions)}}
\t\tGROUP BY {group}
\t\tORDER BY {order}
\t\t""",
\t\tparams,
\t\tas_dict=True,
\t)
\treturn columns, rows
'''


def _get_all_py(columns: str, doctype: str, fields: list[str], extra_links: dict | None = None) -> str:
	fields_repr = repr(fields)
	extra = repr(extra_links or {})
	post = ""
	if "profit" in columns or "cost_variance" in columns:
		post = """
\tfor row in data:
\t\trow.cost_variance = flt(row.actual_cost) - flt(row.planned_cost)
"""
		import_flt = "from frappe.utils import flt\n"
	else:
		import_flt = ""
	return f'''# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
{import_flt}{IMPORT_BLOCK}


def execute(filters=None):
\tfilters = prepare_filters(filters)
\tfilters_dict = get_all_filters(filters, "{doctype}", date_field="creation", company=True, branch=True, extra_links={extra})
\tdata = frappe.get_all(
\t\t"{doctype}",
\t\tfields={fields_repr},
\t\tfilters=filters_dict,
\t\tlimit_page_length=5000,
\t)
{post}
\treturn {columns}, data
'''


def patch_file(py_path: Path, report_name: str, ref_doctype: str) -> bool:
	text = py_path.read_text(encoding="utf-8")
	if "prepare_filters" in text:
		return False
	text = text.replace("{{", "{").replace("}}", "}")

	if report_name == "Governance Overview" and ref_doctype in GOVERNANCE_APPS:
		app, snap = GOVERNANCE_APPS[ref_doctype]
		py_path.write_text(_governance_py(ref_doctype, app, snap), encoding="utf-8")
		return True

	cols = _extract_columns_block(text)
	if not cols:
		cols = "[]"

	if "frappe.get_all" in text and ref_doctype:
		fields_m = re.search(r'fields=\[([^\]]+)\]', text)
		fields = []
		if fields_m:
			fields = [f.strip().strip("'\"") for f in fields_m.group(1).split(",") if f.strip()]
		if not fields:
			fields = ["name"]
		extra = {}
		if ref_doctype == "BOQ Item":
			extra = {"project_contract": "project_contract"}
		if ref_doctype == "Project Contract" and report_name.startswith("Project Profitability"):
			# special profitability - keep custom loop, only add filter on get_all
			new = text
			if "prepare_filters" not in new:
				new = new.replace(
					"def execute(filters=None):",
					"def execute(filters=None):\n\tfilters = prepare_filters(filters)",
				)
				if "from omnexa_core" not in new:
					new = "import frappe\n" + IMPORT_BLOCK + "\n" + new.split("import frappe", 1)[-1]
				new = new.replace(
					'frappe.get_all(\n\t\t"Project Contract",\n\t\tfields=',
					'frappe.get_all(\n\t\t"Project Contract",\n\t\tfilters=get_all_filters(filters, "Project Contract", company=True, branch=True, extra_links={"name": "project_contract"}),\n\t\tfields=',
				)
				py_path.write_text(new, encoding="utf-8")
				return True
		py_path.write_text(_get_all_py(cols, ref_doctype, fields, extra), encoding="utf-8")
		return True

	sql_parts = _extract_sql(text)
	if sql_parts:
		dt, select, group, order = sql_parts
		extra_where = ""
		if "docstatus = 1" in text:
			extra_where = "docstatus = 1"
		py_path.write_text(_sql_py(cols, dt, select, group, order, extra_where), encoding="utf-8")
		return True

	return False


def main():
	patched = 0
	for app_dir in sorted((BENCH / "apps").iterdir()):
		if not app_dir.is_dir() or app_dir.name in WIRE_SKIP_APPS:
			continue
		if not (app_dir.name.startswith("omnexa_") or app_dir.name.startswith("erpgenex_")):
			continue
		for j in app_dir.rglob("report/*/*.json"):
			try:
				d = json.loads(j.read_text(encoding="utf-8"))
			except Exception:
				continue
			if d.get("doctype") != "Report":
				continue
			if not (d.get("filters") or []):
				continue
			py = j.with_suffix(".py")
			if not py.exists():
				continue
			if patch_file(py, d.get("name") or j.stem, d.get("ref_doctype") or ""):
				patched += 1
				print("patched", py)
	print("total patched", patched)


if __name__ == "__main__":
	main()
