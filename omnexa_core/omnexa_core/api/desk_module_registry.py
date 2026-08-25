# Copyright (c) 2026, Omnexa — Next.js desk module registry (all workspaces)
from __future__ import annotations

import frappe

from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY

# Core ERP workspaces (not always in vertical workcenter registry)
_CORE_ERP_MODULES: list[dict] = [
	{
		"app": "omnexa_customer_core",
		"slug": "crm",
		"title_en": "CRM",
		"title_ar": "إدارة العملاء",
		"icon": "handshake",
		"color": "purple",
		"workspace": "CRM",
		"tier": 1,
	},
	{
		"app": "omnexa_core",
		"slug": "stock",
		"title_en": "Stock",
		"title_ar": "المخزون",
		"icon": "package",
		"color": "orange",
		"workspace": "Stock",
		"tier": 1,
	},
	{
		"app": "omnexa_core",
		"slug": "sell",
		"title_en": "Sell",
		"title_ar": "المبيعات",
		"icon": "shopping-cart",
		"color": "blue",
		"workspace": "Sell",
		"tier": 1,
	},
	{
		"app": "omnexa_core",
		"slug": "buy",
		"title_en": "Buy",
		"title_ar": "المشتريات",
		"icon": "truck",
		"color": "green",
		"workspace": "Buy",
		"tier": 1,
	},
	{
		"app": "omnexa_core",
		"slug": "finance-group",
		"title_en": "Finance Group",
		"title_ar": "المجموعة المالية",
		"icon": "landmark",
		"color": "blue",
		"workspace": "Finance Group",
		"workcenter": "finance-workcenter",
		"tier": 1,
	},
]

_ICON_BY_SLUG = {
	"hr": "users",
	"accounting": "calculator",
	"healthcare": "heart-pulse",
	"education": "graduation-cap",
	"trading": "store",
	"construction": "hard-hat",
	"manufacturing": "factory",
	"tourism": "plane",
	"agriculture": "wheat",
	"projects-pm": "folder-kanban",
	"finance-engine": "landmark",
}


def _app_installed(app: str) -> bool:
	try:
		return bool(app) and app in frappe.get_installed_apps()
	except Exception:
		return False


def _normalize_entry(row: dict) -> dict:
	slug = row["slug"]
	return {
		"id": slug,
		"app": row["app"],
		"slug": slug,
		"label": row.get("title_en") or slug.replace("-", " ").title(),
		"label_ar": row.get("title_ar") or "",
		"icon": row.get("icon") or _ICON_BY_SLUG.get(slug, "layout-dashboard"),
		"color": row.get("color", "blue"),
		"href": f"/{slug}",
		"next_href": f"/{slug}",
		"workcenter_href": f"/{slug}/workcenter",
		"dashboard_href": f"/{slug}/dashboard",
		"frappe_workspace": row.get("workspace") or row.get("title_en") or slug.replace("-", " ").title(),
		"workcenter_page": row.get("workcenter"),
		"frappe_workcenter_route": f"/app/{row['workcenter']}" if row.get("workcenter") else None,
		"tier": row.get("tier", 2),
		"status": row.get("status", "partial"),
	}


def get_all_modules(*, include_core: bool = True) -> list[dict]:
	seen: set[str] = set()
	modules: list[dict] = []

	for row in VERTICAL_WORKCENTER_REGISTRY:
		if not _app_installed(row["app"]):
			continue
		entry = _normalize_entry(row)
		if entry["slug"] in seen:
			continue
		seen.add(entry["slug"])
		modules.append(entry)

	if include_core:
		for row in _CORE_ERP_MODULES:
			if not _app_installed(row["app"]):
				continue
			if row["slug"] in seen:
				continue
			seen.add(row["slug"])
			modules.append(_normalize_entry(row))

	modules.sort(key=lambda m: (m.get("tier", 9), m["label"]))
	return modules


def get_module_by_slug(slug: str) -> dict | None:
	slug = (slug or "").strip().lower()
	for mod in get_all_modules():
		if mod["slug"] == slug:
			return mod
	return None


def get_module_app(slug: str) -> str | None:
	mod = get_module_by_slug(slug)
	return mod["app"] if mod else None


@frappe.whitelist()
def get_module_registry():
	return {
		"modules": get_all_modules(),
		"count": len(get_all_modules()),
	}
