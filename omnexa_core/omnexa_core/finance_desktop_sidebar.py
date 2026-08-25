# Copyright (c) 2026, ErpGenEx
"""Filter desk sidebar — hide finance role-demo stubs; activity scope via app_visibility."""

from __future__ import annotations

import frappe

from .finance_demo.finance_role_demo import ROLE_DEMO_WORKSPACE_NAMES


def filter_workspace_sidebar(result: dict) -> dict:
	"""Remove role-demo stub workspaces and out-of-activity desks from sidebar."""
	pages = result.get("pages") or []
	filtered = [p for p in pages if (p.get("name") or "") not in ROLE_DEMO_WORKSPACE_NAMES]
	if len(filtered) != len(pages):
		result = {**result, "pages": filtered}

	try:
		from omnexa_core.omnexa_core.app_visibility import (
			_activity_filter_applies_to_user,
			_filter_workspace_pages,
			get_desk_hidden_for_user,
		)

		if _activity_filter_applies_to_user():
			hidden = get_desk_hidden_for_user()
			pages = result.get("pages") or []
			filtered = _filter_workspace_pages(pages, hidden)
			if len(filtered) != len(pages):
				result = {**result, "pages": filtered}
	except Exception:
		frappe.log_error(title="Omnexa: activity sidebar filter failed")

	return result


def organize_by_business_categories(result: dict) -> dict:
	"""Deprecated — kept for backward compatibility; use sector_sidebar_sync instead."""
	return result


@frappe.whitelist()
def get_workspace_sidebar_items():
	from frappe.desk.desktop import get_workspace_sidebar_items as _orig

	return filter_workspace_sidebar(_orig())
