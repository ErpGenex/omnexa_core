# Copyright (c) 2026, Omnexa — read-only desk shell context for Next.js UI
from __future__ import annotations

import frappe
from frappe.utils import get_fullname

from omnexa_core.omnexa_core.api.desk_module_registry import get_all_modules, get_module_by_slug
from omnexa_core.omnexa_core.session_context import get_effective_company, get_view_context

_HR_CHILDREN = [
	{"id": "hr-dashboard", "label": "HR Dashboard", "href": "/hr/dashboard", "icon": "layout-dashboard"},
	{"id": "hr-executive", "label": "Executive Dashboard", "href": "/hr/dashboard", "icon": "layout-dashboard"},
	{"id": "employee-directory", "label": "Employee Directory", "href": "/hr/employee-directory", "icon": "contact"},
	{"id": "hr-analytics", "label": "Analytics (ISO 30414)", "href": "/hr/analytics", "icon": "bar-chart-3"},
	{"id": "hr-ess", "label": "Self Service", "href": "/hr/self-service", "icon": "user"},
	{"id": "hr-workcenter", "label": "HR Workcenter", "href": "/hr/workcenter", "icon": "briefcase"},
	{"id": "hr-operations", "label": "Operations Desk", "href": "/hr/operations", "icon": "settings"},
	{"id": "hr-finance", "label": "Finance Desk", "href": "/hr/finance", "icon": "calculator"},
	{"id": "hr-customer", "label": "Customer Portal", "href": "/hr/customer-portal", "icon": "users"},
]

_ERP_SLUG_ORDER = ["accounting", "sell", "buy", "stock", "fixed-assets", "crm", "projects-pm"]
_ERP_SLUGS = set(_ERP_SLUG_ORDER)
_FINANCE_SLUGS = {"finance-group", "finance-engine"}


def _module_nav_children(slug: str) -> list[dict]:
	if slug == "hr":
		return _HR_CHILDREN
	children = [
		{"id": f"{slug}-dashboard", "label": "Dashboard", "href": f"/{slug}/dashboard", "icon": "layout-dashboard"},
	]
	mod = get_module_by_slug(slug)
	if mod and mod.get("workcenter_page"):
		children.append(
			{"id": f"{slug}-workcenter", "label": "Workcenter", "href": f"/{slug}/workcenter", "icon": "briefcase"}
		)
	children.append(
		{"id": f"{slug}-analytics", "label": "Analytics", "href": f"/{slug}/analytics", "icon": "bar-chart-3"},
	)
	return children


def _nav_item(mod: dict) -> dict:
	slug = mod["slug"]
	return {
		"id": slug,
		"label": mod["label"],
		"icon": mod["icon"],
		"href": mod["href"],
		"active_prefix": f"/{slug}",
		"children": _module_nav_children(slug),
	}


def _build_modules_nav() -> list[dict]:
	return [_nav_item(mod) for mod in get_all_modules()]


def _build_grouped_nav() -> tuple[list[dict], list[dict]]:
	erp_children: list[dict] = []
	finance_children: list[dict] = []
	vertical_modules: list[dict] = []

	for mod in get_all_modules():
		slug = mod["slug"]
		item = _nav_item(mod)
		if slug in _ERP_SLUGS:
			erp_children.append(item)
		elif slug in _FINANCE_SLUGS:
			finance_children.append(item)
		else:
			vertical_modules.append(item)

	erp_children.sort(key=lambda x: _ERP_SLUG_ORDER.index(x["id"]) if x["id"] in _ERP_SLUG_ORDER else 99)

	groups: list[dict] = [
		{
			"id": "erp",
			"label": "ERP",
			"icon": "factory",
			"collapsible": True,
			"children": erp_children,
		},
	]

	if finance_children:
		groups.append(
			{
				"id": "finance",
				"label": "Finance",
				"icon": "landmark",
				"collapsible": True,
				"children": finance_children,
			}
		)

	for group_id, label, icon, links in (
		(
			"compliance",
			"Compliance",
			"settings",
			[
				{"id": "compliance-ws", "label": "Compliance", "href": "/app/compliance", "icon": "settings", "external": True},
			],
		),
		(
			"reports",
			"Reports",
			"bar-chart-3",
			[
				{"id": "reports-ws", "label": "Reports", "href": "/app/reports", "icon": "bar-chart-3", "external": True},
			],
		),
		(
			"tools",
			"Tools",
			"briefcase",
			[
				{"id": "tools-ws", "label": "Tools", "href": "/app/tools", "icon": "briefcase", "external": True},
			],
		),
	):
		groups.append({"id": group_id, "label": label, "icon": icon, "collapsible": True, "children": links})

	return groups, vertical_modules


@frappe.whitelist()
def get_desk_context():
	user = frappe.session.user
	view = get_view_context(user)
	company = get_effective_company()
	groups, vertical_modules = _build_grouped_nav()

	return {
		"user": {
			"name": user,
			"full_name": get_fullname(user) or user,
			"initial": (get_fullname(user) or user)[:1].upper(),
		},
		"scope": {
			"company": company,
			"branch": view.get("branch"),
			"label": view.get("label"),
			"view_all_branches": bool(view.get("view_all_branches")),
		},
		"brand": {"name": "ErpGenEx", "logo": "/assets/omnexa_core/images/erpgenex-logo.svg"},
		"navigation": _navigation(groups, vertical_modules),
	}


def _navigation(groups: list[dict] | None = None, vertical_modules: list[dict] | None = None):
	if groups is None or vertical_modules is None:
		groups, vertical_modules = _build_grouped_nav()
	return {
		"public": [
			{"id": "home", "label": "Dashboard", "href": "/", "icon": "layout-dashboard"},
		],
		"groups": groups,
		"modules": vertical_modules or _build_modules_nav(),
	}
