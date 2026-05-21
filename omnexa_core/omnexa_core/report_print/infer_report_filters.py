# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Infer Desk Report filters from Script Report Python and sync JSON (W4 wave)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import frappe

from omnexa_core.omnexa_core.report_print.report_filter_specs import (
	ACCOUNTING_REPORT_FILTERS,
	FILTER_FIELD_ORDER,
	INFERRED_FILTER_TEMPLATES,
)

_W123_APPS = frozenset(
	{
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
)

_FILTER_GET_RE = re.compile(r"""filters\.get\(\s*["'](\w+)["']""")
_REQUIRED_RE_TEMPLATE = r"""if\s+not\s+filters\.get\(\s*["']{field}["']"""


def _labelize(fieldname: str) -> str:
	return fieldname.replace("_", " ").title()


def _is_required(fieldname: str, py_text: str) -> bool:
	return bool(re.search(_REQUIRED_RE_TEMPLATE.format(field=fieldname), py_text))


def infer_filters_from_py(py_path: Path) -> list[dict]:
	if not py_path.exists():
		return []
	text = py_path.read_text(encoding="utf-8", errors="replace")
	mentioned = set(_FILTER_GET_RE.findall(text))
	if not mentioned:
		return []

	filters: list[dict] = []
	seen: set[str] = set()

	def _append(fieldname: str, template: dict | None = None):
		if fieldname in seen:
			return
		seen.add(fieldname)
		entry = dict(template or {})
		if not entry:
			entry = {
				"fieldname": fieldname,
				"fieldtype": "Data",
				"label": _labelize(fieldname),
				"width": "180px",
			}
		else:
			entry = dict(entry)
		if _is_required(fieldname, text):
			entry["reqd"] = 1
		filters.append(entry)

	for fieldname in FILTER_FIELD_ORDER:
		if fieldname in mentioned:
			_append(fieldname, INFERRED_FILTER_TEMPLATES.get(fieldname))

	for fieldname in sorted(mentioned):
		if fieldname not in FILTER_FIELD_ORDER:
			_append(fieldname, INFERRED_FILTER_TEMPLATES.get(fieldname))

	return filters


def _erpgenex_apps() -> list[str]:
	return [
		app
		for app in frappe.get_installed_apps()
		if app != "frappe" and (app.startswith("omnexa_") or app.startswith("erpgenex_"))
	]


def sync_w4_inferred_report_json_filters(
	*,
	dry_run: bool = False,
	only_empty: bool = True,
) -> dict[str, int]:
	"""Write inferred filters into sector (W4) report JSON files."""
	stats = {
		"scanned": 0,
		"updated_json": 0,
		"skipped_has_filters": 0,
		"skipped_w123_manual": 0,
		"skipped_no_infer": 0,
		"imported": 0,
	}
	manual_reports = set(ACCOUNTING_REPORT_FILTERS.keys())
	changed_paths: list[Path] = []

	for app in _erpgenex_apps():
		if app in _W123_APPS:
			continue
		try:
			base = Path(frappe.get_app_path(app))
		except Exception:
			continue
		for json_path in base.rglob("report/*/*.json"):
			if "/report/" not in str(json_path).replace("\\", "/"):
				continue
			try:
				doc = json.loads(json_path.read_text(encoding="utf-8"))
			except Exception:
				continue
			if doc.get("doctype") != "Report":
				continue
			stats["scanned"] += 1
			report_name = doc.get("name") or json_path.stem
			if report_name in manual_reports:
				stats["skipped_w123_manual"] += 1
				continue
			if only_empty and (doc.get("filters") or []):
				stats["skipped_has_filters"] += 1
				continue
			py_path = json_path.with_suffix(".py")
			inferred = infer_filters_from_py(py_path)
			if not inferred:
				stats["skipped_no_infer"] += 1
				continue
			if doc.get("filters") == inferred:
				continue
			doc["filters"] = inferred
			if not dry_run:
				json_path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
				changed_paths.append(json_path)
			stats["updated_json"] += 1

	if not dry_run and changed_paths:
		from frappe.modules.import_file import import_file_by_path

		for json_path in changed_paths:
			try:
				import_file_by_path(str(json_path), force=True)
				stats["imported"] += 1
			except Exception:
				frappe.log_error(
					frappe.get_traceback(),
					f"Omnexa: import report filters {json_path}",
				)
		frappe.db.commit()

	return stats


def ensure_w4_inferred_report_json_filters():
	return sync_w4_inferred_report_json_filters()
