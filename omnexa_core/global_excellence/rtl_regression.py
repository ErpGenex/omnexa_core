# Copyright (c) 2026, ErpGenEx
"""RTL regression audit for ERPGenex role portals and workcenters."""

from __future__ import annotations

import re
from pathlib import Path

import frappe

from omnexa_core.global_excellence.system_discovery import _app_path
from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY

_PORTAL_JS = "public/js/vertical-portal-desk.js"
_PORTAL_CSS = "public/css/portal_theme.css"


def _read_app_file(app: str, rel: str) -> str:
	root = _app_path(app)
	if not root:
		return ""
	for candidate in (Path(root) / rel, Path(root) / app / rel):
		if candidate.is_file():
			return candidate.read_text(encoding="utf-8", errors="ignore")
	return ""


def _check_portal_js(js: str) -> dict:
	checks = {
		"bilingual_helper_t": bool(re.search(r"function\s+t\s*\(\s*ar\s*,\s*en\s*\)", js)),
		"render_list_panel_bilingual": "renderListPanel" in js and "title_ar" in js or "label_ar" in js,
		"dir_attribute_support": 'dir="' in js or "setAttribute(\"dir\"" in js or "frappe.boot.lang" in js,
		"arabic_quick_strings": bool(re.search(r"[\u0600-\u06FF]", js)),
	}
	passed = sum(1 for v in checks.values() if v)
	return {"checks": checks, "passed": passed, "total": len(checks), "status": "pass" if passed >= 3 else "warn"}


def _check_portal_css(css: str) -> dict:
	checks = {
		"rtl_direction_rules": "[dir=\"rtl\"]" in css or ".oj-rtl" in css,
		"portal_layout_flex": "oj-vertical-portal" in css or "omnexa-portal" in css,
		"sidebar_rules": "portal-aside" in css or "portal-sidebar" in css or "oj-vertical-portal-aside" in css,
	}
	passed = sum(1 for v in checks.values() if v)
	return {"checks": checks, "passed": passed, "total": len(checks), "status": "pass" if checks["rtl_direction_rules"] else "fail"}


def audit_rtl_for_vertical(app: str, *, workcenter: str | None = None) -> dict:
	js = _read_app_file("omnexa_core", _PORTAL_JS)
	css = _read_app_file("omnexa_core", _PORTAL_CSS)
	js_result = _check_portal_js(js)
	css_result = _check_portal_css(css)
	page_ok = bool(workcenter and frappe.db.exists("Page", workcenter))
	overall = "pass"
	if css_result["status"] == "fail":
		overall = "fail"
	elif js_result["status"] == "warn" or not page_ok:
		overall = "warn"
	return {
		"app": app,
		"workcenter": workcenter,
		"workcenter_page_exists": page_ok,
		"portal_js": js_result,
		"portal_css": css_result,
		"overall": overall,
	}


def run_rtl_regression(*, reference_only: bool = False) -> dict:
	targets = VERTICAL_WORKCENTER_REGISTRY
	if reference_only:
		targets = [r for r in targets if r.get("reference")]

	results = []
	for entry in targets:
		app = entry["app"]
		wc = entry.get("workcenter")
		if not wc:
			continue
		results.append(audit_rtl_for_vertical(app, workcenter=wc))

	# Core SSOT always checked
	core = audit_rtl_for_vertical("omnexa_core", workcenter="finance-workcenter")
	results.insert(0, core)

	passed = sum(1 for r in results if r.get("overall") == "pass")
	failed = sum(1 for r in results if r.get("overall") == "fail")
	return {
		"status": "completed",
		"portals_tested": len(results),
		"passed": passed,
		"failed": failed,
		"warn": len(results) - passed - failed,
		"results": results,
	}


@frappe.whitelist()
def run_rtl_portal_regression() -> dict:
	frappe.only_for("System Manager")
	return run_rtl_regression(reference_only=False)
