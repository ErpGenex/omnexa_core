# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_table_name


PRIVILEGED_ROLES = {"System Manager", "Company Admin", "Education Manager"}


def user_can_wipe_company(user: str | None = None) -> bool:
	"""Full company wipe (transactions + masters + branches)."""
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return "System Manager" in set(frappe.get_roles(user))


def user_can_access_all_branches(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in ("Administrator",):
		return True
	roles = set(frappe.get_roles(user))
	return bool(PRIVILEGED_ROLES & roles)


def _filter_existing_branches(branch_names: list[str] | None) -> list[str]:
	if not branch_names:
		return []
	return [b for b in branch_names if b and frappe.db.exists("Branch", b)]


def _single_company_branch_fallback(company: str | None) -> list[str]:
	"""Allow the only branch on site when User Branch Access was not configured yet."""
	if not company:
		return []
	if frappe.db.count("Branch", {"company": company
	}) != 1:
		return []
	return frappe.get_all("Branch", filters={"company": company
	}, pluck="name", limit=1)


def get_allowed_branches(user: str | None = None, company: str | None = None) -> list[str] | None:
	user = user or frappe.session.user
	if user_can_access_all_branches(user):
		return None
	filters = {"user": user
	}
	if company:
		filters["company"] = company
	allowed = _filter_existing_branches(
		frappe.get_all("User Branch Access", filters=filters, pluck="branch")
	)
	if allowed:
		return allowed
	return _single_company_branch_fallback(company)


def get_default_company(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if user_can_access_all_branches(user):
		company = frappe.defaults.get_user_default("omnexa_view_company", user)
		if company:
			return company

	# 1) explicit defaults (user then global)
	row = frappe.db.sql(
		"""
		SELECT defvalue
		FROM `tabDefaultValue`
		WHERE parent IN (%s, '__default')
		  AND defkey IN ('company', 'Company')
		ORDER BY CASE WHEN parent = %s THEN 0 ELSE 1 END
		LIMIT 1
		""",
		(user, user),
	)
	if row and row[0][0]:
		return row[0][0]

	# 2) derive from user branch access if single-company
	if not user_can_access_all_branches(user):
		companies = frappe.get_all(
			"User Branch Access",
			filters={"user": user
	},
			fields=["company"],
			distinct=True,
		)
		if len(companies) == 1:
			return companies[0].company

	# 3) exactly one company on the site (common single-tenant installs)
	cos = frappe.get_all("Company", pluck="name", limit=2)
	if len(cos) == 1:
		return cos[0]

	return None


def get_default_branch(company: str, user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if user_can_access_all_branches(user):
		if cint(frappe.defaults.get_user_default("omnexa_view_all_branches", user)):
			pass
		else:
			branch = frappe.defaults.get_user_default("omnexa_view_branch", user)
			if branch and branch not in ("__ALL__", ""):
				if frappe.db.get_value("Branch", branch, "company") == company:
					return branch

	# 1) explicit defaults
	row = frappe.db.sql(
		"""
		SELECT defvalue
		FROM `tabDefaultValue`
		WHERE parent IN (%s, '__default')
		  AND defkey IN ('branch', 'Branch')
		ORDER BY CASE WHEN parent = %s THEN 0 ELSE 1 END
		LIMIT 1
		""",
		(user, user),
	)
	if row and row[0][0]:
		branch = row[0][0]
		branch_company = frappe.db.get_value("Branch", branch, "company")
		if branch_company == company:
			return branch

	# 2) branch access grants for normal users
	if not user_can_access_all_branches(user):
		entries = frappe.get_all(
			"User Branch Access",
			filters={"user": user, "company": company
	},
			fields=["branch", "is_default"],
			order_by="is_default desc, modified asc",
		)
		for row in entries:
			if row.branch and frappe.db.exists("Branch", row.branch):
				return row.branch
		fallback = _single_company_branch_fallback(company)
		return fallback[0] if fallback else None

	# 3) privileged users: head office fallback
	head_office = frappe.db.get_value("Branch", {"company": company, "is_head_office": 1
	}, "name")
	if head_office:
		return head_office
	return frappe.db.get_value("Branch", {"company": company
	}, "name")


_BRANCH_COHERENCE_SKIP = frozenset(
	{
		"DocType",
		"Custom Field",
		"Property Setter",
		"Patch Log",
		"Version",
		"Error Log",
		"File",
		"Module Def",
		"Production Seed Log",
		"COA Reset Audit Log",
	}
)


def _assert_branch_belongs_to_company(branch: str, company: str | None, context: str) -> None:
	branch_company = frappe.db.get_value("Branch", branch, "company")
	if not branch_company:
		frappe.throw(_("Branch {0} was not found.").format(branch), title=_("Branch"))
	if not company:
		frappe.throw(
			_("Select Company before choosing Branch ({0}).").format(context),
			title=_("Branch"),
		)
	if branch_company != company:
		frappe.throw(
			_("Branch {0} does not belong to Company {1}.").format(branch, company),
			title=_("Branch"),
		)


def enforce_branch_company_coherence(doc, method=None) -> None:
	"""Reject documents where branch is not a child of the selected company."""
	if getattr(frappe.flags, "in_install", False) or getattr(frappe.flags, "in_migrate", False):
		return
	if getattr(frappe.flags, "in_import", False):
		return
	if getattr(getattr(doc, "flags", None), "ignore_branch_company_coherence", False):
		return

	doctype = getattr(doc, "doctype", None)
	if not doctype or doctype in _BRANCH_COHERENCE_SKIP:
		return

	meta = getattr(doc, "meta", None)
	if not meta:
		return

	if doctype == "Branch":
		parent_branch = doc.get("parent_branch")
		company = doc.get("company")
		if parent_branch and company:
			_assert_branch_belongs_to_company(parent_branch, company, doctype)
		return

	if meta.has_field("branch") and doc.get("branch"):
		company = doc.get("company") if meta.has_field("company") else None
		_assert_branch_belongs_to_company(doc.branch, company, doctype)

	parent_company = doc.get("company") if meta.has_field("company") else None
	for table_field in meta.get_table_fields() or []:
		child_meta = frappe.get_meta(table_field.options)
		if not child_meta.has_field("branch"):
			continue
		for row in doc.get(table_field.fieldname) or []:
			if not row.get("branch"):
				continue
			row_company = row.get("company") if child_meta.has_field("company") else parent_company
			_assert_branch_belongs_to_company(
				row.branch,
				row_company,
				f"{doctype}.{table_field.fieldname}[{row.idx}]",
			)


def enforce_branch_access(doc, method=None, user: str | None = None):
	user = user or frappe.session.user
	if user == "Guest" or getattr(getattr(doc, "flags", None), "ignore_branch_access", False):
		return
	if getattr(getattr(doc, "flags", None), "wizard_save", False):
		return
	if getattr(doc, "doctype", None) in {
		"User Branch Access",
		"User",
		"Company",
		"Branch",
		"Production Seed Log",
		"COA Reset Audit Log",
	}:
		return
	branch = getattr(doc, "branch", None)
	company = getattr(doc, "company", None)
	if not branch:
		return

	if user_can_access_all_branches(user):
		stored_company = frappe.defaults.get_user_default("omnexa_view_company", user)
		view_all = cint(frappe.defaults.get_user_default("omnexa_view_all_branches", user))
		stored_branch = frappe.defaults.get_user_default("omnexa_view_branch", user)
		if stored_branch and stored_branch not in ("__ALL__", "") and not frappe.db.exists("Branch", stored_branch):
			stored_branch = None
			view_all = 1

		if view_all or stored_branch in ("__ALL__", ""):
			return
		if stored_branch and stored_branch not in ("__ALL__", "") and branch != stored_branch:
			frappe.throw(_("You are viewing branch {0} only.").format(stored_branch), title=_("Branch Access"))
		if stored_company and company and company != stored_company:
			frappe.throw(_("You are viewing company {0} only.").format(stored_company), title=_("Branch Access"))
		return

	allowed = set(get_allowed_branches(user, company) or [])
	if not allowed:
		frappe.throw(
			_("No branch is assigned to your user. Ask an administrator to set up User Branch Access."),
			title=_("Branch Access"),
		)
	if branch not in allowed:
		frappe.throw(_("You are not allowed to access this branch."), title=_("Branch Access"))


def permission_query_conditions_for_branch_field(doctype: str, user: str | None = None) -> str:
	"""SQL fragment for list views: branch (+ company) scope per user/session."""
	from omnexa_core.omnexa_core.session_context import get_effective_branch_list, get_effective_company

	user = user or frappe.session.user
	if user_can_access_all_branches(user):
		stored_company = frappe.defaults.get_user_default("omnexa_view_company", user)
		view_all = cint(frappe.defaults.get_user_default("omnexa_view_all_branches", user))
		stored_branch = frappe.defaults.get_user_default("omnexa_view_branch", user)
		has_view_context = bool(stored_company) or view_all or (
			stored_branch and stored_branch not in ("", "__ALL__")
		)
		if not has_view_context:
			return ""

	company = get_effective_company(user)
	allowed = get_effective_branch_list(user, company)

	table = get_table_name(doctype, wrap_in_backticks=True)
	parts: list[str] = []

	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		meta = None

	if meta and meta.has_field("company") and company:
		parts.append(f"{table}.company = {frappe.db.escape(company)}")

	if doctype == "Branch":
		if allowed is None:
			return " and ".join(parts) if parts else ""
		if not allowed:
			return "1=0"
		quoted = ", ".join(frappe.db.escape(v) for v in allowed)
		parts.append(f"{table}.name in ({quoted})")
		return " and ".join(parts)

	if allowed is None:
		return " and ".join(parts) if parts else ""

	if not allowed:
		return "1=0"

	quoted = ", ".join(frappe.db.escape(v) for v in allowed)
	if user_can_access_all_branches(user):
		parts.append(f"{table}.branch in ({quoted})")
	else:
		# Strict: desk users see only their branch rows (no shared null-branch rows).
		parts.append(f"{table}.branch in ({quoted})")
	return " and ".join(parts)
