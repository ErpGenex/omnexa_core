# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Shared helpers for ERPGenex test suites."""

from __future__ import annotations

import frappe


def clear_privileged_view_context(user: str = "Administrator") -> None:
	"""Reset desk company/branch view scope so tests are not polluted by MLAB defaults."""
	from omnexa_core.omnexa_core.session_context import (
		_BRANCH_KEY,
		_COMPANY_KEY,
		_VIEW_ALL_KEY,
		_set_user_default,
	)

	frappe.set_user(user)
	_set_user_default(_COMPANY_KEY, None, user)
	_set_user_default(_BRANCH_KEY, None, user)
	_set_user_default(_VIEW_ALL_KEY, "0", user)
	frappe.clear_cache(user=user)


def delete_company_with_branches(company: str) -> None:
	"""Delete branches first — Company is linked to auto-created head office."""
	for branch in frappe.get_all("Branch", filters={"company": company
	}, pluck="name"):
		frappe.delete_doc("Branch", branch, force=True, ignore_permissions=True)
	frappe.delete_doc("Company", company, force=True, ignore_permissions=True)


_WORKFLOW_PRINT_PATCH = None


def suppress_workflow_attach_print() -> None:
	"""Stub PDF attachments triggered by workflow emails during bench run-tests."""
	global _WORKFLOW_PRINT_PATCH
	if _WORKFLOW_PRINT_PATCH is not None:
		return
	from unittest.mock import patch

	def _stub(*args, **kwargs):
		return {"fname": "test.pdf", "fcontent": b"%PDF-1.4\n"
	}

	_WORKFLOW_PRINT_PATCH = patch("frappe.attach_print", _stub)
	_WORKFLOW_PRINT_PATCH.start()
