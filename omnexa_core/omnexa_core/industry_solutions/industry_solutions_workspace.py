# Copyright (c) 2026, ErpGenEx
"""Industry Solutions home workspace — vertical shortcuts, Arabic header."""

from __future__ import annotations

import json

import frappe
from frappe import _

WORKSPACE_NAME = "Industry Solutions"
INDUSTRY_SOLUTIONS_ROUTE = "/app/industry-solutions"

INDUSTRY_APP_REGISTRY = [
	{
		"app": "omnexa_education",
		"workspace": "Education",
		"exec_page": "education-workcenter",
		"icon": "graduation-cap",
		"marketing_ar": "التعليم",
		"marketing_en": "Education"
	},
	{
		"app": "omnexa_nursery",
		"workspace": "Nursery",
		"exec_page": "nursery-workcenter",
		"icon": "child",
		"marketing_ar": "الحضانة",
		"marketing_en": "Nursery"
	},
	{
		"app": "omnexa_car_rental",
		"workspace": "Car Rental",
		"exec_page": "car-rental-workcenter",
		"icon": "car",
		"marketing_ar": "تأجير السيارات",
		"marketing_en": "Car Rental"
	},
	{
		"app": "omnexa_agriculture",
		"workspace": "Agriculture",
		"exec_page": "agriculture-workcenter",
		"icon": "plant",
		"marketing_ar": "الزراعة",
		"marketing_en": "Agriculture"
	},
	{
		"app": "omnexa_healthcare",
		"workspace": "Healthcare",
		"exec_page": "healthcare-workcenter",
		"icon": "hospital",
		"marketing_ar": "الصحة",
		"marketing_en": "Healthcare"
	},
	{
		"app": "omnexa_restaurant",
		"workspace": "Restaurant",
		"exec_page": "restaurant-workcenter",
		"icon": "utensils",
		"marketing_ar": "المطاعم",
		"marketing_en": "Restaurant"
	},
	{
		"app": "omnexa_tourism",
		"workspace": "Tourism",
		"exec_page": "tourism-workcenter",
		"icon": "plane",
		"marketing_ar": "السياحة",
		"marketing_en": "Tourism"
	},
]


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
		_card_break("🏢 Industry Portals", "star"),
	]
	installed = set(frappe.get_installed_apps() or [])
	for spec in INDUSTRY_APP_REGISTRY:
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
	return rows


def _build_shortcuts() -> list[dict]:
	shortcuts = []
	colors = ("Green", "Orange", "Red", "Cyan", "Purple", "Teal", "Pink", "Yellow")
	idx = 0
	installed = set(frappe.get_installed_apps() or [])
	for spec in INDUSTRY_APP_REGISTRY:
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
			"data": {"onboarding_name": "ERPGENEX — Industry Solutions", "col": 12}
	},
		{
			"id": "is-header",
			"type": "header",
			"data": {
				"text": (
					'<span class="h4"><b>Industry Solutions</b></span><br>'
					'<span class="text-muted">'
					"Use the sidebar to open each industry portal. "
					"Each vertical has its own workcenter and role-based access."
					"</span>"
				),
				"col": 12}
	},
	]
	for idx, spec in enumerate(INDUSTRY_APP_REGISTRY):
		if spec["app"] not in (frappe.get_installed_apps() or []):
			continue
		if not frappe.db.exists("Page", spec["exec_page"]):
			continue
		blocks.append(
			{
				"id": f"is-shortcut-{spec['app']
	}",
				"type": "shortcut",
				"data": {
					"shortcut_name": spec.get("marketing_en") or spec["workspace"],
					"col": 3 if idx % 4 else 3}
	}
		)
	return json.dumps(blocks)


def sync_industry_solutions_home(*, save: bool = True) -> dict:
	"""Ensure Industry Solutions workspace has vertical portal links."""
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return {"ok": False, "reason": "workspace_missing"
	}

	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	ws.icon = "industry"
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
	return {"ok": True, "workspace": WORKSPACE_NAME, "links": len(links), "shortcuts": len(ws.shortcuts)
	}


@frappe.whitelist()
def sync_industry_solutions_home_api() -> dict:
	frappe.only_for("System Manager")
	result = sync_industry_solutions_home()
	frappe.db.commit()
	return result
