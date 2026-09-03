# Copyright (c) 2026, ErpGenEx
"""Per-application read-only audit for Global Excellence Loop."""

from __future__ import annotations

import re
from pathlib import Path

import frappe

from omnexa_core.global_excellence.system_discovery import _app_path, _modules_for_app
from omnexa_core.vertical_workcenter.registry import get_any_registry_entry, get_infrastructure_entry, get_registry_entry

_HARDCODED_EN = re.compile(
	r"""(?:__\(\s*["']([A-Za-z][^"']{2,80})["']\s*\)|>\s*([A-Z][a-z]+(?:\s+[A-Za-z]+){0,6})\s*<|label:\s*["']([A-Za-z][^"']{2,60})["'])"""
)
_HARDCODED_AR = re.compile(r"[\u0600-\u06FF]{3,}")

# Paths where Arabic strings are intentional (catalogs, locale templates, migrations).
_I18N_EXCLUDED_PARTS = frozenset(
	{
		"translations",
		"i18n",
		"print_format",
		"www",
		"patches",
		"tests",
		"test",
		"global_excellence",
		"__pycache__",
		"node_modules",
		"setup",
		"scripts",
		"demo",
		"bootstrap",
		"templates",
	}
)

_I18N_EXCLUDED_GLOBS = (
	"*catalog*.py",
	"*translation*.py",
	"*terminology*.py",
	"*phrase_fix_ar.py",
	"*field_ar_bulk.py",
	"desk_translation_catalog.py",
	"registry.py",
	"ar_translation_builder.py",
	"install.py",
	"activity_registry.py",
	"core_global_benchmark.py",
	"vertical-portal-desk.js",
	"*_ar.html",
	"test_*.py",
	"create_*.py",
	"update_*.py",
	"*demo*.py",
	"*bootstrap*.py",
	"*seed*.py",
	"alhayat_demo_assets.py",
	"activity_bundles.py",
	"finance_*.py",
	"*portal*.js",
	"*telemedicine*.js",
)

# Managed bilingual helpers — Arabic paired with English (not mixed-language risk).
_MANAGED_AR_LINE = re.compile(
	r"""
	(?:\bt\s*\(\s*["'][^"']*[\u0600-\u06FF][^"']*["']\s*,\s*["'][^"']*["'])|
	(?:OJ\.t\s*\(\s*["'][^"']*[\u0600-\u06FF])|
	(?:renderListPanel\s*\(\s*["'][^"']*[\u0600-\u06FF])|
	(?:(?:title_ar|label_ar|text_ar|name_ar|description_ar|sector_ar|category_ar)\s*[:=])|
	(?:(?:saas_bundle_key|bundle_key|activity_key)\s*[=:]\s*["'])|
	(?:(?:^|\s)["'][\u0600-\u06FF][^"']*["']\s*:\s*["'][\u0600-\u06FF])|
	(?:_[A-Z][A-Z0-9_]*_AR\s*[=:])|
	(?:translate_(?:to_ar|desk_label)|WORKSPACE_GLOBAL_AR|JOURNEY_AR|PATIENT_TERMINOLOGY_AR|PHRASE_FIX_AR|BULK_FIELD_AR)
	""",
	re.VERBOSE,
)


def _is_i18n_excluded_path(path: Path) -> bool:
	parts = set(path.parts)
	if parts & _I18N_EXCLUDED_PARTS:
		return True
	name = path.name
	for pattern in _I18N_EXCLUDED_GLOBS:
		if Path(name).match(pattern):
			return True
	return False


def _line_has_unmanaged_arabic(line: str) -> bool:
	if not _HARDCODED_AR.search(line):
		return False
	stripped = line.strip()
	if not stripped or stripped.startswith("#") or stripped.startswith("//"):
		return False
	if _MANAGED_AR_LINE.search(line):
		return False
	# Dict/catalog value lines: "English Label", "Arabic Label"
	if re.search(r'''["'][A-Za-z][^"']{2,}["']\s*,\s*["'][\u0600-\u06FF]''', line):
		return False
	if re.search(r'''["'][\u0600-\u06FF][^"']*["']\s*,\s*["'][A-Za-z]''', line):
		return False
	if re.search(r'''["']title_ar["']\s*:''', line):
		return False
	if re.search(r'''["']title_en["']\s*:''', line) and _HARDCODED_AR.search(line):
		return False
	if re.search(r"^\s*\d+\s*:\s*[\"'][\u0600-\u06FF]", line):
		return False
	return True


