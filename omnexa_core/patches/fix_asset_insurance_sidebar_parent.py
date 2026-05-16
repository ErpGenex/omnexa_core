# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Asset Insurance must nest under Fixed Assets: ``parent_page`` must equal parent ``title`` exactly."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.workspace_control_tower import (
	_ensure_asset_insurance_workspace,
	_resolve_workspace_parent_page_field,
)


def execute() -> None:
	parent_token = _resolve_workspace_parent_page_field("Fixed Assets")
	if not parent_token:
		return

	for ws_name in ("Fixed Assets", "Fixed assets"):
		if frappe.db.exists("Workspace", ws_name):
			frappe.db.set_value(
				"Workspace",
				ws_name,
				{"title": parent_token, "label": parent_token},
				update_modified=False,
			)

	if frappe.db.exists("Workspace", "Asset Insurance"):
		frappe.db.set_value(
			"Workspace",
			"Asset Insurance",
			"parent_page",
			parent_token,
			update_modified=False,
		)

	_ensure_asset_insurance_workspace()
	frappe.clear_cache()
