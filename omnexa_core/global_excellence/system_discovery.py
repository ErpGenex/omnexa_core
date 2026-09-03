# Copyright (c) 2026, ErpGenEx
"""Phase 1 — System Discovery (read-only). Builds MASTER_APPLICATION_INVENTORY."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import frappe
from frappe.utils import get_bench_path

from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY, get_registry_entry


def _installed_apps() -> list[str]:
	return list(frappe.get_installed_apps() or [])


def _app_path(app: str) -> str | None:
	try:
		return frappe.get_app_path(app)
	except Exception:
		return None


def _count_for_app(table: str, app: str, *, extra_filters: str = "") -> int:
	filters = f"WHERE app = {frappe.db.escape(app)}"
	if extra_filters:
		filters += f" AND {extra_filters}"
	try:
		return frappe.db.sql(f"SELECT COUNT(*) FROM `{table}` {filters}")[0][0]
	except Exception:
		return 0


def _doctypes_by_module() -> dict[str, int]:
	rows = frappe.db.sql(
		"""
		SELECT module, COUNT(*) AS c
		FROM `tabDocType`
		WHERE custom = 0 AND istable = 0
		GROUP BY module
		""",
		as_dict=True,
	)
	return {r.module: r.c for r in rows}


def _reports_by_module() -> dict[str, int]:
	rows = frappe.db.sql(
		"""
		SELECT module, COUNT(*) AS c
		FROM `tabReport`
		GROUP BY module
		""",
		as_dict=True,
	)
	return {r.module: r.c for r in rows}


def _workflows_summary() -> list[dict]:
	return frappe.get_all(
		"Workflow",
		fields=["name", "document_type", "workflow_state_field", "is_active"],
		order_by="name",
	)


def _global_counts() -> dict:
	def _count(sql: str) -> int:
		try:
			return frappe.db.sql(sql)[0][0]
		except Exception:
			return 0

	return {
		"doctypes_standard": _count("SELECT COUNT(*) FROM `tabDocType` WHERE custom=0 AND istable=0"),
		"child_tables": _count("SELECT COUNT(*) FROM `tabDocType` WHERE istable=1"),
		"doctypes_custom": _count("SELECT COUNT(*) FROM `tabDocType` WHERE custom=1 AND istable=0"),
		"reports": _count("SELECT COUNT(*) FROM `tabReport`"),
		"pages": _count("SELECT COUNT(*) FROM `tabPage`"),
		"workspaces": _count("SELECT COUNT(*) FROM `tabWorkspace`"),
		"workflows": _count("SELECT COUNT(*) FROM `tabWorkflow`"),
		"roles": _count("SELECT COUNT(*) FROM `tabRole`"),
		"custom_fields": _count("SELECT COUNT(*) FROM `tabCustom Field`"),
		"property_setters": _count("SELECT COUNT(*) FROM `tabProperty Setter`"),
		"client_scripts": _count("SELECT COUNT(*) FROM `tabClient Script`"),
		"server_scripts": _count("SELECT COUNT(*) FROM `tabServer Script`"),
		"translations": _count("SELECT COUNT(*) FROM `tabTranslation`"),
		"print_formats": _count("SELECT COUNT(*) FROM `tabPrint Format`"),
		"web_forms": _count("SELECT COUNT(*) FROM `tabWeb Form`"),
		"notifications": _count("SELECT COUNT(*) FROM `tabNotification`"),
		"email_templates": _count("SELECT COUNT(*) FROM `tabEmail Template`"),
	}


def _modules_for_app(app: str) -> list[str]:
	try:
		return list(frappe.get_module_list(app) or [])
	except Exception:
		return []


def _app_inventory_row(app: str, dt_by_mod: dict[str, int], rpt_by_mod: dict[str, int]) -> dict:
	modules = _modules_for_app(app)
	dt_count = sum(dt_by_mod.get(m, 0) for m in modules)
	rpt_count = sum(rpt_by_mod.get(m, 0) for m in modules)
	reg = get_registry_entry(app) or {}
	return {
		"app": app,
		"path_exists": bool(_app_path(app)),
		"modules": modules,
		"module_count": len(modules),
		"doctype_count": dt_count,
		"report_count": rpt_count,
		"page_count": _count_for_app("tabPage", app),
		"workspace_count": _count_for_app("tabWorkspace", app),
		"registry": {
			"slug": reg.get("slug"),
			"title_en": reg.get("title_en"),
			"title_ar": reg.get("title_ar"),
			"workcenter": reg.get("workcenter"),
			"status": reg.get("status"),
			"tier": reg.get("tier"),
			"reference": bool(reg.get("reference")),
		}
		if reg
		else None,
		"audit_status": "pending",
		"priority_hint": _priority_hint(app, reg),
	}


def _priority_hint(app: str, reg: dict | None) -> str:
	if app in ("frappe", "omnexa_core"):
		return "P0-platform"
	if reg and reg.get("reference"):
		return "P0-reference"
	if reg and reg.get("status") == "complete":
		return "P1-complete-vertical"
	if reg and reg.get("status") == "partial":
		return "P2-partial-vertical"
	if reg and reg.get("status") == "finance_group":
		return "P1-finance-group"
	return "P3-supporting"


def _suggested_audit_order(apps: list[dict]) -> list[str]:
	order = {"P0-platform": 0, "P0-reference": 1, "P1-complete-vertical": 2, "P1-finance-group": 3, "P2-partial-vertical": 4, "P3-supporting": 5}
	return [
		a["app"]
		for a in sorted(apps, key=lambda x: (order.get(x.get("priority_hint") or "P3-supporting", 9), x.get("app") or ""))
	]


def build_master_application_inventory(*, site: str | None = None) -> dict:
	"""Read-only discovery — no DB writes."""
	site = site or frappe.local.site
	installed = _installed_apps()
	dt_by_mod = _doctypes_by_module()
	rpt_by_mod = _reports_by_module()
	app_rows = [_app_inventory_row(app, dt_by_mod, rpt_by_mod) for app in installed]

	registry_apps = {r["app"] for r in VERTICAL_WORKCENTER_REGISTRY}
	unregistered_verticals = [a for a in installed if a.startswith(("omnexa_", "erpgenex_")) and a not in registry_apps]

	return {
		"meta": {
			"phase": "PHASE_1_SYSTEM_DISCOVERY",
			"site": site,
			"generated_at": datetime.now().isoformat(timespec="seconds"),
			"read_only": True,
			"framework": "ERPGENEX_GLOBAL_EXCELLENCE_LOOP",
			"localization_extension": True,
			"target_level": "World-Class / Global Excellence #1 Benchmark",
		},
		"global_counts": _global_counts(),
		"installed_apps_count": len(installed),
		"applications": app_rows,
		"vertical_registry_entries": len(VERTICAL_WORKCENTER_REGISTRY),
		"unregistered_custom_apps": unregistered_verticals,
		"suggested_audit_order": _suggested_audit_order(app_rows),
		"workflows_sample": _workflows_summary()[:50],
		"workflows_total": len(_workflows_summary()),
		"next_phase": {
			"action": "SELECT_APPLICATION_01",
			"recommended_app": (_suggested_audit_order(app_rows)[1] if len(_suggested_audit_order(app_rows)) > 1 else None),
			"note": "Do not modify system until application audit begins with safe-fix classification.",
		},
	}


def _default_export_dir() -> Path:
	bench = Path(get_bench_path())
	return bench / "Docs" / datetime.now().strftime("%Y-%m-%d")


@frappe.whitelist()
def export_master_application_inventory(export_dir: str | None = None) -> dict:
	"""Export MASTER_APPLICATION_INVENTORY.json (System Manager)."""
	frappe.only_for("System Manager")
	payload = build_master_application_inventory()
	out_dir = Path(export_dir) if export_dir else _default_export_dir()
	out_dir.mkdir(parents=True, exist_ok=True)
	json_path = out_dir / "01_MASTER_APPLICATION_INVENTORY.json"
	json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
	return {"path": str(json_path), "summary": payload["meta"], "apps": payload["installed_apps_count"]}


def run_phase1_discovery(export_dir: str | None = None) -> dict:
	return export_master_application_inventory(export_dir=export_dir)