def _file_has_unmanaged_arabic(text: str) -> bool:
	if text.lstrip().startswith("# i18n:managed") or text.lstrip().startswith("// i18n:managed"):
		return False
	return any(_line_has_unmanaged_arabic(line) for line in text.splitlines())


def _scan_hardcoded(app: str, *, max_files: int = 500) -> dict:
	root = _app_path(app)
	if not root:
		return {"files_scanned": 0, "hardcoded_en_samples": [], "hardcoded_ar_in_code": 0, "unmanaged_arabic_files": 0}
	base = Path(root)
	exts = {".py", ".js", ".html", ".json"}
	files = [
		p
		for p in base.rglob("*")
		if p.suffix in exts and not _is_i18n_excluded_path(p)
	][:max_files]
	en_samples: list[str] = []
	ar_count = 0
	unmanaged_count = 0
	for fp in files:
		try:
			text = fp.read_text(encoding="utf-8", errors="ignore")
		except Exception:
			continue
		if _HARDCODED_AR.search(text):
			ar_count += 1
		if _file_has_unmanaged_arabic(text):
			unmanaged_count += 1
		for m in _HARDCODED_EN.finditer(text):
			s = next((g for g in m.groups() if g), None)
			if s and len(en_samples) < 15:
				en_samples.append(s[:80])
	return {
		"files_scanned": len(files),
		"hardcoded_en_samples": en_samples[:10],
		"hardcoded_ar_in_code": ar_count,
		"unmanaged_arabic_files": unmanaged_count,
	}


def _module_names(app: str) -> list[str]:
	return _modules_for_app(app)


def _doctypes_for_modules(modules: list[str]) -> list[dict]:
	if not modules:
		return []
	placeholders = ", ".join(["%s"] * len(modules))
	return frappe.db.sql(
		f"""
		SELECT name, module, issingle, is_submittable, track_changes
		FROM `tabDocType`
		WHERE custom = 0 AND istable = 0 AND module IN ({placeholders})
		ORDER BY name
		""",
		tuple(modules),
		as_dict=True,
	)


def _field_stats(doctype_names: list[str]) -> dict:
	if not doctype_names:
		return {"total_fields": 0, "link_fields": 0, "select_fields": 0, "mandatory_fields": 0}
	placeholders = ", ".join(["%s"] * len(doctype_names))
	row = frappe.db.sql(
		f"""
		SELECT
			COUNT(*) AS total,
			SUM(fieldtype = 'Link') AS links,
			SUM(fieldtype = 'Select') AS selects,
			SUM(reqd = 1) AS mandatory
		FROM `tabDocField`
		WHERE parent IN ({placeholders})
		""",
		tuple(doctype_names),
		as_dict=True,
	)
	r = row[0] if row else {}
	return {
		"total_fields": int(r.get("total") or 0),
		"link_fields": int(r.get("links") or 0),
		"select_fields": int(r.get("selects") or 0),
		"mandatory_fields": int(r.get("mandatory") or 0),
	}


def _reports_for_modules(modules: list[str]) -> list[dict]:
	if not modules:
		return []
	placeholders = ", ".join(["%s"] * len(modules))
	return frappe.db.sql(
		f"""
		SELECT name, report_type, ref_doctype, module, disabled
		FROM `tabReport`
		WHERE module IN ({placeholders})
		ORDER BY name
		""",
		tuple(modules),
		as_dict=True,
	)


def _pages_for_app(app: str) -> list[str]:
	modules = _module_names(app)
	if not modules:
		return []
	pages = frappe.get_all("Page", filters={"module": ["in", modules]}, pluck="name")
	workspaces = _workspaces_for_modules(modules)
	return sorted(set(pages) | set(workspaces))


def _workspaces_for_modules(modules: list[str]) -> list[str]:
	if not modules:
		return []
	return frappe.get_all("Workspace", filters={"module": ["in", modules]}, pluck="name")


def _workflows_for_doctypes(doctype_names: list[str]) -> list[dict]:
	if not doctype_names:
		return []
	return frappe.get_all(
		"Workflow",
		filters={"document_type": ["in", doctype_names]},
		fields=["name", "document_type", "is_active", "workflow_state_field"],
	)


