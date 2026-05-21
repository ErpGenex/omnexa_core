# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Sync Report.filters JSON files + DB from report_filter_specs (idempotent)."""

from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.modules import scrub

from omnexa_core.omnexa_core.report_print.report_filter_specs import ACCOUNTING_REPORT_FILTERS


def _find_report_json(report_name: str) -> Path | None:
	slug = scrub(report_name)
	for app in frappe.get_installed_apps():
		if app == "frappe" or not (app.startswith("omnexa_") or app.startswith("erpgenex_")):
			continue
		try:
			base = Path(frappe.get_app_path(app))
		except Exception:
			continue
		for pattern in (f"report/{slug}/{slug}.json", f"reports/report/{slug}/{slug}.json"):
			for path in base.rglob(pattern):
				return path
	return None


def sync_accounting_report_json_filters(*, dry_run: bool = False) -> dict[str, int]:
	"""Apply ACCOUNTING_REPORT_FILTERS to repo JSON and Report doctype."""
	stats = {"updated_json": 0, "skipped": 0, "missing": 0}

	for report_name, filters in ACCOUNTING_REPORT_FILTERS.items():
		json_path = _find_report_json(report_name)
		if not json_path:
			stats["missing"] += 1
			continue

		doc = json.loads(json_path.read_text(encoding="utf-8"))
		if doc.get("filters") == filters:
			stats["skipped"] += 1
		else:
			doc["filters"] = filters
			if not dry_run:
				json_path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
			stats["updated_json"] += 1

	return stats


def reload_accounting_reports_from_json():
	"""Import updated Report JSON into DB (child Report Filter rows)."""
	from frappe.modules.import_file import import_file_by_path

	imported = 0
	for report_name in ACCOUNTING_REPORT_FILTERS:
		json_path = _find_report_json(report_name)
		if not json_path:
			continue
		import_file_by_path(str(json_path), force=True)
		imported += 1
	frappe.db.commit()
	return imported


def ensure_accounting_report_json_filters():
	stats = sync_accounting_report_json_filters()
	try:
		stats["reloaded"] = reload_accounting_reports_from_json()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: reload accounting reports from JSON")
	return stats
