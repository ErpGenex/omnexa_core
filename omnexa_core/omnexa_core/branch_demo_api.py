"""Branch Demo data tab — all transactional demo scoped to one branch."""

from __future__ import annotations

import frappe
from frappe import _


def _assert_system_manager() -> None:
	if "System Manager" not in (frappe.get_roles() or []) and frappe.session.user != "Administrator":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def run_demo_action_for_branch(branch_doc, action_key: str, **kwargs) -> dict:
	if "omnexa_setup_intelligence" in (frappe.get_installed_apps() or []):
		from omnexa_setup_intelligence.utils.branch_demo_router import run_demo_action_for_branch as _route

		return _route(branch_doc, action_key, **kwargs)

	_assert_system_manager()
	frappe.throw(_("Install omnexa_setup_intelligence to run branch demo actions."))


@frappe.whitelist()
def wipe_branch_all_data(company: str, branch: str, confirm_text: str | None = None) -> dict:
	"""Hard wipe for one branch: transactions + construction demo (does not delete company CoA)."""
	if frappe.session.user != "Administrator":
		frappe.throw(_("Only Administrator can run full branch wipe."), frappe.PermissionError)
	_assert_system_manager()
	normalized_confirm = " ".join((confirm_text or "").strip().upper().split())
	if normalized_confirm not in {"DELETE BRANCH", "DELETEBRANCH"}:
		frappe.throw(_("Type DELETE BRANCH to confirm full branch wipe."), title=_("Wipe Branch Data"))
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Company is required"), title=_("Wipe Branch Data"))
	if not branch or not frappe.db.exists("Branch", branch):
		frappe.throw(_("Branch is required"), title=_("Wipe Branch Data"))
	b_company = frappe.db.get_value("Branch", branch, "company")
	if b_company != company:
		frappe.throw(_("Branch does not belong to this company."), title=_("Wipe Branch Data"))

	from omnexa_accounting.utils.production_readiness import run_reset_transactions_batched

	tx = run_reset_transactions_batched(
		company=company, branch=branch, limit=0, batch_size=300, user=frappe.session.user
	)

	construction = None
	if "omnexa_construction" in (frappe.get_installed_apps() or []):
		from omnexa_construction.utils.demo_seed import reset_construction_demo_for_branch

		construction = reset_construction_demo_for_branch(company=company, branch=branch, dry_run=0)

	healthcare = None
	if "omnexa_healthcare" in (frappe.get_installed_apps() or []):
		from omnexa_healthcare.utils.branch_demo_seed import reset_healthcare_demo_for_branch

		healthcare = reset_healthcare_demo_for_branch(company=company, branch=branch, dry_run=0)

	finance = None
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_branch_demo_seed import reset_finance_demo_for_branch

		finance = reset_finance_demo_for_branch(company=company, branch=branch, dry_run=0)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "wipe_branch_all_data:finance")

	return {
		"ok": True,
		"company": company,
		"branch": branch,
		"transactions": tx,
		"construction": construction,
		"healthcare": healthcare,
		"finance": finance
	}
