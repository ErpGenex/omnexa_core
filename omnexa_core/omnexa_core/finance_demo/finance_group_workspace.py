# Copyright (c) 2026, ErpGenEx
"""Finance Group home workspace — demo hub link, vertical shortcuts, Arabic header."""

from __future__ import annotations

import json

import frappe
from frappe import _

from omnexa_core.omnexa_core.finance_demo.finance_app_registry import FINANCE_APP_REGISTRY
from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import sync_finance_group_sidebar
from omnexa_core.omnexa_core.workspace_control_tower import _append_finance_group_workspace_nav_link

WORKSPACE_NAME = "Finance Group"
FINANCE_GROUP_ROUTE = "/app/finance-group"
FINANCE_GROUP_LEGACY_ROUTE = "/app/finance_group"


def _link_row(*, label: str, link_type: str, link_to: str, icon: str = "folder-normal") -> dict:
	return {
		"type": "Link",
		"label": label,
		"link_type": link_type,
		"link_to": link_to,
		"icon": icon,
		"hidden": 0
	}


def _card_break(label: str, icon: str = "folder-normal") -> dict:
	return {"type": "Card Break", "label": label, "icon": icon, "hidden": 0
	}


def _build_links() -> list[dict]:
	rows: list[dict] = [
		_card_break("🏢 Workcenter & Portals", "star"),
		_link_row(label=_("Finance Workcenter"), link_type="Page", link_to="finance-workcenter", icon="star"),
		_link_row(
			label=_("Finance Control Center"),
			link_type="Page",
			link_to="finance-control-center",
			icon="setting",
		),
		_card_break("🏦 Core Engines", "bank"),
	]
	installed = set(frappe.get_installed_apps() or [])
	for spec in FINANCE_APP_REGISTRY:
		app = spec["app"]
		if app not in installed:
			continue
		ws = spec["workspace"]
		if not frappe.db.exists("Workspace", ws):
			continue
		label = spec.get("marketing_ar") or spec.get("marketing_en") or ws
		rows.append(
			_link_row(
				label=label,
				link_type="Page",
				link_to=spec["exec_page"],
				icon=spec.get("icon") or "folder-normal",
			)
		)
		_append_finance_group_workspace_nav_link(label=ws, icon=spec.get("icon") or "folder-normal", link_to=ws)
	rows.extend(
		[
			_card_break("📒 Core Platform", "accounting"),
			_link_row(
				label=_("FinTruth — Accounting (Core)"),
				link_type="Page",
				link_to="acct-executive-dashboard",
				icon="accounting",
			),
			_card_break("📊 Reports & GL", "reports"),
			_link_row(
				label=_("General Ledger"),
				link_type="Report",
				link_to="General Ledger",
				icon="book",
			),
			_link_row(
				label=_("Trial Balance"),
				link_type="Report",
				link_to="Trial Balance",
				icon="list",
			),
		]
	)
	return rows


def _build_shortcuts() -> list[dict]:
	shortcuts = [
		{
			"type": "Page",
			"link_to": "finance-workcenter",
			"label": _("Workcenter"),
			"color": "Blue"
	},
	]
	colors = ("Green", "Orange", "Red", "Cyan", "Purple", "Teal", "Pink", "Yellow")
	idx = 0
	installed = set(frappe.get_installed_apps() or [])
	for spec in FINANCE_APP_REGISTRY:
		if spec["app"] not in installed:
			continue
		if not frappe.db.exists("Page", spec["exec_page"]):
			continue
		shortcuts.append(
			{
				"type": "Page",
				"link_to": spec["exec_page"],
				"label": spec.get("marketing_en") or spec["workspace"],
				"color": colors[idx % len(colors)]
	}
		)
		idx += 1
	return shortcuts


def _build_content() -> str:
	blocks = [
		{
			"id": "erpgenex-onboarding",
			"type": "onboarding",
			"data": {"onboarding_name": "ERPGENEX — Finance Group", "col": 12}
	},
		{
			"id": "fg-header",
			"type": "header",
			"data": {
				"text": (
					'<span class="h4"><b>Finance Group</b></span><br>'
					'<span class="text-muted">'
					"Use the sidebar to open each finance portal. "
					"Start at <b>Finance Workcenter</b> — each user enters by role."
					"</span>"
				),
				"col": 12}
	},
	]
	for idx, spec in enumerate(FINANCE_APP_REGISTRY):
		if spec["app"] not in (frappe.get_installed_apps() or []):
			continue
		if not frappe.db.exists("Page", spec["exec_page"]):
			continue
		blocks.append(
			{
				"id": f"fg-shortcut-{spec['app']
	}",
				"type": "shortcut",
				"data": {
					"shortcut_name": spec.get("marketing_en") or spec["workspace"],
					"col": 3 if idx % 4 else 3}
	}
		)
	return json.dumps(blocks)


def sync_finance_group_home(*, save: bool = True) -> dict:
	"""Ensure Finance Group workspace has demo hub + vertical portal links."""
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return {"ok": False, "reason": "workspace_missing"
	}

	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	ws.icon = "accounting"
	ws.title = WORKSPACE_NAME
	ws.label = WORKSPACE_NAME
	ws.public = 1
	ws.module = ws.module or "Omnexa Core"
	links = _build_links()
	ws.set("links", [])
	for row in links:
		ws.append("links", row)
	ws.set("shortcuts", [])
	for row in _build_shortcuts():
		ws.append("shortcuts", row)
	ws.content = _build_content()
	if save:
		ws.flags.ignore_permissions = True
		ws.save()
	sync_finance_group_sidebar(save=save)
	return {"ok": True, "workspace": WORKSPACE_NAME, "links": len(links), "shortcuts": len(ws.shortcuts)
	}


@frappe.whitelist()
def sync_finance_group_home_api() -> dict:
	frappe.only_for("System Manager")
	result = sync_finance_group_home()
	frappe.db.commit()
	return result
