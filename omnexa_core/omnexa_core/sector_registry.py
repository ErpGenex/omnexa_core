# Copyright (c) 2026, ErpGenEx
"""Single source of truth for desk sidebar sector grouping.

Workspaces listed here are nested under their sector parent via ``parent_page``.
Workspaces **not** listed remain at their current sidebar position (never removed).
"""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.app_uninstall_groups import APP_UNINSTALL_GROUPS

# Sector parent workspace title (= Workspace.name for autoname workspaces).
SECTOR_DEFINITIONS: dict[str, dict] = {
	"core_erp": {
		"order": 10,
		"label": "Core ERP",
		"sidebar_label": "ERP",
		"label_ar": "الأساسيات",
		"purpose": "Accounting, sales, stock, HR",
		"icon": "accounting",
		"parent_workspace": "Core ERP",
		"workspaces": [
			"Accounting",
			"Sell",
			"Buy",
			"Stock",
			"HR",
			"Fixed Assets",
			"Fixed assets",
			"CRM",
			"Settings",
			"Governance",
			"Commerce",
			"Omnexa Documents",
			"Omnexa Entities",
			"Customer Management",
		],
	},
	"projects_services": {
		"order": 20,
		"label": "Projects & Services",
		"sidebar_label": "Proj-Svc",
		"label_ar": "المشاريع",
		"purpose": "Projects, services and maintenance",
		"icon": "projects",
		"parent_workspace": "Projects & Services",
		"workspaces": [
			"projects",
			"Projects",
			"Services",
			"Maintenance Core",
		],
	},
	"finance_group": {
		"order": 30,
		"label": "Finance Group",
		"sidebar_label": "Finance",
		"label_ar": "المالية",
		"purpose": "Banking, lending and finance verticals",
		"icon": "loan",
		"parent_workspace": "Finance Group",
		"workspaces": [],  # children managed by finance_group_sidebar.py
		"managed_by": "finance_group_sidebar",
	},
	"audit_compliance": {
		"order": 40,
		"label": "Audit & Compliance",
		"sidebar_label": "Compliance",
		"label_ar": "الامتثال",
		"purpose": "Audit, reporting and compliance",
		"icon": "quality",
		"parent_workspace": "Audit & Compliance",
		"workspaces": [
			"Statutory Audit",
			"Reporting Compliance",
			"Audit",
			"Omnexa Statutory Audit",
			"Omnexa Reporting Compliance",
		],
	},
	"real_estate": {
		"order": 50,
		"label": "Real Estate",
		"sidebar_label": "Realty",
		"label_ar": "العقارات",
		"purpose": "Property, development and sales",
		"icon": "assets",
		"parent_workspace": "Real Estate",
		"workspaces": [
			"Property Management",
			"RE Marketing",
			"RE Development",
		],
	},
	"construction_engineering": {
		"order": 60,
		"label": "Construction & Engineering",
		"sidebar_label": "Engineering",
		"label_ar": "الهندسة",
		"purpose": "Construction and engineering tools",
		"icon": "tool",
		"parent_workspace": "Construction & Engineering",
		"workspaces": [
			"Construction",
			"engineering-consulting",
			"Engineering Consulting",
			"Document Control",
			"Omnexa Eng Document Control",
			"Workflow Engine",
			"Omnexa Eng Workflow Engine",
			"Platform Integrations",
			"Omnexa Eng Platform Integrations",
		],
	},
	"trading_manufacturing": {
		"order": 70,
		"label": "Trading & Manufacturing",
		"sidebar_label": "Mfg-Trade",
		"label_ar": "التجارة",
		"purpose": "Trading, manufacturing and agriculture",
		"icon": "retail",
		"parent_workspace": "Trading & Manufacturing",
		"workspaces": [
			"Trading",
			"Manufacturing",
			"Agriculture",
		],
	},
	"industry_solutions": {
		"order": 80,
		"label": "Industry Solutions",
		"sidebar_label": "Industries",
		"label_ar": "القطاعات",
		"purpose": "Healthcare, education, tourism and more",
		"icon": "organization",
		"parent_workspace": "Industry Solutions",
		"workspaces": [
			"Healthcare",
			"Education",
			"Nursery",
			"Tourism",
			"Restaurant",
			"Car Rental",
			"Hotel Front Office",
		],
	},
	"ai_intelligence": {
		"order": 90,
		"label": "AI & Intelligence",
		"sidebar_label": "AI",
		"label_ar": "الذكاء",
		"purpose": "AI platform and setup intelligence",
		"icon": "workflow",
		"parent_workspace": "AI & Intelligence",
		"workspaces": [
			"Omnexa Intelligence Core",
			"Intelligence Core",
			"Omnexa Setup Intelligence",
			"Setup Intelligence",
			"AI Employee",
			"Omnexa AI Employee",
		],
	},
	"documents_integration": {
		"order": 100,
		"label": "Documents & Integration",
		"sidebar_label": "Docs",
		"label_ar": "المستندات",
		"purpose": "Documents, e-invoice and integrations",
		"icon": "integration",
		"parent_workspace": "Documents & Integration",
		"workspaces": [
			"Electronic Archive",
			"E-Invoice",
			"N8N Bridge",
			"Omnexa n8n Bridge",
			"Omnexa N8N Bridge",
			"Omnexa Edms",
			"Omnexa EDMS",
			"Integrations",
			"Integrations Hub",
			"Tax Countries",
		],
	},
	"platform_administration": {
		"order": 110,
		"label": "Platform & Administration",
		"sidebar_label": "Platform",
		"label_ar": "المنصة",
		"purpose": "SaaS, marketplace and admin tools",
		"icon": "setting-gear",
		"parent_workspace": "Platform & Administration",
		"workspaces": [
			"Demo Studio",
			"ERPGenex SaaS",
			"Experience",
			"Omnexa Experience",
			"Theme Manager",
			"Theme 0426",
			"Applications",
			"ERPGenex Applications",
			"omnexa-backup",
			"Omnexa Backup",
			"User Academy",
			"Omnexa User Academy",
			"Marketplace",
			"Users",
			"Website",
			"Tools",
			"Build",
			"Admin",
		],
	},
}

