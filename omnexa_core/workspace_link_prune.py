# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Strip Workspace child rows / content blocks that point to deleted desk artifacts.

Used by vertical ``governance_setup`` modules after migrate removes DocTypes; stale
Number Cards / Dashboard Charts / DocType links otherwise cause LinkValidationError on save.
"""

from __future__ import annotations

import json

import frappe


def prune_workspace_stale_links(ws) -> None:
	"""Remove invalid links from a Workspace document before ``save``."""
	for row in list(ws.get("number_cards") or []):
		name = getattr(row, "number_card_name", None) or (row or {}).get("number_card_name")
		if name and not frappe.db.exists("Number Card", name):
			ws.remove(row)

	for row in list(ws.get("charts") or []):
		ch = getattr(row, "chart_name", None) or (row or {}).get("chart_name")
		if ch and not frappe.db.exists("Dashboard Chart", ch):
			ws.remove(row)

	for row in list(ws.get("links") or []):
		if getattr(row, "link_type", None) == "DocType" or (row or {}).get("link_type") == "DocType":
			lt = getattr(row, "link_to", None) or (row or {}).get("link_to")
			if lt and not frappe.db.exists("DocType", lt):
				ws.remove(row)

	try:
		blocks = json.loads(ws.content or "[]")
	except Exception:
		blocks = []
	if isinstance(blocks, list):
		filtered = []
		for b in blocks:
			if (b or {}).get("type") == "chart":
				cn = (((b or {}).get("data") or {}).get("chart_name") or "").strip()
				if cn and not frappe.db.exists("Dashboard Chart", cn):
					continue
			filtered.append(b)
		ws.content = json.dumps(filtered)
