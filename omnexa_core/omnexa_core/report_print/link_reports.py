# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Wire ERPGENEX print assets (letter head + HTML) to every ErpGenEx Script Report."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.modules import scrub

from omnexa_core.global_print_design import GLOBAL_LETTER_HEAD_NAME, ensure_global_print_design_system
from omnexa_core.omnexa_core.report_print.report_print_categories import report_print_category, template_filename

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_MARKER = "ERPGENEX report print template"


def _erpgenex_app_names() -> set[str]:
	return {
		app
		for app in frappe.get_installed_apps()
		if app != "frappe" and (app.startswith("omnexa_") or app.startswith("erpgenex_"))
	}


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


def _template_html(report_name: str, module: str | None = None, ref_doctype: str | None = None) -> str:
	category = report_print_category(report_name, module, ref_doctype)
	name = template_filename(category)
	return (_TEMPLATE_DIR / name).read_text(encoding="utf-8")


def _write_print_html(
	folder: Path,
	report_name: str,
	*,
	module: str | None = None,
	ref_doctype: str | None = None,
	force: bool = False,
) -> bool:
	html_path = folder / f"{scrub(report_name)}.html"
	category = report_print_category(report_name, module, ref_doctype)
	content = _template_html(report_name, module, ref_doctype)
	if html_path.exists() and not force:
		existing = html_path.read_text(encoding="utf-8")
		marker = f"erpg-{category[:3]}-print"
		if marker in existing:
			return False
	html_path.write_text(content, encoding="utf-8")
	return True


def _link_html_in_repo(*, only_missing: bool = True, force: bool = False) -> dict[str, int]:
	"""Deploy print HTML beside every Report JSON in ErpGenEx apps (filesystem)."""
	stats = {"json_seen": 0, "html_written": 0, "html_skipped": 0}
	for app in _erpgenex_app_names():
		try:
			base = Path(frappe.get_app_path(app))
		except Exception:
			continue
		for json_path in base.rglob("report/*/*.json"):
			try:
				doc = frappe.parse_json(json_path.read_text(encoding="utf-8"))
			except Exception:
				continue
			if doc.get("doctype") != "Report":
				continue
			stats["json_seen"] += 1
			report_name = doc.get("name") or json_path.stem
			folder = json_path.parent
			if only_missing and not force:
				html_path = folder / f"{scrub(report_name)}.html"
				if html_path.exists():
					try:
						text = html_path.read_text(encoding="utf-8")
						cat = report_print_category(report_name, doc.get("module"), doc.get("ref_doctype"))
						if f"erpg-{cat[:3]}-print" in text:
							stats["html_skipped"] += 1
							continue
					except OSError:
						pass
			if _write_print_html(
				folder,
				report_name,
				module=doc.get("module"),
				ref_doctype=doc.get("ref_doctype"),
				force=force,
			):
				stats["html_written"] += 1
			else:
				stats["html_skipped"] += 1
	return stats


def link_erpgenex_report_print_assets(*, only_missing_html: bool = False, force_html: bool = False) -> dict[str, int]:
	"""Assign global letter head + deploy print HTML for ErpGenEx reports."""
	ensure_global_print_design_system()
	letter_head = (
		frappe.db.get_value("Letter Head", {"letter_head_name": GLOBAL_LETTER_HEAD_NAME}, "name")
		or frappe.db.get_value("Letter Head", {"is_default": 1}, "name")
	)

	repo_stats = _link_html_in_repo(only_missing=only_missing_html, force=force_html)
	stats = {
		"reports_seen": 0,
		"letter_head_set": 0,
		"html_written": repo_stats.get("html_written", 0),
		"html_skipped": repo_stats.get("html_skipped", 0),
		"folder_missing": 0,
		"repo_json_seen": repo_stats.get("json_seen", 0),
	}

	reports = frappe.get_all(
		"Report",
		filters={"disabled": 0, "report_type": "Script Report"},
		fields=["name", "module", "ref_doctype"],
	)

	for row in reports:
		folder = _find_report_folder(row.name)
		if not folder:
			continue

		stats["reports_seen"] += 1

		if letter_head and frappe.db.get_value("Report", row.name, "letter_head") != letter_head:
			frappe.db.set_value("Report", row.name, "letter_head", letter_head, update_modified=False)
			stats["letter_head_set"] += 1

		if only_missing_html and not force_html and (folder / f"{scrub(row.name)}.html").exists():
			stats["html_skipped"] += 1
			continue

		if _write_print_html(
			folder,
			row.name,
			module=row.module,
			ref_doctype=row.ref_doctype,
			force=force_html,
		):
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
