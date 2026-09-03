# Copyright (c) 2026, ErpGenEx
"""SSOT — standard Trading-style portal page JS for all vertical apps."""

from __future__ import annotations

import json
from pathlib import Path

import frappe

from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY


def role_desk_page_js(page_name: str, app: str, role_key: str) -> str:
	return f'''frappe.pages["{page_name}"].on_page_load = function (wrapper) {{
	function mount() {{
		if (window.omnexa_core && omnexa_core.vertical_portal && omnexa_core.vertical_portal.mountRoleDesk) {{
			omnexa_core.vertical_portal.mountRoleDesk(wrapper, "{app}", "{role_key}");
			return true;
		}}
		return false;
	}}
	if (mount()) return;
	frappe.require("/assets/omnexa_core/js/vertical-portal-desk.js", mount);
}};
'''


def workcenter_page_js(page_name: str, app: str, title_en: str) -> str:
	title = title_en.replace('"', '\\"')
	return f'''frappe.pages["{page_name}"].on_page_load = function (wrapper) {{
	function mount() {{
		if (window.omnexa_core && omnexa_core.vertical_portal && omnexa_core.vertical_portal.mountWorkcenter) {{
			omnexa_core.vertical_portal.mountWorkcenter(wrapper, "{app}", {{
				pageTitle: __("{title} Workcenter"),
			}});
			return true;
		}}
		return false;
	}}
	if (mount()) return;
	frappe.require("/assets/omnexa_core/js/vertical-portal-desk.js", mount);
}};
'''


def _write_page_js(page_dir: Path, folder: str, content: str) -> None:
	(page_dir / f"{folder}.js").write_text(content)


def sync_registry_workcenters(*, import_db: bool = False) -> list[str]:
	installed = set(frappe.get_installed_apps() or [])
	synced: list[str] = []
	for entry in VERTICAL_WORKCENTER_REGISTRY:
		if entry.get("status") == "finance_group":
			continue
		app = entry["app"]
		if app not in installed:
			continue
		page_name = entry["workcenter"]
		if page_name in ("finance-workcenter",):
			continue
		try:
			from omnexa_core.vertical_workcenter.scaffold import _module_folder

			module_root = _module_folder(app)
			folder = page_name.replace("-", "_")
			page_dir = module_root / "page" / folder
			if not page_dir.is_dir():
				continue
			_write_page_js(page_dir, folder, workcenter_page_js(page_name, app, entry["title_en"]))
			synced.append(page_name)
		except Exception as exc:
			frappe.log_error(title=f"sync workcenter {app}", message=str(exc))
	if import_db:
		frappe.db.commit()
	return synced


def sync_trading_pharma_role_pages(*, import_db: bool = False) -> list[str]:
	if "omnexa_trading" not in (frappe.get_installed_apps() or []):
		return []
	from omnexa_trading.pharma_portal_catalog import PHARMA_ROLE_PORTALS

	synced: list[str] = []
	base = Path(frappe.get_app_path("omnexa_trading")) / "omnexa_trading" / "page"
	for row in PHARMA_ROLE_PORTALS:
		key = row.get("key")
		page_name = row.get("page")
		if not key or not page_name or key == "workcenter":
			continue
		folder = page_name.replace("-", "_")
		page_dir = base / folder
		if not page_dir.is_dir():
			continue
		_write_page_js(page_dir, folder, role_desk_page_js(page_name, "omnexa_trading", key))
		synced.append(page_name)
	if import_db:
		frappe.db.commit()
	return synced


@frappe.whitelist()
def sync_all_standard_portal_pages(*, import_db: bool = True, files_only: bool = False) -> dict:
	"""Rewrite workcenter + default role desk page JS to Trading-style bootstrap."""
	result: dict = {"workcenters": [], "journey_portals": {}, "trading_pharma": [], "legal": []}

	result["workcenters"] = sync_registry_workcenters(import_db=False)
	if files_only:
		result["journey_portals"] = sync_journey_portal_page_js()
	else:
		from omnexa_core.vertical_workcenter.journey_portal_scaffold import scaffold_all_journey_portals

		result["journey_portals"] = scaffold_all_journey_portals()
	result["trading_pharma"] = sync_trading_pharma_role_pages(import_db=False)

	if "erpgenex_legal" in (frappe.get_installed_apps() or []):
		try:
			from erpgenex_legal.utils.legal_workcenter import sync_legal_desk_pages

			result["legal"] = sync_legal_desk_pages(import_db=import_db and not files_only)
		except Exception as exc:
			result["legal"] = {"error": str(exc)}

	if import_db and not files_only:
		frappe.db.commit()
	return result


def sync_journey_portal_page_js() -> dict:
	"""Rewrite journey role portal JS only — no DB import (migrate-safe)."""
	from omnexa_core.vertical_workcenter.default_portal_catalog import DEFAULT_ROLE_PORTALS
	from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY
	from omnexa_core.vertical_workcenter.scaffold import _module_folder

	installed = set(frappe.get_installed_apps() or [])
	synced: list[str] = []
	for entry in VERTICAL_WORKCENTER_REGISTRY:
		if entry.get("reference") or entry.get("status") == "finance_group":
			continue
		if entry.get("tier", 99) > 2:
			continue
		app = entry["app"]
		if app not in installed or app in ("omnexa_education", "omnexa_healthcare", "omnexa_core"):
			continue
		slug = entry["slug"]
		module_root = _module_folder(app)
		for role in DEFAULT_ROLE_PORTALS:
			page_name = f"{slug}-{role['key']}"
			folder = page_name.replace("-", "_")
			page_dir = module_root / "page" / folder
			if not page_dir.is_dir():
				continue
			_write_page_js(page_dir, folder, role_desk_page_js(page_name, app, role["key"]))
			synced.append(page_name)
	return {"synced": synced}
