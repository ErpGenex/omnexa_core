# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Shared workspace sidebar + shortcuts + content builders for vertical apps."""

from __future__ import annotations

import json
from typing import Any

import frappe

from omnexa_core.omnexa_core.vertical_workspace_catalog import (
	WorkspaceSections,
	get_effective_workspace_sections,
)

_SHORTCUT_COLORS = ("Blue", "Green", "Orange", "Red", "Cyan", "Purple", "Teal", "Pink", "Yellow")


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	return False


def build_link_rows_for_app(app_name: str, base_sections: WorkspaceSections) -> list[dict]:
	rows: list[dict] = []
	seen: set[tuple[str, str]] = set()
	sections = get_effective_workspace_sections(app_name, base_sections)
	for section_label, items in sections:
		valid = [(t, to, label) for t, to, label in items if _link_exists(t, to)]
		if not valid:
			continue
		rows.append({"label": section_label, "type": "Card Break", "link_type": "DocType"
	})
		for link_type, link_to, label in valid:
			key = (link_type, link_to)
			if key in seen:
				continue
			seen.add(key)
			row: dict[str, Any] = {
				"type": "Link",
				"label": label,
				"link_type": link_type,
				"link_to": link_to,
				"is_query_report": 1 if link_type == "Report" else 0
	}
			if link_type == "Report":
				row["report_ref_doctype"] = frappe.db.get_value("Report", link_to, "ref_doctype")
			rows.append(row)
	return rows


def build_shortcuts_from_link_rows(link_rows: list[dict]) -> list[dict]:
	shortcuts: list[dict] = []
	idx = 0
	priority_types = ("Page", "DocType", "Report", "Dashboard")
	links = [r for r in link_rows if r.get("type") == "Link"]
	for lt in priority_types:
		for row in links:
			if row.get("link_type") != lt:
				continue
			entry: dict[str, Any] = {
				"label": row["label"],
				"link_to": row["link_to"],
				"type": row["link_type"],
				"color": _SHORTCUT_COLORS[idx % len(_SHORTCUT_COLORS)]
	}
			if lt == "DocType":
				entry["doc_view"] = "List"
			if lt == "Report" and row.get("report_ref_doctype"):
				entry["report_ref_doctype"] = row["report_ref_doctype"]
			shortcuts.append(entry)
			idx += 1
	return shortcuts


def build_content_from_link_rows(
	link_rows: list[dict],
	ws,
	*,
	title: str,
	slug: str,
) -> str:
	content: list[dict] = []
	try:
		existing = json.loads(ws.content or "[]")
	except json.JSONDecodeError:
		existing = []
	content.extend([b for b in existing if isinstance(b, dict) and b.get("type") == "onboarding"])
	content.append(
		{
			"id": f"{slug
	}-title",
			"type": "header",
			"data": {"text": f'<span class="h4"><b>{title
	}</b></span>', "col": 12}
	}
	)
	section_idx = 0
	link_idx = 0
	for row in link_rows:
		if row.get("type") == "Card Break":
			if section_idx:
				content.append({"id": f"{slug}-sp-{section_idx
	}", "type": "spacer", "data": {"col": 12}
	})
			content.append(
				{
					"id": f"{slug}-sec-{section_idx
	}",
					"type": "header",
					"data": {"text": f'<span class="h5"><b>{row["label"]
	}</b></span>', "col": 12}
	}
			)
			section_idx += 1
			continue
		content.append(
			{
				"id": f"{slug}-lnk-{link_idx
	}",
				"type": "shortcut",
				"data": {"shortcut_name": row["label"], "col": 4}
	}
		)
		link_idx += 1

	if ws.number_cards:
		content.append({"id": f"{slug
	}-kpi-sp", "type": "spacer", "data": {"col": 12}
	})
		content.append(
			{
				"id": f"{slug
	}-kpi-h",
				"type": "header",
				"data": {"text": '<span class="h5"><b>📊 KPIs</b></span>', "col": 12}
	}
		)
		for idx, nc in enumerate(ws.number_cards):
			content.append(
				{
					"id": f"{slug}-nc-{idx
	}",
					"type": "number_card",
					"data": {"number_card_name": nc.number_card_name, "col": 4}
	}
			)

	if ws.charts:
		content.append({"id": f"{slug
	}-ch-sp", "type": "spacer", "data": {"col": 12}
	})
		content.append(
			{
				"id": f"{slug
	}-ch-h",
				"type": "header",
				"data": {"text": '<span class="h5"><b>📈 Charts</b></span>', "col": 12}
	}
		)
		for idx, ch in enumerate(ws.charts):
			content.append(
				{
					"id": f"{slug}-ch-{idx
	}",
					"type": "chart",
					"data": {"chart_name": ch.label or ch.chart_name, "col": 4}
	}
			)

	return json.dumps(content, separators=(",", ":"))


def drop_missing_workspace_dashboard_links(ws) -> None:
	"""Drop workspace dashboard rows pointing at missing Number Cards / Charts."""
	if ws.number_cards:
		ws.number_cards = [
			row
			for row in ws.number_cards
			if row.number_card_name
			and frappe.db.exists("Number Card", row.number_card_name)
		]
	if ws.charts:
		ws.charts = [
			row
			for row in ws.charts
			if row.chart_name and frappe.db.exists("Dashboard Chart", row.chart_name)
		]
