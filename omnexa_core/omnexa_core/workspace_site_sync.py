# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Site-wide workspace audit + full desk sync (all Omnexa apps)."""

from __future__ import annotations

import json
from typing import Any

import frappe

from omnexa_core.omnexa_core.vertical_workspace_catalog import GLOBAL_MIN_LINKS, get_workspace_catalog_stats

from omnexa_core.omnexa_core.workspace_control_tower import (
	_APP_SPECS,
	_app_installed,
	_vertical_app_owns_workspace,
	get_desk_sections_for_workspace,
	sync_all_workspace_kpi_layout,
)
from omnexa_core.omnexa_core.workspace_desk_layouts import resolve_desk_sections_for_workspace_doc

_VERTICAL_WORKSPACE_MODULES: dict[str, str] = {
	"omnexa_construction": "omnexa_construction.workspace.construction_workspace",
	"omnexa_healthcare": "omnexa_healthcare.workspace.healthcare_workspace",
	"omnexa_education": "omnexa_education.workspace.education_workspace",
	"omnexa_car_rental": "omnexa_car_rental.workspace.car_rental_workspace",
	"omnexa_projects_pm": "omnexa_projects_pm.workspace.projects_workspace",
	"omnexa_trading": "omnexa_trading.workspace.trading_workspace",
	"omnexa_manufacturing": "omnexa_manufacturing.workspace.manufacturing_workspace",
	"omnexa_tourism": "omnexa_tourism.workspace.tour_workspace",
	"omnexa_engineering_consulting": "omnexa_engineering_consulting.workspace.eng_workspace",
	"omnexa_restaurant": "omnexa_restaurant.workspace.rest_workspace",
	"omnexa_services": "omnexa_services.workspace.svc_workspace",
	"omnexa_agriculture": "omnexa_agriculture.workspace.agri_workspace",
	"omnexa_hr": "omnexa_hr.workspace.hr_workspace",
	"omnexa_accounting": "omnexa_accounting.workspace.acct_workspace",
	"omnexa_nursery": "omnexa_nursery.workspace.nurs_workspace",
	"omnexa_fixed_assets": "omnexa_fixed_assets.workspace.fa_workspace",
	"omnexa_finance_engine": "omnexa_finance_engine.workspace.fe_workspace",
	"omnexa_credit_engine": "omnexa_credit_engine.workspace.ce_workspace",
	"omnexa_credit_risk": "omnexa_credit_risk.workspace.rk_workspace",
	"omnexa_alm": "omnexa_alm.workspace.al_workspace",
	"omnexa_consumer_finance": "omnexa_consumer_finance.workspace.cf_workspace",
	"omnexa_vehicle_finance": "omnexa_vehicle_finance.workspace.vf_workspace",
	"omnexa_mortgage_finance": "omnexa_mortgage_finance.workspace.mg_workspace",
	"omnexa_factoring": "omnexa_factoring.workspace.fc_workspace",
	"omnexa_sme_retail_finance": "omnexa_sme_retail_finance.workspace.sr_workspace",
	"omnexa_leasing_finance": "omnexa_leasing_finance.workspace.lf_workspace",
	"omnexa_statutory_audit": "omnexa_statutory_audit.workspace.sa_workspace",
	"erpgenex_property_mgmt": "erpgenex_property_mgmt.workspace.pm_workspace",
	"erpgenex_realestate_dev": "erpgenex_realestate_dev.workspace.rd_workspace",
	"erpgenex_realestate_sales": "erpgenex_realestate_sales.workspace.rs_workspace",
	"erpgenex_maintenance_core": "erpgenex_maintenance_core.workspace.mc_workspace",
	"omnexa_operational_risk": "omnexa_operational_risk.workspace.or_workspace",
	"omnexa_einvoice": "omnexa_einvoice.workspace.ei_workspace"
	}


def _sections_from_vertical_app(app: str) -> list | None:
	mod_path = _VERTICAL_WORKSPACE_MODULES.get(app)
	if not mod_path:
		return None
	try:
		mod = __import__(mod_path, fromlist=["WORKSPACE_SECTIONS"])
		return getattr(mod, "WORKSPACE_SECTIONS", None)
	except Exception:
		return None


def _links_from_sections(sections: list) -> list[tuple[str, str, str]]:
	out: list[tuple[str, str, str]] = []
	for _section, items in sections:
		for item in items:
			if not item or len(item) < 2:
				continue
			link_type, link_to = item[0], item[1]
			label = item[2] if len(item) > 2 else link_to
			if (link_type or "").strip() == "URL":
				continue
			out.append((link_type, link_to, label))
	return out


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	if link_type == "Workspace":
		return bool(frappe.db.exists("Workspace", link_to))
	return False


