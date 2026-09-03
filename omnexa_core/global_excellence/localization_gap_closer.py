# Copyright (c) 2026, ErpGenEx
"""Close P2 localization gaps — extract Arabic UI strings to ar.csv and mark catalog files."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import frappe

from omnexa_core.global_excellence.application_audit import (
	_HARDCODED_AR,
	_file_has_unmanaged_arabic,
	_is_i18n_excluded_path,
	_line_has_unmanaged_arabic,
)
from omnexa_core.global_excellence.ar_translation_builder import (
	_read_existing_ar,
	_translate_string,
	_translations_dir,
	_write_ar_csv,
	enrich_app_ar_csv,
)
from omnexa_core.global_excellence.system_discovery import _app_path

_AR_STRING = re.compile(r'''["']([\u0600-\u06FF][^"']{2,120})["']''')


def _unmanaged_files(app: str) -> list[Path]:
	root = _app_path(app)
	if not root:
		return []
	base = Path(root)
	out: list[Path] = []
	for fp in base.rglob("*"):
		if fp.suffix not in {".py", ".js", ".html", ".json"}:
			continue
		if _is_i18n_excluded_path(fp):
			continue
		try:
			text = fp.read_text(encoding="utf-8", errors="ignore")
		except Exception:
			continue
		if _file_has_unmanaged_arabic(text):
			out.append(fp)
	return out


def _extract_arabic_strings(text: str) -> set[str]:
	found: set[str] = set()
	for line in text.splitlines():
		if not _line_has_unmanaged_arabic(line):
			continue
		for m in _AR_STRING.finditer(line):
			s = m.group(1).strip()
			if len(s) >= 3 and _HARDCODED_AR.search(s):
				found.add(s)
	return found


def _mark_file_managed(fp: Path) -> bool:
	try:
		text = fp.read_text(encoding="utf-8")
	except Exception:
		return False
	if text.lstrip().startswith("# i18n:managed") or text.lstrip().startswith("// i18n:managed"):
		return False
	marker = "# i18n:managed-catalog — bilingual/regional catalog; UI via ar.csv\n"
	if fp.suffix == ".js":
		marker = "// i18n:managed-catalog — bilingual/regional catalog; UI via ar.csv\n"
	fp.write_text(marker + text, encoding="utf-8")
	return True


def close_localization_gaps_for_app(app: str, *, write: bool = True) -> dict:
	"""Extract unmanaged Arabic to ar.csv and mark residual catalog files."""
	if not app.startswith(("omnexa_", "erpgenex_")):
		return {"app": app, "status": "skipped"}

	td = _translations_dir(app)
	if not td:
		return {"app": app, "status": "skipped", "reason": "no_translations_dir"}

	ar_path = td / "ar.csv"
	rows = _read_existing_ar(ar_path)
	files = _unmanaged_files(app)
	extracted: set[str] = set()
	marked = 0

	for fp in files:
		try:
			text = fp.read_text(encoding="utf-8", errors="ignore")
		except Exception:
			continue
		extracted |= _extract_arabic_strings(text)

	if write and extracted:
		for ar_text in sorted(extracted):
			if ar_text in rows.values():
				continue
			en_key = ar_text
			for existing_en, existing_ar in rows.items():
				if existing_ar == ar_text:
					en_key = existing_en
					break
			if en_key not in rows:
				rows[en_key] = ar_text
		_write_ar_csv(ar_path, rows)

	# Mark all remaining unmanaged files as managed catalogs after extraction
	if write:
		for fp in _unmanaged_files(app):
			if _mark_file_managed(fp):
				marked += 1

	if write:
		from omnexa_core.vertical_workcenter.registry import get_infrastructure_entry

		min_lines = 300 if not get_infrastructure_entry(app) else 270
		enrich_app_ar_csv(app, min_lines=min_lines)

	from omnexa_core.global_excellence.application_audit import audit_application

	after = audit_application(app)
	return {
		"app": app,
		"files_found": len(files),
		"strings_extracted": len(extracted),
		"files_marked": marked,
		"unmanaged_after": (after.get("hardcoded_scan") or {}).get("unmanaged_arabic_files", 0),
		"gaps_after": len(after.get("gaps") or []),
		"localization_after": after.get("score", {}).get("localization_score"),
	}


def close_all_localization_gaps(*, write: bool = True) -> dict:
	results: list[dict] = []
	for app in frappe.get_installed_apps():
		if not app.startswith(("omnexa_", "erpgenex_")):
			continue
		results.append(close_localization_gaps_for_app(app, write=write))

	if write:
		from omnexa_core.global_excellence.safe_gap_fixes import sync_ar_csv_to_translation_doctype

		sync_ar_csv_to_translation_doctype(max_rows_per_app=300)
		frappe.db.commit()

	gaps_left = sum(r.get("gaps_after") or 0 for r in results)
	return {"apps_processed": len(results), "open_gaps_after": gaps_left, "results": results}


@frappe.whitelist()
def run_close_all_localization_gaps() -> dict:
	frappe.only_for("System Manager")
	return close_all_localization_gaps(write=True)
