# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Site-wide admin tools — purge companies/branches (System Manager only)."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_core.omnexa_core.branch_access import user_can_wipe_company


def _assert_admin() -> None:
	if not user_can_wipe_company():
		frappe.throw(_("Only System Manager or Administrator can run site purge."), frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def purge_all_branches(confirm_text: str | None = None) -> dict:
	"""Delete every branch on the site (after per-branch data wipe)."""
	_assert_admin()
	if (confirm_text or "").strip().upper() != "DELETE ALL BRANCHES":
		frappe.throw(_('Type exactly "DELETE ALL BRANCHES" to confirm.'))

	from omnexa_core.omnexa_core.branch_demo_api import wipe_branch_all_data

	results = []
	for row in frappe.get_all("Branch", fields=["name", "company"], order_by="creation desc"):
		try:
			wipe_branch_all_data(row.company, row.name, confirm_text="DELETE ALL")
		except Exception:
			pass
		try:
			frappe.delete_doc("Branch", row.name, force=1, ignore_permissions=True)
			results.append(row.name)
		except Exception as exc:
			frappe.log_error(title=f"Purge branch {row.name}", message=str(exc))

	frappe.db.commit()
	frappe.clear_cache()
	return {"deleted_branches": results, "count": len(results)}


@frappe.whitelist(methods=["POST"])
def purge_all_companies(confirm_text: str | None = None) -> dict:
	"""Delete every company (full wipe + company record)."""
	_assert_admin()
	if (confirm_text or "").strip().upper() != "DELETE ALL COMPANIES":
		frappe.throw(_('Type exactly "DELETE ALL COMPANIES" to confirm.'))

	from omnexa_accounting.utils.production_readiness import enqueue_wipe_company_all_data

	deleted = []
	for company in frappe.get_all("Company", pluck="name", order_by="creation desc"):
		try:
			enqueue_wipe_company_all_data(company=company, branch=None, confirm_text="DELETE ALL")
		except Exception:
			try:
				from omnexa_accounting.utils.production_readiness import purge_company_for_deletion

				purge_company_for_deletion(company)
			except Exception:
				pass
		try:
			frappe.delete_doc("Company", company, force=1, ignore_permissions=True)
			deleted.append(company)
		except Exception as exc:
			frappe.log_error(title=f"Purge company {company}", message=str(exc))

	frappe.db.commit()
	frappe.clear_cache()
	return {"deleted_companies": deleted, "count": len(deleted)}


@frappe.whitelist()
def get_site_entity_counts() -> dict:
	_assert_admin()
	return {
		"companies": frappe.db.count("Company"),
		"branches": frappe.db.count("Branch"),
		"users": frappe.db.count("User", {"enabled": 1, "name": ["not in", ["Guest", "Administrator"]]}),
	}
