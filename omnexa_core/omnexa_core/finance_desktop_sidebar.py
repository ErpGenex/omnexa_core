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
	
	# Temporarily disable to debug - organization breaks sidebar
	# result = organize_by_business_categories(result)
	
	return result


def organize_by_business_categories(result: dict) -> dict:
	"""Organize sidebar items by business categories."""
	try:
		from ..business_categories import (
			BUSINESS_CATEGORIES,
			get_workspace_category,
		)
	except ImportError:
		return result
	
	pages = result.get("pages") or []
	
	# Keep Dashboard at the top (exclude from organization)
	dashboard_pages = []
	other_pages = []
	
	for page in pages:
		page_name = page.get("name") or ""
		if page_name.lower() == "dashboard":
			dashboard_pages.append(page)
		else:
			other_pages.append(page)
	
	# Create category groups
	category_groups = {}
	for category_id, category_data in BUSINESS_CATEGORIES.items():
		category_groups[category_id] = {
			"label": category_data["label"],
			"order": category_data["order"],
			"purpose": category_data["purpose"],
			"pages": []
	}
	
	# Uncategorized group
	uncategorized_pages = []
	
	# Group pages by category based on workspace name
	for page in other_pages:
		page_name = page.get("name") or ""
		
		# Get category for this workspace
		category_id = get_workspace_category(page_name)
		
		if category_id and category_id in category_groups:
			category_groups[category_id]["pages"].append(page)
		else:
			# Add to uncategorized
			uncategorized_pages.append(page)
	
	# Build final result - start with Dashboard
	final_pages = []
	final_pages.extend(dashboard_pages)
	
	# Add category headers and their pages (sorted by order)
	sorted_categories = sorted(category_groups.items(), key=lambda x: x[1]["order"])
	for category_id, category_data in sorted_categories:
		if category_data["pages"]:
			# Add category header
			final_pages.append({
				"type": "header",
				"label": category_data["label"],
				"purpose": category_data["purpose"],
				"is_category_header": True
	})
			# Add pages in this category
			final_pages.extend(category_data["pages"])
	
	# Add uncategorized pages at the end
	if uncategorized_pages:
		final_pages.append({
			"type": "header",
			"label": "Other",
			"purpose": "Uncategorized applications",
			"is_category_header": True
	})
		final_pages.extend(uncategorized_pages)
	
	result["pages"] = final_pages
	return result


@frappe.whitelist()
def get_workspace_sidebar_items():
	from frappe.desk.desktop import get_workspace_sidebar_items as _orig

	return filter_workspace_sidebar(_orig())
