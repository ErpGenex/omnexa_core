# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Wire ERPGENEX print assets (letter head + HTML) to every ErpGenEx Script Report."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.modules import scrub

from omnexa_core.global_print_design import GLOBAL_LETTER_HEAD_NAME, ensure_global_print_design_system

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_MARKER = "ERPGENEX report print template"
_AUDIT_KEYWORDS = ("audit", "compliance", "governance", "remediation", "evidence", "control")


def _erpgenex_app_names() -> set[str]:
	return {
		app
		for app in frappe.get_installed_apps()
		if app != "frappe" and (app.startswith("omnexa_") or app.startswith("erpgenex_"))
	}


def _is_audit_report(report_name: str, module: str | None) -> bool:
	blob = f"{report_name} {module or ''}".lower()
	return any(k in blob for k in _AUDIT_KEYWORDS)


def _find_report_folder(report_name: str) -> Path | None:
	slug = scrub(report_name)
	for app in _erpgenex_app_names():
		try:
			base = Path(frappe.get_app_path(app))
		except Exception:
			continue
		for pattern in (f"report/{slug}/{slug}.json", f"reports/report/{slug}/{slug}.json"):
			for json_path in base.rglob(pattern):
				return json_path.parent
	return None


def _template_html(audit: bool) -> str:
	name = "erpgenex_audit_report_print.html" if audit else "erpgenex_report_print.html"
	return (_TEMPLATE_DIR / name).read_text(encoding="utf-8")


def _write_print_html(folder: Path, report_name: str, audit: bool) -> bool:
	html_path = folder / f"{scrub(report_name)}.html"
	content = _template_html(audit)
	if html_path.exists():
		existing = html_path.read_text(encoding="utf-8")
		if _MARKER in existing:
			if audit and "statutory audit opinion" in existing:
				return False
			if not audit and "statutory audit opinion" not in existing:
				return False
	html_path.write_text(content, encoding="utf-8")
	return True


def link_erpgenex_report_print_assets(*, only_missing_html: bool = False) -> dict[str, int]:
	"""Assign global letter head + deploy print HTML for ErpGenEx reports."""
	ensure_global_print_design_system()
	letter_head = (
		frappe.db.get_value("Letter Head", {"letter_head_name": GLOBAL_LETTER_HEAD_NAME}, "name")
		or frappe.db.get_value("Letter Head", {"is_default": 1}, "name")
	)

	stats = {
		"reports_seen": 0,
		"letter_head_set": 0,
		"html_written": 0,
		"html_skipped": 0,
		"folder_missing": 0,
	}

	reports = frappe.get_all(
		"Report",
		filters={"disabled": 0, "report_type": "Script Report"},
		fields=["name", "module"],
	)

	for row in reports:
		folder = _find_report_folder(row.name)
		if not folder:
			continue

		stats["reports_seen"] += 1
		audit = _is_audit_report(row.name, row.module)

		if letter_head and frappe.db.get_value("Report", row.name, "letter_head") != letter_head:
			frappe.db.set_value("Report", row.name, "letter_head", letter_head, update_modified=False)
			stats["letter_head_set"] += 1

		if only_missing_html and (folder / f"{scrub(row.name)}.html").exists():
			stats["html_skipped"] += 1
			continue

		if _write_print_html(folder, row.name, audit):
			stats["html_written"] += 1
		else:
			stats["html_skipped"] += 1

	frappe.db.commit()
	return stats


def ensure_erpgenex_report_print_assets() -> None:
	"""Idempotent hook entry — safe on every migrate."""
	try:
		link_erpgenex_report_print_assets()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa: link_erpgenex_report_print_assets")