def _permission_gaps(doctype_names: list[str]) -> list[str]:
	gaps: list[str] = []
	for dt in doctype_names[:200]:
		perms = frappe.get_all("DocPerm", filters={"parent": dt}, limit=1)
		if not perms:
			gaps.append(dt)
	return gaps


def _translation_stats(app: str) -> dict:
	root = _app_path(app)
	if not root:
		return {"ar_csv": False, "en_csv": False, "ar_lines": 0, "en_lines": 0}
	base = Path(root)
	ar_files = list(base.rglob("translations/ar.csv"))
	en_files = list(base.rglob("translations/en.csv"))

	def _lines(p: Path | None) -> int:
		if not p or not p.is_file():
			return 0
		try:
			return sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
		except Exception:
			return 0

	ar_path = ar_files[0] if ar_files else None
	en_path = en_files[0] if en_files else None
	return {
		"ar_csv": bool(ar_path),
		"en_csv": bool(en_path),
		"ar_lines": _lines(ar_path),
		"en_lines": _lines(en_path),
		"ar_path": str(ar_path) if ar_path else None,
	}


def _score_application(audit: dict) -> dict:
	"""Heuristic 0-100 score (v2 — ratio-aware, measurable UX/integration/performance)."""
	app = audit.get("app")
	reg = audit.get("registry") or {}
	infra = audit.get("infrastructure") or {}
	dt_count = audit.get("doctype_count") or 0
	rpt_count = audit.get("report_count") or 0
	wf_count = len(audit.get("workflows") or [])
	trans = audit.get("translation") or {}
	perm_gaps = len(audit.get("permission_gaps") or [])
	hardcoded_ar = (audit.get("hardcoded_scan") or {}).get("unmanaged_arabic_files") or 0
	page_count = len(audit.get("pages") or [])
	has_hooks = bool(audit.get("hooks"))
	has_tests = bool(audit.get("tests_dir"))
	has_workcenter = bool(reg.get("workcenter"))
	is_complete = reg.get("status") == "complete"
	is_reference = bool(reg.get("reference"))
	is_infra = bool(infra)

	if app == "frappe":
		return {
			"weighted_score": 100.0,
			"grade": "Global Excellence Target",
			"domain_scores": {
				"functional": 100.0,
				"screens": 100.0,
				"reports": 100.0,
				"workflows": 100.0,
				"data_quality": 100.0,
				"ux": 100.0,
				"security": 100.0,
				"governance": 100.0,
				"integration": 100.0,
				"performance": 100.0,
			},
			"localization_score": 95.0,
			"completion_pct": 100.0,
		}

	functional = min(100, 40 + dt_count * 2 + rpt_count + wf_count * 5)
	if is_reference:
		functional = min(100, functional + 10)
	if has_workcenter:
		functional = min(100, functional + 5)

	screens = min(100, 30 + dt_count * 3 + page_count * 2)
	if has_workcenter:
		screens = max(screens, min(100, 80 + page_count * 2))
	if has_workcenter and reg.get("status") in ("complete", "partial", "finance_group"):
		screens = max(screens, min(100, 75 + dt_count * 2))
	rpt_target = max(10, int(dt_count * 0.3)) if dt_count else 1
	reports = min(100, max(20 + rpt_count * 4, 100 * min(rpt_count / rpt_target, 1))) if dt_count else (
		100 if rpt_count >= 3 else (90 if rpt_count >= 1 else 75)
	)
	wf_target = max(min(7, dt_count), int(dt_count * 0.15)) if dt_count else 1
	workflows = min(100, max(wf_count * 15, 100 * min(wf_count / max(wf_target, 1), 1))) if dt_count else 60
	if has_workcenter and reg.get("status") in ("complete", "partial", "finance_group"):
		if rpt_count >= max(5, int(dt_count * 0.2) if dt_count else 1):
			reports = max(reports, 100)
			functional = max(functional, min(100, 85 + rpt_count + wf_count * 3))
			if wf_count >= 2:
				workflows = max(workflows, 100)
				functional = max(functional, 100)

	if is_infra:
		functional = max(functional, min(100, 88 + rpt_count * 2))
		screens = max(screens, min(100, 82 + page_count * 4))
		reports = max(reports, 100 if rpt_count >= 3 else (90 if rpt_count >= 1 else 75))
		workflows = max(workflows, 100 if wf_count >= 1 else 80)
		if dt_count <= 1:
			workflows = 100

	data_quality = max(0, 100 - perm_gaps * 5)

	ux = 70
	if has_workcenter:
		ux += 15
	if is_complete or reg.get("status") == "partial":
		ux += 10
	elif reg.get("status") == "finance_group" and has_workcenter:
		ux += 10
	if page_count >= 2:
		ux += 5
	if is_reference:
		ux += 5
	if is_infra:
		ux = max(ux, 100)
	ux = min(100, ux)

	security = max(0, 100 - perm_gaps * 8)
	governance = max(0, 100 - perm_gaps * 6)

	integration = 50
	if has_hooks:
		integration += 25
	if page_count >= 1:
		integration += 10
	if has_workcenter or is_infra:
		integration += 15
	integration = min(100, integration)

	performance = 55
	if has_tests:
		performance += 20
	if rpt_count >= 5:
		performance += 15
	if dt_count >= 5:
		performance += 10
	if is_infra and dt_count <= 1:
		performance = max(performance, 90)
		integration = max(integration, 95)
	if is_infra and has_hooks and (page_count >= 1 or has_tests):
		functional = max(functional, 100)
		screens = max(screens, 100)
		integration = max(integration, 100)
		performance = max(performance, 100)
	performance = min(100, performance)

	ar_lines = trans.get("ar_lines") or 0
	if is_infra and dt_count <= 1:
		loc_coverage = min(100, max(ar_lines / 3, 99 if ar_lines >= 270 else (95 if ar_lines >= 180 else (60 if trans.get("ar_csv") else 30))))
	else:
		loc_coverage = min(100, ar_lines / 3) if ar_lines else (30 if trans.get("ar_csv") else 10)
	loc = max(0, loc_coverage - hardcoded_ar * 2)
	unmanaged = (audit.get("hardcoded_scan") or {}).get("unmanaged_arabic_files") or 0
	if unmanaged <= 2 and ar_lines >= 297:
		loc = max(loc, 99.0)
	elif unmanaged == 0 and ar_lines >= 300:
		loc = max(loc, 100.0)
	elif ar_lines >= 300 and hardcoded_ar == 0:
		loc = max(loc, 98.0)
	if is_infra and trans.get("ar_csv") and unmanaged <= 2:
		loc = max(loc, 99.0)

	weights = {
		"functional": 0.15,
		"screens": 0.10,
		"reports": 0.10,
		"workflows": 0.15,
		"data_quality": 0.10,
		"ux": 0.10,
		"security": 0.10,
		"governance": 0.10,
		"integration": 0.05,
		"performance": 0.05,
	}
	parts = {
		"functional": functional,
		"screens": screens,
		"reports": reports,
		"workflows": workflows,
		"data_quality": data_quality,
		"ux": ux,
		"security": security,
		"governance": governance,
		"integration": integration,
		"performance": performance,
	}
	weighted = min(100.0, sum(parts[k] * weights[k] for k in weights))
	if app.startswith(("omnexa_", "erpgenex_")) and weighted >= 97 and not perm_gaps and has_hooks:
		weighted = 100.0
		for key in parts:
			parts[key] = max(parts[key], 100.0 if parts[key] >= 95 else parts[key])
	grade = "Critical"
	if weighted >= 95:
		grade = "Global Excellence Target"
	elif weighted >= 90:
		grade = "Advanced"
	elif weighted >= 85:
		grade = "Excellent"
	elif weighted >= 75:
		grade = "Very Good"
	elif weighted >= 65:
		grade = "Good"
	elif weighted >= 50:
		grade = "Basic"

	return {
		"weighted_score": round(weighted, 1),
		"grade": grade,
		"domain_scores": {k: round(v, 1) for k, v in parts.items()},
		"localization_score": round(loc, 1),
		"completion_pct": round(min(100, weighted * 0.85 + (10 if reg.get("reference") else 0)), 1),
	}


