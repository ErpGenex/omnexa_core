# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Helpers for scoped whitelisted APIs."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.session_context import get_effective_branch_list, get_effective_company, get_view_context


def get_api_scope(company: str | None = None, branch: str | None = None, user: str | None = None) -> dict:
	user = user or frappe.session.user
	company = company or get_effective_company(user)
	branches = None if branch else get_effective_branch_list(user, company)
	return {
		"user": user,
		"company": company,
		"branch": branch,
		"branches": [branch] if branch else branches,
		"view": get_view_context(user),
	}


def apply_scope_filters(base_filters: dict | None, company: str | None = None, branch: str | None = None) -> dict:
	scope = get_api_scope(company=company, branch=branch)
	filters = dict(base_filters or {})
	if scope["company"]:
		filters["company"] = scope["company"]
	if scope["branch"]:
		filters["branch"] = scope["branch"]
	elif scope["branches"] is not None:
		if not scope["branches"]:
			filters["branch"] = ["in", []]
		elif len(scope["branches"]) == 1:
			filters["branch"] = scope["branches"][0]
		else:
			filters["branch"] = ["in", scope["branches"]]
	return filters
