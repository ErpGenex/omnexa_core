# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe


def _ensure_workspace_link(ws, *, label: str, link_to: str) -> None:
	for row in ws.links or []:
		if row.type == "Link" and row.link_type == "DocType" and row.link_to == link_to:
			row.label = label
			row.hidden = 0
			return
	ws.append(
		"links",
		{
			"type": "Link",
			"label": label,
			"link_type": "DocType",
			"link_to": link_to,
			"hidden": 0,
			"onboard": 0,
		},
	)


def _ensure_workspace_shortcut(ws, *, label: str, link_to: str) -> None:
	for row in ws.shortcuts or []:
		if row.type == "DocType" and row.link_to == link_to:
			row.label = label
			row.doc_view = row.doc_view or "List"
			return
	ws.append(
		"shortcuts",
		{
			"type": "DocType",
			"label": label,
			"link_to": link_to,
			"doc_view": "List",
			"icon": "es-line-filetype",
			"color": "Cyan",
		},
	)


def execute():
	if not frappe.db.exists("Workspace", "Settings"):
		return
	ws = frappe.get_doc("Workspace", "Settings")

	_ensure_workspace_link(ws, label="Company Settings", link_to="Company")
	_ensure_workspace_link(ws, label="Branches", link_to="Branch")

	_ensure_workspace_shortcut(ws, label="Company Settings", link_to="Company")
	_ensure_workspace_shortcut(ws, label="Branches", link_to="Branch")

	ws.save(ignore_permissions=True)

