# Copyright (c) 2026, ErpGenEx
"""Scaffold {slug}-workcenter page in a vertical app."""

from __future__ import annotations

import json
from pathlib import Path

import frappe

from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY, get_registry_entry

ROLES = [{"role": "System Manager"}, {"role": "Company Admin"}]


def _app_module(app: str) -> str:
	mod_file = Path(frappe.get_app_path(app)) / app / "modules.txt"
	if not mod_file.exists():
		mod_file = Path(frappe.get_app_path(app)) / "modules.txt"
	if mod_file.exists():
		for line in mod_file.read_text().splitlines():
			line = line.strip()
			if line:
				return line
	existing = frappe.get_all("Page", filters={"name": ["like", "%"]}, fields=["module"], limit=1)
	# fallback: scan filesystem json
	base = _module_folder(app)
	for p in (base / "page").glob("*/*.json"):
		try:
			data = json.loads(p.read_text())
			if data.get("module"):
				return data["module"]
		except Exception:
			pass
	return app.replace("_", " ").title()


def _module_folder(app: str) -> Path:
	base = Path(frappe.get_app_path(app))
	for p in sorted(base.iterdir()):
		if p.is_dir() and (p / "page").is_dir():
			return p
	inner = app.rsplit("_", 1)[-1] if app.startswith("erpgenex_") or app.startswith("omnexa_") else app
	return base / inner


def scaffold_workcenter(app: str, *, sync_hooks: bool = True) -> dict:
	entry = get_registry_entry(app)
	if not entry:
		frappe.throw(f"App not in registry: {app}")
	slug = entry["slug"]
	page_name = entry["workcenter"]
	folder = slug.replace("-", "_") + "_workcenter"
	module_root = _module_folder(app)
	page_dir = module_root / "page" / folder
	page_dir.mkdir(parents=True, exist_ok=True)

	(page_dir / "__init__.py").write_text("")
	(page_dir / f"{folder}.py").write_text("")

	(page_dir / f"{folder}.json").write_text(
		json.dumps(
			{
				"doctype": "Page",
				"module": _app_module(app),
				"name": page_name,
				"page_name": page_name,
				"standard": "Yes",
				"title": f"{entry['title_en']} Workcenter",
				"roles": ROLES,
			},
			indent="\t",
		)
		+ "\n"
	)

	page_doc = {
		"doctype": "Page",
		"module": _app_module(app),
		"name": page_name,
		"page_name": page_name,
		"standard": "Yes",
		"title": f"{entry['title_en']} Workcenter",
		"roles": ROLES,
	}
	if not frappe.db.exists("Page", page_name):
		from frappe.modules.import_file import import_file_by_path

		import_file_by_path(str(page_dir / f"{folder}.json"), force=True, ignore_version=True)
	else:
		frappe.db.set_value("Page", page_name, "title", page_doc["title"], update_modified=False)

	js = f'''frappe.pages["{page_name}"].on_page_load = function (wrapper) {{
	if (window.omnexa_core && omnexa_core.vertical_workcenter && omnexa_core.vertical_workcenter.mount) {{
		omnexa_core.vertical_workcenter.mount(wrapper, "{app}");
		return;
	}}
	const page = frappe.ui.make_app_page({{
		parent: wrapper,
		title: __("{entry["title_en"]} Workcenter"),
		single_column: true,
	}});
	$(page.body).html('<p class="text-muted">' + __("Load omnexa_core vertical workcenter kit") + "</p>");
}};
'''
	(page_dir / f"{folder}.js").write_text(js)

	if sync_hooks:
		_update_hooks_route(app, page_name, entry["title_en"])

	return {"app": app, "page": page_name, "path": str(page_dir), "route": f"/app/{page_name}"}


def _update_hooks_route(app: str, page_name: str, title: str) -> None:
	hooks_path = Path(frappe.get_app_path(app)) / app / "hooks.py"
	if not hooks_path.exists():
		hooks_path = Path(frappe.get_app_path(app)) / "hooks.py"
	if not hooks_path.exists():
		return
	text = hooks_path.read_text()
	route_line = f'\t\t"route": "/app/{page_name}",'
	if f'"/app/{page_name}"' in text:
		return
	if "add_to_apps_screen" in text and "route" in text:
		import re

		text = re.sub(
			r'("route":\s*")[^"]+(")',
			lambda m: f'{m.group(1)}/app/{page_name}{m.group(2)}',
			text,
			count=1,
		)
		hooks_path.write_text(text)


@frappe.whitelist()
def scaffold_app_workcenter(app: str) -> dict:
	frappe.only_for("System Manager")
	return scaffold_workcenter(app)


@frappe.whitelist()
def scaffold_tier1_workcenters() -> dict:
	frappe.only_for("System Manager")
	out = []
	for entry in VERTICAL_WORKCENTER_REGISTRY:
		if entry.get("tier") != 1 or entry.get("reference") or entry.get("status") == "finance_group":
			continue
		if entry["app"] not in (frappe.get_installed_apps() or []):
			out.append({"app": entry["app"], "skipped": "not_installed"})
			continue
		try:
			out.append(scaffold_workcenter(entry["app"]))
		except Exception as exc:
			out.append({"app": entry["app"], "error": str(exc)})
	frappe.db.commit()
	return {"scaffolded": out}


@frappe.whitelist()
def scaffold_all_workcenters() -> dict:
	frappe.only_for("System Manager")
	out = []
	for entry in VERTICAL_WORKCENTER_REGISTRY:
		if entry.get("reference") or entry.get("status") == "finance_group":
			continue
		if entry["app"] not in (frappe.get_installed_apps() or []):
			continue
		try:
			out.append(scaffold_workcenter(entry["app"], sync_hooks=entry.get("tier") == 1))
		except Exception as exc:
			out.append({"app": entry["app"], "error": str(exc)})
	frappe.db.commit()
	return {"scaffolded": out}
