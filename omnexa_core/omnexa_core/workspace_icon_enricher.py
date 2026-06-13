# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Ensure workspace Card Break emoji labels, shortcut colors, and link icons."""

from __future__ import annotations

import re
from typing import Any

import frappe

_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
_SHORTCUT_COLORS = ("Cyan", "Blue", "Purple", "Orange", "Green", "Red", "Teal", "Pink", "Yellow")

_CARD_EMOJI_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
	(("report",), "📈"),
	(("dashboard", "kpi", "analytic", "executive"), "📊"),
	(("governance", "compliance", "risk", "audit"), "⚖️"),
	(("finance", "billing", "payment", "gl", "accounting"), "💰"),
	(("tax", "zatca", "eta", "e-invoice", "einvoice", "invoice"), "🧾"),
	(("front office", "hotel", "guest", "tourism"), "🏨"),
	(("sales", "sell", "crm", "commerce"), "🛒"),
	(("stock", "inventory", "warehouse"), "📦"),
	(("buy", "purchase", "procurement"), "🛍️"),
	(("hr", "payroll", "employee"), "👥"),
	(("project", "construction", "engineering"), "🏗️"),
	(("customization", "custom", "script", "developer"), "⚙️"),
	(("module", "model", "doctype"), "📋"),
	(("view", "form", "list"), "👁️"),
	(("package", "app", "build"), "🔧"),
	(("log", "system", "monitor"), "📜"),
	(("setting", "config", "setup"), "⚙️"),
	(("integration", "api", "bridge", "hub"), "🔗"),
	(("theme", "desk", "experience"), "🎨"),
	(("insurance", "asset"), "🛡️"),
	(("operation", "delivery", "service"), "⚙️"),
	(("master", "catalog"), "📋"),
	(("portal", "mobile", "pwa"), "📱"),
	(("submission",), "📤"),
	(("profile",), "⚙️"),
)


def _has_emoji(text: str) -> bool:
	return bool(_EMOJI_RE.search(text or ""))


def enrich_card_break_label(label: str) -> str:
	"""Prefix Card Break label with section emoji when missing."""
	text = (label or "").strip()
	if not text or _has_emoji(text):
		return text
	lower = text.lower()
	for keywords, emoji in _CARD_EMOJI_RULES:
		if any(kw in lower for kw in keywords):
			return f"{emoji} {text}"
	return f"📁 {text}"


def _link_es_icon(link_type: str, link_to: str | None) -> str:
	lt = (link_type or "").strip()
	if lt == "Report":
		return "es-line-reports"
	if lt == "Page":
		return "es-line-dashboard"
	if lt == "DocType" and link_to and frappe.db.exists("DocType", link_to):
		di = frappe.db.get_value("DocType", link_to, "icon")
		if isinstance(di, str) and di.startswith("es-"):
			return di
		if isinstance(di, str) and di and " " not in di and not di.startswith("fa"):
			return di
		return "es-line-filetype"
	return "es-line-filetype"


def _card_break_es_icon(label: str) -> str:
	t = (label or "").lower()
	if "report" in t:
		return "es-line-reports"
	if any(k in t for k in ("chart", "kpi", "analytic", "dashboard")):
		return "es-line-dashboard"
	return "es-line-zap"


def enrich_workspace_visual_icons(ws_name: str, *, save: bool = True) -> dict[str, int]:
	"""Apply emoji Card Breaks, shortcut colors, and link icons for one workspace."""
	stats = {"card_breaks_enriched": 0, "shortcut_colors": 0, "link_icons": 0}
	if not frappe.db.exists("Workspace", ws_name):
		return stats
	ws = frappe.get_doc("Workspace", ws_name)
	changed = False

	for row in ws.links or []:
		if not row.name:
			continue
		updates: dict[str, str] = {}
		if row.get("type") == "Card Break":
			new_label = enrich_card_break_label(row.label or "")
			if new_label != (row.label or ""):
				updates["label"] = new_label
				stats["card_breaks_enriched"] += 1
			icon = _card_break_es_icon(updates.get("label") or row.label or "")
			if (row.icon or "") != icon:
				updates["icon"] = icon
		elif row.get("type") == "Link":
			lt = (row.link_type or "").strip()
			if lt not in ("DocType", "Page", "Report"):
				continue
			icon = _link_es_icon(lt, row.link_to)
			if (row.icon or "") != icon:
				updates["icon"] = icon
				stats["link_icons"] += 1
		if updates and save:
			frappe.db.set_value("Workspace Link", row.name, updates, update_modified=False)
			changed = True
		elif updates:
			changed = True

	for i, row in enumerate(ws.shortcuts or []):
		if not row.name:
			continue
		updates: dict[str, str] = {}
		color = _SHORTCUT_COLORS[i % len(_SHORTCUT_COLORS)]
		if not (row.color or "").strip():
			updates["color"] = color
			stats["shortcut_colors"] += 1
		st = (row.type or "").strip()
		if st == "DocType" and not (row.doc_view or "").strip():
			updates["doc_view"] = "List"
		if not (row.icon or "").strip():
			if st == "URL":
				updates["icon"] = "es-line-link"
			elif st in ("DocType", "Page", "Report"):
				updates["icon"] = _link_es_icon(st, row.link_to)
		if updates and save:
			frappe.db.set_value("Workspace Shortcut", row.name, updates, update_modified=False)
			changed = True
		elif updates:
			changed = True

	if changed and save:
		frappe.clear_cache(doctype="Workspace")
	return stats


def enrich_all_workspace_visual_icons(*, save: bool = True) -> dict[str, Any]:
	"""Run visual icon enrichment across every public workspace."""
	names = frappe.get_all("Workspace", filters={"is_hidden": 0}, pluck="name")
	totals = {"workspaces": 0, "card_breaks_enriched": 0, "shortcut_colors": 0, "link_icons": 0}
	details: list[dict[str, Any]] = []
	for name in names:
		st = enrich_workspace_visual_icons(name, save=save)
		if any(st.values()):
			details.append({"workspace": name, **st})
		totals["workspaces"] += 1
		for k in ("card_breaks_enriched", "shortcut_colors", "link_icons"):
			totals[k] += st.get(k, 0)
	if save:
		frappe.db.commit()
	return {"summary": totals, "updated": details}
