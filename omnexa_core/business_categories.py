# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Business Categories — backward-compatible re-export of sector_registry."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.sector_registry import (
	BUSINESS_CATEGORIES,
	SECTOR_DEFINITIONS,
	get_sector_definitions,
	get_workspace_sector,
)


def get_workspace_category(workspace_name: str) -> str | None:
	return get_workspace_sector(workspace_name)


def get_category_workspaces(category_id: str) -> list[str]:
	return list(SECTOR_DEFINITIONS.get(category_id, {}).get("workspaces") or [])


@frappe.whitelist()
def get_business_categories() -> dict:
	return get_sector_definitions()