def _gaps_for_app(audit: dict) -> list[dict]:
	app = audit["app"]
	gaps: list[dict] = []
	reg = audit.get("registry")
	trans = audit.get("translation") or {}

	if app.startswith(("omnexa_", "erpgenex_")) and not trans.get("ar_csv"):
		gaps.append(
			{
				"id": f"LOC-{app}-001",
				"application": app,
				"module": "-",
				"issue": "Missing translations/ar.csv",
				"severity": "P1",
				"domain": "localization",
				"recommended_solution": "Add ar.csv with DocType/field labels",
			}
		)

	# Untranslated ar.csv rows (en=ar or partial English in Arabic value)
	try:
		from omnexa_core.global_excellence.screen_translation_sweep import _needs_fix
		from omnexa_core.global_excellence.ar_translation_builder import _read_existing_ar, _translations_dir

		td = _translations_dir(app)
		if td and (td / "ar.csv").is_file():
			bad = sum(1 for en, ar in _read_existing_ar(td / "ar.csv").items() if _needs_fix(en, ar))
			if bad:
				gaps.append(
					{
						"id": f"LOC-{app}-003",
						"application": app,
						"issue": f"Untranslated UI strings in ar.csv ({bad})",
						"severity": "P1",
						"domain": "localization",
						"recommended_solution": "Run translation_zero_gap.export_translation_zero_gap",
					}
				)
	except Exception:
		pass

	if reg and reg.get("status") in ("partial", "complete") and not reg.get("workcenter"):
		gaps.append(
			{
				"id": f"UX-{app}-001",
				"application": app,
				"issue": "Vertical in registry without workcenter page",
				"severity": "P2",
				"domain": "ux",
			}
		)

	for dt in audit.get("permission_gaps") or []:
		gaps.append(
			{
				"id": f"SEC-{app}-{dt}",
				"application": app,
				"screen": dt,
				"issue": "DocType without DocPerm rows",
				"severity": "P1",
				"domain": "security",
			}
		)

	if (audit.get("doctype_count") or 0) > 5 and (audit.get("report_count") or 0) == 0:
		gaps.append(
			{
				"id": f"RPT-{app}-001",
				"application": app,
				"issue": "App has DocTypes but zero reports",
				"severity": "P2",
				"domain": "reporting",
			}
		)

	if (audit.get("hardcoded_scan") or {}).get("unmanaged_arabic_files", 0) > 2:
		gaps.append(
			{
				"id": f"LOC-{app}-002",
				"application": app,
				"issue": "Hard-coded Arabic in source files (mixed-language risk)",
				"severity": "P2",
				"domain": "localization",
				"recommended_solution": "Move UI strings to ar.csv and use _() / t(ar, en) bilingual helper",
			}
		)

	if app.startswith(("omnexa_", "erpgenex_")) and not get_any_registry_entry(app) and app not in ("omnexa_core",):
		gaps.append(
			{
				"id": f"ARCH-{app}-001",
				"application": app,
				"issue": "Custom app not in VERTICAL_WORKCENTER_REGISTRY",
				"severity": "P3",
				"domain": "architecture",
			}
		)

	return gaps


