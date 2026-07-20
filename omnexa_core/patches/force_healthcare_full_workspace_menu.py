"""Restore full Healthcare workspace after control-tower desk sync drift."""

from __future__ import annotations

import frappe


def execute() -> None:
	if "omnexa_healthcare" not in (frappe.get_installed_apps() or []):
		return
	if not frappe.db.exists("Workspace", "Healthcare"):
		return

	from omnexa_healthcare.workspace.healthcare_workspace import sync_healthcare_workspace_menu

	stats = sync_healthcare_workspace_menu(save=True, rebuild=True)
	link_count = frappe.db.count("Workspace Link", {"parent": "Healthcare", "type": "Link"
	})
	if link_count < 145:
		frappe.log_error(
			title="Healthcare workspace still truncated after force sync",
			message=f"links={link_count} stats={stats}",
		)
