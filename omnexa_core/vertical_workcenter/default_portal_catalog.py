# Copyright (c) 2026, ErpGenEx
"""Default role portal catalog for vertical apps without a dedicated SSOT module."""

from __future__ import annotations

import frappe

from omnexa_core.vertical_workcenter.portal_role_policy import (
	frappe_roles_for_portal_key,
	user_can_see_portal,
)
from omnexa_core.vertical_workcenter.registry import get_registry_entry

DEFAULT_ROLE_PORTALS: list[dict] = [
	{
		"key": "executive-dashboard",
		"icon": "📊",
		"label_en": "Executive Dashboard",
		"label_ar": "لوحة الإدارة التنفيذية",
		"role_en": "Executive",
		"role_ar": "الإدارة التنفيذية",
	},
	{
		"key": "operations-desk",
		"icon": "⚙️",
		"label_en": "Operations Desk",
		"label_ar": "مكتب العمليات",
		"role_en": "Operations Manager",
		"role_ar": "مدير العمليات",
	},
	{
		"key": "finance-desk",
		"icon": "💰",
		"label_en": "Finance Desk",
		"label_ar": "مكتب المالية",
		"role_en": "Finance Officer",
		"role_ar": "مسؤول المالية",
	},
	{
		"key": "customer-portal",
		"icon": "👤",
		"label_en": "Customer Portal",
		"label_ar": "بوابة العميل",
		"role_en": "Customer",
		"role_ar": "العميل",
	},
	{
		"key": "analytics-dashboard",
		"icon": "📈",
		"label_en": "Analytics Dashboard",
		"label_ar": "لوحة التحليلات",
		"role_en": "Analyst",
		"role_ar": "محلل البيانات",
	},
]


def _app_portal_catalog_hook(app: str) -> list[dict] | None:
	"""Try app-specific catalog modules (education, healthcare, finance)."""
	hooks = {
		"omnexa_education": "omnexa_education.api.education_portal_catalog.get_grouped_portal_catalog",
		"omnexa_healthcare": "omnexa_healthcare.api.portal_catalog.get_grouped_portal_catalog",
		"omnexa_trading": "omnexa_trading.pharma_portal_catalog.get_grouped_pharma_portal_catalog",
		"omnexa_fixed_assets": "omnexa_fixed_assets.fixed_assets_portal_catalog.get_grouped_portal_catalog",
		"erpgenex_legal": "erpgenex_legal.api.portal_catalog.get_grouped_portal_catalog",
	}
	method = hooks.get(app)
	if not method:
		return None
	try:
		groups = frappe.call(method, include_missing=0)
		if groups:
			return groups
	except Exception:
		return None
	return None


def get_default_grouped_portal_catalog(app: str) -> list[dict]:
	entry = get_registry_entry(app)
	if not entry:
		return []
	slug = entry["slug"]
	portals = []
	for role in DEFAULT_ROLE_PORTALS:
		page_name = f"{slug}-{role['key']}"
		portal_roles = frappe_roles_for_portal_key(role["key"])
		portals.append(
			{
				"id": page_name,
				"label_en": role["label_en"],
				"label_ar": role["label_ar"],
				"role_en": role["role_en"],
				"role_ar": role["role_ar"],
				"route": f"/app/{page_name}",
				"icon": role["icon"],
				"roles": portal_roles,
				"exists": bool(frappe.db.exists("Page", page_name)),
			}
		)
		portals[-1]["allowed"] = user_can_see_portal(portals[-1])
	return [
		{
			"label_en": "Role Portals",
			"label_ar": "بوابات الأدوار",
			"portals": portals,
		}
	]


def _enrich_portal_groups(app: str, groups: list[dict]) -> list[dict]:
	from omnexa_core.vertical_workcenter.portal_menu_item import enrich_portal_groups

	return enrich_portal_groups(app, groups)


def get_grouped_portal_catalog_for_app(app: str, *, filter_by_user: bool = True) -> list[dict]:
	custom = _app_portal_catalog_hook(app)
	if custom:
		groups = custom
	else:
		groups = get_default_grouped_portal_catalog(app)

	if not filter_by_user:
		return _enrich_portal_groups(app, groups)

	from omnexa_core.vertical_workcenter.portal_role_policy import filter_grouped_portals_for_user

	return _enrich_portal_groups(app, filter_grouped_portals_for_user(groups))
