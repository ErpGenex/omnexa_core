# Copyright (c) 2026, ErpGenEx
"""Filter desk sidebar — hide finance role-demo stubs; keep Finance Group verticals only.
Also organize sidebar by business categories."""

from __future__ import annotations

import frappe

from .finance_demo.finance_role_demo import ROLE_DEMO_WORKSPACE_NAMES

# Workspaces that belong to Finance Group vertical desk (control tower + group home).
_FINANCE_GROUP_ROOT = frozenset({"Finance Group"})


def filter_workspace_sidebar(result: dict) -> dict:
	"""Remove role-demo stub workspaces from desk sidebar for all users."""
	pages = result.get("pages") or []
	filtered = [p for p in pages if (p.get("name") or "") not in ROLE_DEMO_WORKSPACE_NAMES]
	if len(filtered) != len(pages):
		result = {**result, "pages": filtered
	}
	
	# Sidebar grouping uses native Frappe parent_page via sector_sidebar_sync (not flat headers).
	return result


def organize_by_business_categories(result: dict) -> dict:
	"""Deprecated — kept for backward compatibility; use sector_sidebar_sync instead."""
	return result


@frappe.whitelist()
def get_workspace_sidebar_items():
	from frappe.desk.desktop import get_workspace_sidebar_items as _orig

	return filter_workspace_sidebar(_orig())
