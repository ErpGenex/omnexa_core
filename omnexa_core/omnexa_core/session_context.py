# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from omnexa_core.omnexa_core.activity_labels import get_company_activity_info, get_companies_activity_map
from omnexa_core.omnexa_core.branch_access import (
	get_allowed_branches,
	get_default_branch,
	get_default_company,
	user_can_access_all_branches,
)

VIEW_ALL_BRANCHES = "__ALL__"
_COMPANY_KEY = "omnexa_view_company"
_BRANCH_KEY = "omnexa_view_branch"
_VIEW_ALL_KEY = "omnexa_view_all_branches"


def _set_user_default(key: str, value: str | None, user: str) -> None:
	frappe.defaults.set_user_default(key, value or "", user)
	if not value:
		frappe.defaults.clear_user_default(key, user)


def _get_user_default(key: str, user: str) -> str | None:
	value = frappe.defaults.get_user_default(key, user)
	return value or None


def get_view_context(user: str | None = None) -> dict:
	"""Active desk view scope (privileged users may set company/branch/all)."""
	user = user or frappe.session.user
	can_switch = user_can_access_all_branches(user)
	company = _get_user_default(_COMPANY_KEY, user) if can_switch else None
	branch = _get_user_default(_BRANCH_KEY, user) if can_switch else None
	view_all = cint(_get_user_default(_VIEW_ALL_KEY, user)) if can_switch else 0

	if not can_switch:
		company = get_default_company(user)
		branch = get_default_branch(company, user) if company else None
		view_all = 0
	elif not company:
		company = get_default_company(user)
	elif view_all:
		branch = VIEW_ALL_BRANCHES
	elif branch == VIEW_ALL_BRANCHES:
		view_all = 1

	activity_info = get_company_activity_info(company)
	return {
		"can_switch": can_switch,
		"company": company,
		"branch": branch if branch != VIEW_ALL_BRANCHES else None,
		"view_all_branches": bool(view_all),
		"label": _context_label(company, branch, view_all),
		"activity": activity_info.get("activity"),
		"activity_raw": activity_info.get("activity_raw"),
		"activity_label": activity_info.get("label")
	}


def _context_label(company: str | None, branch: str | None, view_all: int) -> str:
	if view_all and company:
		return f"{company} · {_('All branches')}"
	if company and branch:
		branch_label = frappe.db.get_value("Branch", branch, "branch_name") or branch
		return f"{company} · {branch_label}"
	if company:
		return company
	return _("All companies")


def set_view_context(
	company: str | None = None,
	branch: str | None = None,
	view_all_branches: int | str | None = None,
	user: str | None = None,
) -> dict:
	user = user or frappe.session.user
	if not user_can_access_all_branches(user):
		frappe.throw(_("Only administrators can change company/branch view."), frappe.PermissionError)

	view_all = cint(view_all_branches)
	normalized_branch = (branch or "").strip()
	if normalized_branch in ("", VIEW_ALL_BRANCHES, "ALL", "all"):
		view_all = 1
		normalized_branch = ""

	if company and not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} not found").format(company))

	if view_all:
		if not company:
			frappe.throw(_("Select a company or choose All companies."))
		_set_user_default(_BRANCH_KEY, VIEW_ALL_BRANCHES, user)
		_set_user_default(_VIEW_ALL_KEY, "1", user)
		_set_user_default(_COMPANY_KEY, company, user)
	elif normalized_branch:
		if not frappe.db.exists("Branch", normalized_branch):
			frappe.throw(_("Branch {0} not found").format(normalized_branch))
		branch_company = frappe.db.get_value("Branch", normalized_branch, "company")
		if not branch_company:
			frappe.throw(_("Branch {0} not found").format(normalized_branch))
		if company and branch_company != company:
			frappe.throw(_("Branch {0} does not belong to company {1}.").format(normalized_branch, company))
		company = company or branch_company
		_set_user_default(_BRANCH_KEY, normalized_branch, user)
		_set_user_default(_VIEW_ALL_KEY, "0", user)
		_set_user_default(_COMPANY_KEY, company, user)
	elif company:
		_set_user_default(_COMPANY_KEY, company, user)
		_set_user_default(_BRANCH_KEY, VIEW_ALL_BRANCHES, user)
		_set_user_default(_VIEW_ALL_KEY, "1", user)
		view_all = 1
	else:
		_set_user_default(_COMPANY_KEY, None, user)
		_set_user_default(_BRANCH_KEY, None, user)
		_set_user_default(_VIEW_ALL_KEY, "0", user)

	frappe.clear_cache(user=user)
	return get_view_context(user)


def get_effective_company(user: str | None = None) -> str | None:
	"""Company scope for list filters (navbar context or user default)."""
	return get_default_company(user)


def get_effective_branch_list(user: str | None = None, company: str | None = None) -> list[str] | None:
	"""Branches allowed for list queries: None = unrestricted (all branches in scope)."""
	user = user or frappe.session.user
	company = company or get_effective_company(user)

	if user_can_access_all_branches(user):
		stored_company = frappe.defaults.get_user_default("omnexa_view_company", user)
		view_all = cint(frappe.defaults.get_user_default("omnexa_view_all_branches", user))
		stored_branch = frappe.defaults.get_user_default("omnexa_view_branch", user)
		if stored_branch and stored_branch not in ("__ALL__", "") and not frappe.db.exists("Branch", stored_branch):
			stored_branch = None
			view_all = 1

		if not stored_company and not view_all and not stored_branch:
			return None
		if view_all or (stored_branch in ("__ALL__", "")):
			if company:
				return frappe.get_all("Branch", filters={"company": company
	}, pluck="name") or []
			return None
		if stored_branch and stored_branch not in ("__ALL__", ""):
			return [stored_branch]
		return None

	allowed = get_allowed_branches(user, company) or []
	if company:
		allowed = [
			b
			for b in allowed
			if frappe.db.get_value("Branch", b, "company") == company
		]
	return allowed


@frappe.whitelist()
def get_view_context_for_desk() -> dict:
	return get_view_context()


@frappe.whitelist()
def get_view_context_options() -> dict:
	user = frappe.session.user
	can_switch = user_can_access_all_branches(user)
	companies = frappe.get_all("Company", pluck="name", order_by="name asc")
	branches_by_company: dict[str, list[dict]] = {}
	for company in companies:
		branches_by_company[company] = frappe.get_all(
			"Branch",
			filters={"company": company
	},
			fields=["name", "branch_name", "branch_code", "is_head_office"],
			order_by="is_head_office desc, branch_name asc",
		)
	return {
		"can_switch": can_switch,
		"context": get_view_context(user),
		"companies": companies,
		"branches_by_company": branches_by_company,
		"company_activities": get_companies_activity_map()
	}


@frappe.whitelist(methods=["POST"])
def set_desk_view_context(
	company: str | None = None,
	branch: str | None = None,
	view_all_branches: int | str | None = None,
) -> dict:
	result = set_view_context(company=company, branch=branch, view_all_branches=view_all_branches)
	frappe.response["message"] = result
	return result
