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
		if (getattr(row, "type", None) or (row or {}).get("type")) != "Link":
			continue
		link_type = (getattr(row, "link_type", None) or (row or {}).get("link_type") or "").strip()
		link_to = (getattr(row, "link_to", None) or (row or {}).get("link_to") or "").strip()
		if not link_type or not link_to:
			continue
		if link_type == "DocType" and not frappe.db.exists("DocType", link_to):
			ws.remove(row)
			continue
		if link_type == "Page" and not frappe.db.exists("Page", link_to):
			ws.remove(row)
			continue
		if link_type == "Report" and not frappe.db.exists("Report", link_to):
			ws.remove(row)
			continue
		ref_dt = (getattr(row, "report_ref_doctype", None) or (row or {}).get("report_ref_doctype") or "").strip()
		if ref_dt and not frappe.db.exists("DocType", ref_dt):
			try:
				row.report_ref_doctype = None
			except Exception:
				row["report_ref_doctype"] = None

	for row in list(ws.get("shortcuts") or []):
		stype = (getattr(row, "type", None) or (row or {}).get("type") or "").strip()
		link_to = (getattr(row, "link_to", None) or (row or {}).get("link_to") or "").strip()
		if not stype or not link_to:
			continue
		if stype == "DocType" and not frappe.db.exists("DocType", link_to):
			ws.remove(row)
		elif stype == "Page" and not frappe.db.exists("Page", link_to):
			ws.remove(row)
		elif stype == "Report" and not frappe.db.exists("Report", link_to):
			ws.remove(row)

	for row in list(ws.get("quick_lists") or []):
		dt = (getattr(row, "document_type", None) or (row or {}).get("document_type") or "").strip()
		if dt and not frappe.db.exists("DocType", dt):
			ws.remove(row)

	try:
		blocks = json.loads(ws.content or "[]")
	except Exception:
		blocks = []
	if isinstance(blocks, list):
		filtered = []
		for b in blocks:
			btype = (b or {}).get("type")
			data = (b or {}).get("data") or {}
			if btype == "chart":
				cn = (data.get("chart_name") or "").strip()
				if cn and not _workspace_chart_block_is_valid(ws, cn):
					continue
			if btype == "number_card":
				nc = (data.get("number_card_name") or "").strip()
				if nc and not frappe.db.exists("Number Card", nc):
					continue
			if btype == "shortcut":
				sn = (data.get("shortcut_name") or "").strip()
				if sn and not _workspace_shortcut_block_is_valid(ws, sn):
					continue
			if btype == "quick_list":
				ql = (data.get("quick_list_name") or "").strip()
				if ql and not _workspace_quick_list_block_is_valid(ws, ql):
					continue
			filtered.append(b)
		ws.content = json.dumps(filtered)


def prune_all_workspaces_stale_references(*, commit: bool = True) -> int:
	"""Sanitize every Workspace on the site (charts/reports/doctypes removed when missing)."""
	fixed = 0
	for row in frappe.get_all("Workspace", pluck="name", order_by="name asc"):
		try:
			ws = frappe.get_doc("Workspace", row)
			before = frappe.as_json(
				{
					"links": [dict(x.as_dict()) for x in (ws.links or [])],
					"charts": [dict(x.as_dict()) for x in (ws.charts or [])],
					"shortcuts": [dict(x.as_dict()) for x in (ws.shortcuts or [])]
	}
			)
			prune_workspace_stale_links(ws)
			after = frappe.as_json(
				{
					"links": [dict(x.as_dict()) for x in (ws.links or [])],
					"charts": [dict(x.as_dict()) for x in (ws.charts or [])],
					"shortcuts": [dict(x.as_dict()) for x in (ws.shortcuts or [])]
	}
			)
			if before != after or (ws.content and ws.has_value_changed("content")):
				ws.save(ignore_permissions=True)
				fixed += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: prune workspace failed ({row})")
	if commit:
		frappe.db.commit()
	return fixed


def _workspace_chart_block_is_valid(ws, block_token: str) -> bool:
	"""EditorJS chart blocks often store the **display label**; ``Dashboard Chart`` name is longer.

	Shipped workspace exports use ``chart_name`` in JSON that matches ``Workspace Chart.label`` while the
	child row's ``chart_name`` field holds the real ``Dashboard Chart`` document name.
	"""
	t = (block_token or "").strip()
	if not t:
		return False
	if frappe.db.exists("Dashboard Chart", t):
		return True
	for row in ws.get("charts") or []:
		chn = (getattr(row, "chart_name", None) or (row or {}).get("chart_name") or "").strip()
		lbl = (getattr(row, "label", None) or (row or {}).get("label") or "").strip()
		if t in (chn, lbl) and chn and frappe.db.exists("Dashboard Chart", chn):
			return True
	return False


def _workspace_shortcut_block_is_valid(ws, block_token: str) -> bool:
	t = (block_token or "").strip()
	if not t:
		return False
	for row in ws.get("shortcuts") or []:
		lbl = (getattr(row, "label", None) or (row or {}).get("label") or "").strip()
		link_to = (getattr(row, "link_to", None) or (row or {}).get("link_to") or "").strip()
		stype = (getattr(row, "type", None) or (row or {}).get("type") or "").strip()
		if t not in (lbl, link_to):
			continue
		if stype == "DocType" and link_to and frappe.db.exists("DocType", link_to):
			return True
		if stype == "Page" and link_to and frappe.db.exists("Page", link_to):
			return True
		if stype == "Report" and link_to and frappe.db.exists("Report", link_to):
			return True
	return False


def _workspace_quick_list_block_is_valid(ws, block_token: str) -> bool:
	t = (block_token or "").strip()
	if not t:
		return False
	for row in ws.get("quick_lists") or []:
		lbl = (getattr(row, "label", None) or (row or {}).get("label") or "").strip()
		if lbl == t:
			dt = (getattr(row, "document_type", None) or (row or {}).get("document_type") or "").strip()
			return bool(dt and frappe.db.exists("DocType", dt))
	return False
