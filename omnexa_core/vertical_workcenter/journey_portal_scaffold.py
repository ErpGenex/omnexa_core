# Copyright (c) 2026, ErpGenEx
"""Scaffold default journey role portal pages for vertical apps."""

from __future__ import annotations

import json
from pathlib import Path

import frappe

from omnexa_core.vertical_workcenter.default_portal_catalog import DEFAULT_ROLE_PORTALS
from omnexa_core.vertical_workcenter.portal_role_policy import frappe_roles_for_portal_key
from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY
from omnexa_core.vertical_workcenter.scaffold import _app_module, _module_folder


from omnexa_core.vertical_workcenter.portal_page_bootstrap import role_desk_page_js


def _page_js(page_name: str, app: str, role_key: str) -> str:
	return role_desk_page_js(page_name, app, role_key)


def _sync_page_roles(page_name: str, roles: list[str]) -> None:
	if not frappe.db.exists("Page", page_name):
		return
	doc = frappe.get_doc("Page", page_name)
	doc.roles = []
	for role in roles:
		doc.append("roles", {"role": role})
	doc.save(ignore_permissions=True)


def scaffold_journey_portals(app: str) -> list[dict]:
	from omnexa_core.vertical_workcenter.registry import get_registry_entry

	entry = get_registry_entry(app)
	if not entry or entry.get("reference"):
		return []
	if entry.get("status") == "finance_group":
		return []

	slug = entry["slug"]
	module_root = _module_folder(app)
	module = _app_module(app)
	out = []

	for role in DEFAULT_ROLE_PORTALS:
		page_name = f"{slug}-{role['key']}"
		folder = page_name.replace("-", "_")
		page_dir = module_root / "page" / folder
		page_dir.mkdir(parents=True, exist_ok=True)
		(page_dir / "__init__.py").write_text("")
		(page_dir / f"{folder}.py").write_text("")

		page_json = {
			"doctype": "Page",
			"module": module,
			"name": page_name,
			"page_name": page_name,
			"standard": "Yes",
			"title": role["label_en"],
			"roles": [{"role": r} for r in frappe_roles_for_portal_key(role["key"])],
		}
		(page_dir / f"{folder}.json").write_text(json.dumps(page_json, indent="\t") + "\n")
		(page_dir / f"{folder}.js").write_text(_page_js(page_name, app, role["key"]))

		if not frappe.db.exists("Page", page_name):
			from frappe.modules.import_file import import_file_by_path

			import_file_by_path(str(page_dir / f"{folder}.json"), force=True, ignore_version=True)
		else:
			frappe.db.set_value("Page", page_name, "title", role["label_en"], update_modified=False)
			_sync_page_roles(page_name, frappe_roles_for_portal_key(role["key"]))

		out.append({"page": page_name, "app": app, "role": role["key"]})
	return out


def scaffold_all_journey_portals() -> dict:
	installed = set(frappe.get_installed_apps() or [])
	scaffolded = []
	for entry in VERTICAL_WORKCENTER_REGISTRY:
		if entry.get("reference") or entry.get("status") == "finance_group":
			continue
		if entry.get("tier", 99) > 2:
			continue
		app = entry["app"]
		if app not in installed:
			continue
		if entry["app"] in ("omnexa_education", "omnexa_healthcare", "omnexa_core"):
			continue
		try:
			scaffolded.extend(scaffold_journey_portals(app))
		except Exception as exc:
			scaffolded.append({"app": app, "error": str(exc)})
	frappe.db.commit()
	return {"scaffolded": scaffolded}
