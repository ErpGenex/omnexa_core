# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""
Minimal reusable fixtures for automated tests and local benches.

Intended for **non-production** sites (CI, dev). Aligns with Egypt pilot defaults
(EGP, Egypt). See Docs/Omnexa_Master_Checklist.md §L (test data generators).
"""

from __future__ import annotations

import frappe


def ensure_pilot_geo() -> None:
	"""Ensure Currency EGP and Country Egypt exist (idempotent)."""
	if not frappe.db.exists("Currency", "EGP"):
		frappe.get_doc(
			{"doctype": "Currency", "currency_name": "EGP", "symbol": "E£", "enabled": 1
	}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Country", "Egypt"):
		frappe.get_doc(
			{"doctype": "Country", "country_name": "Egypt", "code": "EG"
	}
		).insert(ignore_permissions=True)


def create_test_company(abbr: str, *, company_name: str | None = None) -> str:
	"""
	Insert or return existing Company by unique abbr.

	:param abbr: Short unique code (e.g. ``OMNX-TST``).
	:param company_name: Optional display name; default derived from abbr.
	:returns: Company name (document name).
	"""
	ensure_pilot_geo()
	if frappe.db.exists("Company", {"abbr": abbr
	}):
		return frappe.db.get_value("Company", {"abbr": abbr
	}, "name")
	label = company_name or f"Test Co {abbr}"
	doc = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": label,
			"abbr": abbr,
			"default_currency": "EGP",
			"country": "Egypt",
			"status": "Active"
	}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def suppress_workflow_action_emails() -> None:
	"""Disable workflow approval emails (PDF attach) during automated tests."""
	try:
		import frappe.workflow.doctype.workflow_action.workflow_action as workflow_action

		workflow_action.send_workflow_action_email = lambda doc, transitions: None
	except Exception:
		pass


def prepare_test_suite() -> None:
	"""Global pre-test hygiene for all Omnexa apps (Wave 7 functional sweep)."""
	import frappe.core.doctype.user.user as user_module

	suppress_workflow_action_emails()
	user_module.throttle_user_creation = lambda: None
	frappe.conf["throttle_user_limit"] = 999999
	frappe.set_user("Administrator")