def _expected_links_for_workspace(ws_name: str) -> list[tuple[str, str, str]]:
	"""Return (link_type, link_to, label) tuples expected for a workspace."""
	owner = _vertical_app_owns_workspace(ws_name)
	if owner:
		sections = _sections_from_vertical_app(owner)
		if sections:
			return _links_from_sections(sections)

	if _app_installed("omnexa_construction") and ws_name == "Construction":
		from omnexa_construction.workspace.construction_workspace import WORKSPACE_SECTIONS

		out: list[tuple[str, str, str]] = []
		for _section, items in WORKSPACE_SECTIONS:
			for link_type, link_to, label, _icon, _is_report in items:
				out.append((link_type, link_to, label))
		# Standard commercial parties often preserved on desk
		out.append(("DocType", "Customer", "Customer (project owners)"))
		return out

	if frappe.db.exists("Workspace", ws_name):
		ws = frappe.get_doc("Workspace", ws_name)
		sections = resolve_desk_sections_for_workspace_doc(ws) or get_desk_sections_for_workspace(ws_name)
		if sections:
			out = []
			for _card, rows in sections:
				for label, link_type, link_to, _ref in rows:
					if (link_type or "").strip() == "URL":
						continue
					out.append((link_type, link_to, label))
			return out
	return []


def _actual_links(ws_name: str) -> set[tuple[str, str]]:
	if not frappe.db.exists("Workspace", ws_name):
		return set()
	rows = frappe.get_all(
		"Workspace Link",
		filters={"parent": ws_name, "type": "Link"
	},
		fields=["link_type", "link_to"],
	)
	return {(r.link_type, r.link_to) for r in rows if r.link_to and r.link_type}


_CARD_CONTENT_WORKSPACES = frozenset({"Construction"})


def _content_shortcut_labels(ws_name: str) -> set[str]:
	if not frappe.db.exists("Workspace", ws_name):
		return set()
	content = frappe.db.get_value("Workspace", ws_name, "content") or "[]"
	try:
		blocks = json.loads(content)
	except json.JSONDecodeError:
		return set()
	labels: set[str] = set()
	for block in blocks:
		if not isinstance(block, dict):
			continue
		if block.get("type") == "shortcut":
			label = (block.get("data") or {
	}).get("shortcut_name")
			if label:
				labels.add(label)
	return labels


def _content_card_labels(ws_name: str) -> set[str]:
	if not frappe.db.exists("Workspace", ws_name):
		return set()
	content = frappe.db.get_value("Workspace", ws_name, "content") or "[]"
	try:
		blocks = json.loads(content)
	except json.JSONDecodeError:
		return set()
	labels: set[str] = set()
	for block in blocks:
		if not isinstance(block, dict):
			continue
		if block.get("type") == "card":
			label = (block.get("data") or {
	}).get("card_name")
			if label:
				labels.add(label)
	return labels


def _shortcut_labels(ws_name: str) -> set[str]:
	if not frappe.db.exists("Workspace", ws_name):
		return set()
	return {
		row.label
		for row in frappe.get_all(
			"Workspace Shortcut",
			filters={"parent": ws_name
	},
			fields=["label"],
		)
		if row.label
	}


