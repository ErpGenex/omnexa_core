# Copyright (c) 2026, ErpGenEx
"""Wave 9 — Activity-aware Permission Query Conditions (SQL-level vertical isolation)."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.activity_registry import FINANCIAL_CORE_APPS, PLATFORM_STACK_APPS
from omnexa_core.omnexa_core.branch_access import user_can_access_all_branches
from omnexa_core.omnexa_core.isolation_middleware import get_isolation_context

_DOCTYPE_APP_CACHE: dict[str, str | None] = {}
_VERTICAL_APP_CACHE: set[str] | None = None


def _ensure_module_map() -> None:
	if not getattr(frappe.local, "module_app", None):
		frappe.setup_module_map(include_all_apps=True)


def app_from_doctype(doctype: str | None) -> str | None:
	"""Resolve owning Omnexa/ErpGenEx app from DocType module."""
	if not doctype:
		return None
	if doctype in _DOCTYPE_APP_CACHE:
		return _DOCTYPE_APP_CACHE[doctype]
	app: str | None = None
	try:
		_ensure_module_map()
		meta = frappe.get_meta(doctype)
		module = getattr(meta, "module", None)
		if module:
			candidate = (frappe.local.module_app or {}).get(frappe.scrub(module))
			if isinstance(candidate, str) and (
				candidate.startswith("omnexa_") or candidate.startswith("erpgenex_")
			):
				app = candidate
	except Exception:
		app = None
	_DOCTYPE_APP_CACHE[doctype] = app
	return app


def installed_vertical_apps() -> set[str]:
	"""Vertical apps from activity registry that are installed on this site."""
	global _VERTICAL_APP_CACHE
	if _VERTICAL_APP_CACHE is not None:
		return _VERTICAL_APP_CACHE
	from omnexa_core.omnexa_core.activity_registry import ACTIVITIES

	installed = set(frappe.get_installed_apps() or [])
	verticals: set[str] = set()
	for spec in ACTIVITIES.values():
		for app in spec.vertical_apps:
			if app in installed:
				verticals.add(app)
	_VERTICAL_APP_CACHE = verticals
	return verticals


def site_has_multiple_vertical_apps() -> bool:
	return len(installed_vertical_apps()) > 1


def activity_blocks_doctype(doctype: str, user: str | None = None) -> bool:
	"""True when activity scope should hide all rows for this DocType."""
	user = user or frappe.session.user
	if user in ("Administrator",):
		return False
	if user_can_access_all_branches(user) and frappe.session.user == "Administrator":
		return False

	ctx = get_isolation_context(user)
	if ctx.activity_id == "General":
		return False
	if not ctx.strict_activity_filtering:
		return False
	if not site_has_multiple_vertical_apps():
		return False

	owner_app = app_from_doctype(doctype)
	if not owner_app:
		return False
	if owner_app in PLATFORM_STACK_APPS or owner_app in FINANCIAL_CORE_APPS:
		return False
	return owner_app not in ctx.allowed_apps


def activity_permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	"""SQL fragment appended to list/report queries for cross-activity isolation."""
	if not doctype:
		return ""
	if activity_blocks_doctype(doctype, user):
		return "1=0"
	return ""


def activity_pqc_self_test() -> dict:
	"""Smoke test used by isolation QA and Wave 9 certification."""
	results: dict[str, dict] = {}
	healthcare_dt = "Healthcare Patient"
	construction_dt = "IPC Certificate"
	results["multi_vertical_site"] = {
		"pass": site_has_multiple_vertical_apps(),
		"vertical_apps": sorted(installed_vertical_apps()),
	}
	results["healthcare_patient_resolves"] = {
		"pass": app_from_doctype(healthcare_dt) == "omnexa_healthcare",
		"app": app_from_doctype(healthcare_dt),
	}
	results["construction_ipc_resolves"] = {
		"pass": app_from_doctype(construction_dt) == "omnexa_construction",
		"app": app_from_doctype(construction_dt),
	}
	results["platform_doctype_never_blocked"] = {
		"pass": not activity_blocks_doctype("Sales Invoice"),
	}
	passed = sum(1 for row in results.values() if row.get("pass"))
	return {
		"passed": passed,
		"total": len(results),
		"all_pass": passed == len(results),
		"results": results,
	}