# Never reparent — preserve intentional sub-nesting (e.g. Fixed Assets → Asset Insurance).
PRESERVE_EXISTING_PARENT: frozenset[str] = frozenset(
	{
		"Asset Insurance",
	}
)

# Always stay at sidebar root.
ALWAYS_ROOT_WORKSPACES: frozenset[str] = frozenset(
	{
		"Dashboard",
		"Welcome Workspace",
		"Home",
	}
)

# Hide from desk sidebar (duplicate title or superseded by another workspace).
SIDEBAR_HIDDEN_WORKSPACES: frozenset[str] = frozenset(
	{
		# title=Settings duplicates the canonical Settings workspace.
		"Core",
	}
)

# Legacy alias — re-exported by business_categories.py
BUSINESS_CATEGORIES = {
	sector_id: {
		"order": spec["order"],
		"label": spec["label"],
		"purpose": spec["purpose"],
		"workspaces": list(spec.get("workspaces") or []),
	}
	for sector_id, spec in SECTOR_DEFINITIONS.items()
}


def _workspace_name_variants(name: str) -> tuple[str, ...]:
	name = (name or "").strip()
	if not name:
		return ()
	if name == "Fixed Assets":
		return ("Fixed Assets", "Fixed assets")
	if name.lower() == "projects":
		return ("projects", "Projects")
	return (name,)


def resolve_workspace_name(name: str) -> str | None:
	for candidate in _workspace_name_variants(name):
		if frappe.db.exists("Workspace", candidate):
			return candidate
	return None


def get_sector_sidebar_title(spec: dict) -> str:
	return (spec.get("sidebar_label") or spec.get("label") or spec.get("parent_workspace") or "").strip()


def get_sector_legacy_titles(spec: dict) -> list[str]:
	"""Previous sidebar titles that may still be stored in ``parent_page``."""
	sidebar = get_sector_sidebar_title(spec)
	legacy: list[str] = []
	for key in ("parent_workspace", "label"):
		val = (spec.get(key) or "").strip()
		if val and val != sidebar and val not in legacy:
			legacy.append(val)
	return legacy


def get_sector_parent_titles() -> list[str]:
	out: list[str] = []
	for spec in sorted(SECTOR_DEFINITIONS.values(), key=lambda s: s["order"]):
		title = get_sector_sidebar_title(spec)
		if title and title not in out:
			out.append(title)
	return out


def get_sector_parent_title_map() -> dict[str, str]:
	"""Workspace.name → short sidebar title."""
	out: dict[str, str] = {}
	for spec in SECTOR_DEFINITIONS.values():
		parent = (spec.get("parent_workspace") or "").strip()
		if parent:
			out[parent] = get_sector_sidebar_title(spec)
	return out


def get_workspace_sector(workspace_name: str) -> str | None:
	resolved = resolve_workspace_name(workspace_name) or workspace_name
	for sector_id, spec in SECTOR_DEFINITIONS.items():
		if spec.get("managed_by"):
			continue
		for ws in spec.get("workspaces") or []:
			if resolve_workspace_name(ws) == resolved or ws == resolved:
				return sector_id
	return None


def build_workspace_sector_map() -> dict[str, str]:
	"""Map resolved Workspace.name → sector parent sidebar title token."""
	mapping: dict[str, str] = {}
	for sector_id, spec in SECTOR_DEFINITIONS.items():
		if spec.get("managed_by"):
			continue
		parent = get_sector_sidebar_title(spec)
		if not parent:
			continue
		for ws in spec.get("workspaces") or []:
			resolved = resolve_workspace_name(ws)
			if resolved and resolved not in mapping:
				mapping[resolved] = parent
	return mapping


def get_uninstall_group_labels() -> dict[str, str]:
	return {key: spec.get("label") or key for key, spec in APP_UNINSTALL_GROUPS.items()}


@frappe.whitelist()
def get_sector_definitions() -> dict:
	result = {}
	for sector_id, spec in SECTOR_DEFINITIONS.items():
		result[sector_id] = {
			"order": spec["order"],
			"label": get_sector_sidebar_title(spec),
			"label_full": spec.get("label") or get_sector_sidebar_title(spec),
			"label_ar": spec.get("label_ar") or spec["label"],
			"purpose": spec["purpose"],
			"icon": spec.get("icon") or "folder-normal",
			"parent_workspace": spec.get("parent_workspace") or "",
			"workspaces": list(spec.get("workspaces") or []),
			"managed_by": spec.get("managed_by") or "",
		}
	return result
