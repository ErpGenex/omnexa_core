# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Ensure Desk boot payloads use ERPGENEX as the product name (no ERPNext in UI)."""

from __future__ import annotations

from typing import Any


def _rebrand_str(value: str) -> str:
	if "ERPNext" not in value and "ErpNext" not in value:
		return value
	return value.replace("ERPNext", "ERPGENEX").replace("ErpNext", "ERPGENEX")


def _rebrand(value: Any) -> Any:
	if isinstance(value, str):
		return _rebrand_str(value)
	if isinstance(value, dict):
		return {k: _rebrand(v) for k, v in value.items()}
	if isinstance(value, list):
		return [_rebrand(v) for v in value]
	if isinstance(value, tuple):
		return tuple(_rebrand(v) for v in value)
	return value


def boot_session(bootinfo):
	"""Frappe hook: patch bootinfo in place for ERPGENEX branding."""
	for key in ("success_action", "notes"):
		if bootinfo.get(key):
			bootinfo[key] = _rebrand(bootinfo[key])

	try:
		import frappe as _frappe

		bootinfo.erpgenex_installed_apps = _frappe.get_installed_apps()
	except Exception:
		bootinfo.erpgenex_installed_apps = []

	from omnexa_core.desk_license_boot import inject_omnexa_license_boot

	inject_omnexa_license_boot(bootinfo)

	try:
		from omnexa_core.omnexa_core.session_context import get_view_context

		bootinfo.omnexa_view_context = get_view_context()
	except Exception:
		bootinfo.omnexa_view_context = {"can_switch": False}

	try:
		from omnexa_core.omnexa_core.app_visibility import inject_desk_visibility_boot

		inject_desk_visibility_boot(bootinfo)
	except Exception:
		pass

	try:
		from omnexa_core.omnexa_core.finance_demo.finance_portal_registry import PORTAL_SPECS

		bootinfo.finance_portal_registry = PORTAL_SPECS
	except Exception:
		bootinfo.finance_portal_registry = {}

	try:
		from omnexa_core.omnexa_core.finance_demo.finance_borrower_dossier import get_finance_case_doctypes_boot

		bootinfo.finance_case_doctypes = get_finance_case_doctypes_boot()
	except Exception:
		bootinfo.finance_case_doctypes = []
