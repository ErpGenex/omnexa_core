# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""W4 governance — Script Report inventory per ErpGenEx app (print audit index)."""

from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import cint


def execute(filters=None):
	filters = frappe._dict(filters or {})
	app_filter = (filters.get("app_filter") or "").strip().lower()
	show_zero = cint(filters.get("show_zero_apps", 1))

	columns = [
		{"label": _("App"), "fieldname": "app", "fieldtype": "Data", "width": 200},
		{"label": _("Report"), "fieldname": "report", "fieldtype": "Data", "width": 220},
		{"label": _("Module"), "fieldname": "module", "fieldtype": "Data", "width": 160},
		{"label": _("Ref DocType"), "fieldname": "ref_doctype", "fieldtype": "Data", "width": 150},
		{"label": _("Desk Filters"), "fieldname": "filter_count", "fieldtype": "Int", "width": 90},
		{"label": _("Print HTML"), "fieldname": "has_print_html", "fieldtype": "Data", "width": 90},
		{"label": _("Wave"), "fieldname": "wave", "fieldtype": "Data", "width": 70},
		{"label": _("Notes"), "fieldname": "notes", "fieldtype": "Data", "width": 200},
	]

	apps = _installed_erpgenex_apps()
	reports_by_app = _scan_repo_reports()
	data: list[dict] = []

	for app in sorted(apps):
		if app_filter and app_filter not in app.lower():
			continue
		reports = reports_by_app.get(app, [])
		if reports:
			for rep in reports:
				data.append(rep)
		elif show_zero:
			data.append(
				{
					"app": app,
					"report": _("—"),
					"module": "",
					"ref_doctype": "",
					"filter_count": 0,
					"has_print_html": _("N/A"),
					"wave": "W4",
					"notes": _("No Script Reports — infrastructure / theme app (waived)"),
				}
			)

	msg = _("Governance index for W4 print audit. Apps without reports are waived per platform policy.")
	return columns, data, msg, None, None, False


def _installed_erpgenex_apps() -> list[str]:
	return sorted(
		app
		for app in frappe.get_installed_apps()
		if app != "frappe" and (app.startswith("omnexa_") or app.startswith("erpgenex_"))
	)


def _scan_repo_reports() -> dict[str, list[dict]]:
	bench = Path(frappe.get_bench_path())
	w123 = {
		"omnexa_accounting",
		"omnexa_statutory_audit",
		"omnexa_reporting_compliance",
		"omnexa_fixed_assets",
		"erpgenex_property_mgmt",
		"omnexa_alm",
		"omnexa_hr",
		"omnexa_einvoice",
		"omnexa_trading",
	}
	out: dict[str, list[dict]] = {}
	for app_dir in (bench / "apps").iterdir():
		if not app_dir.is_dir():
			continue
		app = app_dir.name
		if not (app.startswith("omnexa_") or app.startswith("erpgenex_")):
			continue
		for json_path in app_dir.rglob("report/*/*.json"):
			try:
				doc = json.loads(json_path.read_text(encoding="utf-8"))
			except Exception:
				continue
			if doc.get("doctype") != "Report":
				continue
			name = doc.get("name") or json_path.stem
			html_path = json_path.with_suffix(".html")
			has_html = html_path.exists() and "ERPGENEX report print template" in html_path.read_text(
				encoding="utf-8", errors="replace"
			)
			wave = "W1" if app in ("omnexa_accounting", "omnexa_statutory_audit", "omnexa_reporting_compliance") else (
				"W2"
				if app in ("omnexa_fixed_assets", "erpgenex_property_mgmt", "omnexa_alm")
				else "W3"
				if app in ("omnexa_hr", "omnexa_einvoice", "omnexa_trading")
				else "W4"
			)
			out.setdefault(app, []).append(
				{
					"app": app,
					"report": name,
					"module": doc.get("module") or "",
					"ref_doctype": doc.get("ref_doctype") or "",
					"filter_count": len(doc.get("filters") or []),
					"has_print_html": _("Yes") if has_html else _("No"),
					"wave": wave,
					"notes": "",
				}
			)
	for app in out:
		out[app].sort(key=lambda r: (r.get("report") or "").lower())
	return out