def audit_all_workspaces(*, verbose: bool = False) -> dict[str, Any]:
	"""Compare desk catalog vs live Workspace Link rows per registered app."""
	report: dict[str, Any] = {
		"workspaces": [],
		"summary": {
			"checked": 0,
			"ok": 0,
			"missing_links": 0,
			"not_in_db": 0,
			"below_min_links": 0,
			"content_gaps": 0,
			"min_links_target": GLOBAL_MIN_LINKS}
	}
	seen_ws: set[str] = set()

	for app_key, spec in _APP_SPECS.items():
		required = spec.get("_requires_app", app_key)
		if not _app_installed(required):
			continue
		ws_name = spec.get("workspace")
		if not ws_name or ws_name in seen_ws:
			continue
		seen_ws.add(ws_name)
		if not frappe.db.exists("Workspace", ws_name):
			report["workspaces"].append(
				{"workspace": ws_name, "app": app_key, "status": "missing_workspace", "missing": [], "extra": []
	}
			)
			report["summary"]["not_in_db"] += 1
			continue

		expected = _expected_links_for_workspace(ws_name)
		expected_keys = {(lt, lto) for lt, lto, _lbl in expected if _link_exists(lt, lto)}
		actual = _actual_links(ws_name)
		missing = sorted(expected_keys - actual)
		extra = sorted(actual - expected_keys) if verbose else []

		owner = _vertical_app_owns_workspace(ws_name)
		catalog_stats = None
		if owner:
			sections = _sections_from_vertical_app(owner) or []
			catalog_stats = get_workspace_catalog_stats(owner, sections)

		link_labels = [
			row.label
			for row in frappe.get_all(
				"Workspace Link",
				filters={"parent": ws_name, "type": "Link"
	},
				fields=["label"],
			)
			if row.label
		]
		section_labels = [
			row.label
			for row in frappe.get_all(
				"Workspace Link",
				filters={"parent": ws_name, "type": "Card Break"
	},
				fields=["label"],
			)
			if row.label
		]
		content_labels = _content_shortcut_labels(ws_name)
		content_cards = _content_card_labels(ws_name)
		shortcut_labels = _shortcut_labels(ws_name)
		is_vertical_owned = bool(_vertical_app_owns_workspace(ws_name))
		if ws_name in _CARD_CONTENT_WORKSPACES:
			missing_content = sorted(set(section_labels) - content_cards)
		elif is_vertical_owned:
			missing_content = sorted(set(link_labels) - content_labels)
		else:
			# Control-tower desks (Sell, Theme Manager, Asset Insurance, …) use card blocks + partial shortcuts.
			missing_content = []
		missing_shortcuts = sorted(set(link_labels) - shortcut_labels) if is_vertical_owned else []
		below_min = bool(catalog_stats and not catalog_stats.get("meets_global_min") and len(actual) < GLOBAL_MIN_LINKS)

		entry = {
			"workspace": ws_name,
			"app": app_key,
			"expected": len(expected_keys),
			"actual": len(actual),
			"missing": [{"link_type": a, "link_to": b
	} for a, b in missing],
			"extra_count": len(extra),
			"catalog_links": (catalog_stats or {
	}).get("links_catalogued"),
			"meets_min_links": not below_min,
			"missing_content_labels": len(missing_content),
			"missing_shortcut_labels": len(missing_shortcuts),
			"status": "ok"
	}
		if missing or below_min or missing_content or missing_shortcuts:
			entry["status"] = "gaps"
		if verbose:
			entry["missing_content"] = missing_content[:20]
			entry["missing_shortcuts"] = missing_shortcuts[:20]
		report["workspaces"].append(entry)
		report["summary"]["checked"] += 1
		if missing:
			report["summary"]["missing_links"] += len(missing)
		if below_min:
			report["summary"]["below_min_links"] += 1
		if missing_content or missing_shortcuts:
			report["summary"]["content_gaps"] += 1
		if entry["status"] == "ok":
			report["summary"]["ok"] += 1

	frappe.logger("omnexa_core").info("Workspace audit: %s", report["summary"])
	return report


def _repair_empty_registered_workspaces() -> list[str]:
	"""Re-sync app desks that ended with zero sidebar links (failed save / hook race)."""
	from omnexa_core.omnexa_core.workspace_control_tower import sync_workspace_for_app

	repaired: list[str] = []
	for app_key, spec in _APP_SPECS.items():
		required = spec.get("_requires_app", app_key)
		if not _app_installed(required):
			continue
		if app_key in _VERTICAL_WORKSPACE_MODULES:
			continue
		ws_name = spec.get("workspace")
		if not ws_name or not frappe.db.exists("Workspace", ws_name):
			continue
		if frappe.db.count("Workspace Link", {"parent": ws_name, "type": "Link"
	}):
			continue
		try:
			sync_workspace_for_app(app_key)
			frappe.db.commit()
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Omnexa: repair empty workspace `{ws_name}`")
			continue
		if frappe.db.count("Workspace Link", {"parent": ws_name, "type": "Link"
	}):
			repaired.append(ws_name)
	return repaired


def run_full_workspace_sync() -> dict[str, Any]:
	"""Sync all control-tower desks, then app-owned vertical workspace menus."""
	from omnexa_core.install import run_workspace_desk_sync, sync_vertical_app_workspace_menus
	from omnexa_core.omnexa_core.sector_sidebar_sync import sync_sector_sidebar

	run_workspace_desk_sync()
	vertical_stats = sync_vertical_app_workspace_menus()
	sector_stats = sync_sector_sidebar(save=True)

	repaired = _repair_empty_registered_workspaces()
	from omnexa_core.omnexa_core.workspace_icon_enricher import enrich_all_workspace_visual_icons

	icon_stats = enrich_all_workspace_visual_icons(save=True)
	frappe.clear_cache(doctype="Workspace")
	audit = audit_all_workspaces()
	return {
		"vertical_workspaces": vertical_stats,
		"repaired_empty": repaired,
		"sector_sidebar": sector_stats,
		"icon_enrichment": icon_stats,
		"audit": audit["summary"],
		"gaps": [w for w in audit["workspaces"] if w.get("status") != "ok"]
	}
