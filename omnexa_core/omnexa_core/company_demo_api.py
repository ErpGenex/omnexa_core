"""Company Chart of accounts tab — COA actions only (all transactional demo is on Branch)."""

from __future__ import annotations

import frappe
from frappe import _


def _assert_system_manager() -> None:
	if "System Manager" not in (frappe.get_roles() or []) and frappe.session.user != "Administrator":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_demo_action_specs(company: str) -> list[dict]:
	"""Return COA button metadata for the Company form (legacy JS hub)."""
	_assert_system_manager()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} not found").format(company))

	if "omnexa_accounting" not in (frappe.get_installed_apps() or []):
		return []

	return [
		{"key": "coa_generate", "group": _("Chart of accounts"), "label": _("Generate professional COA")
	},
		{"key": "coa_resync_labels", "group": _("Chart of accounts"), "label": _("Resync COA labels (names from template)")
	},
		{"key": "ifrs_fill_gl", "group": _("IFRS defaults"), "label": _("Fill default GLs from CoA (by account number)")
	},
	]


@frappe.whitelist()
def run_demo_action(
	company: str,
	action_key: str,
	branch: str | None = None,
	activity: str | None = None,
	confirm_text: str | None = None,
	force: int | str | None = 0,
) -> dict:
	"""Execute a COA action from the Company form."""
	return run_coa_action_for_company(company, action_key, activity=activity)


def run_coa_action_for_company(company: str, action_key: str, activity: str | None = None) -> dict:
	_assert_system_manager()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} not found").format(company))

	key = (action_key or "").strip()
	activity = (activity or "").strip() or None
	if not activity:
		activity = frappe.db.get_value("Company", company, "industry_sector") or "General"

	if key == "coa_generate":
		from omnexa_accounting.utils.production_readiness import generate_professional_chart_of_accounts

		return generate_professional_chart_of_accounts(company, branch=None, activity=activity)

	if key == "ifrs_fill_gl":
		from omnexa_accounting.utils.company_financial_defaults import fill_company_financial_defaults_from_coa

		return fill_company_financial_defaults_from_coa(company, branch=None, overwrite=0)

	if key == "coa_resync_labels":
		from omnexa_accounting.utils.production_readiness import resync_chart_of_accounts_labels

		return resync_chart_of_accounts_labels(company, branch=None, activity=activity)

	frappe.throw(_("Unknown CoA action: {0}").format(key))


def run_demo_action_for_company(
	company: str,
	action_key: str,
	branch: str | None = None,
	activity: str | None = None,
	confirm_text: str | None = None,
	force: int | str | None = 0,
) -> dict:
	"""Backward-compatible alias — transactional demo moved to Branch."""
	return run_coa_action_for_company(company, action_key, activity=activity)


@frappe.whitelist(methods=["POST"])
def wipe_company_all(company: str, confirm_text: str | None = None) -> dict:
	"""Queue full company wipe (System Manager / Administrator)."""
	from omnexa_core.omnexa_core.branch_access import user_can_wipe_company

	if not user_can_wipe_company():
		frappe.throw(_("Only System Manager can run full company wipe."), frappe.PermissionError)
	_assert_system_manager()
	from omnexa_accounting.utils.production_readiness import enqueue_wipe_company_all_data

	return enqueue_wipe_company_all_data(company=company, branch=None, confirm_text=confirm_text)