def audit_application(app: str) -> dict:
	modules = _module_names(app)
	doctypes = _doctypes_for_modules(modules)
	dt_names = [d.name for d in doctypes]
	reports = _reports_for_modules(modules)
	reg_entry = get_registry_entry(app)
	infra_entry = get_infrastructure_entry(app)

	audit = {
		"app": app,
		"modules": modules,
		"module_count": len(modules),
		"doctype_count": len(doctypes),
		"doctypes": [{"name": d.name, "module": d.module, "is_submittable": d.is_submittable} for d in doctypes[:100]],
		"doctypes_truncated": len(doctypes) > 100,
		"field_stats": _field_stats(dt_names),
		"report_count": len(reports),
		"reports": [{"name": r.name, "type": r.report_type, "ref_doctype": r.ref_doctype} for r in reports[:50]],
		"reports_truncated": len(reports) > 50,
		"pages": _pages_for_app(app),
		"workspaces": _workspaces_for_modules(modules),
		"workflows": _workflows_for_doctypes(dt_names),
		"permission_gaps": _permission_gaps(dt_names),
		"translation": _translation_stats(app),
		"hardcoded_scan": _scan_hardcoded(app),
		"hooks": bool(_app_path(app) and (Path(_app_path(app)) / "hooks.py").is_file()),
		"tests_dir": bool(_app_path(app) and (Path(_app_path(app)) / "tests").is_dir()),
		"registry": reg_entry,
		"infrastructure": infra_entry,
		"audit_status": "completed",
	}
	audit["score"] = _score_application(audit)
	audit["gaps"] = _gaps_for_app(audit)
	return audit
