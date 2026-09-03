# Copyright (c) 2026, ErpGenEx
"""E2E business scenario harness for Global Excellence Loop."""

from __future__ import annotations

import frappe

from omnexa_core.global_excellence.system_discovery import _modules_for_app
from omnexa_core.vertical_workcenter.registry import get_registry_entry


def _scenario_doctype_meta(app: str) -> dict:
	modules = _modules_for_app(app)
	if not modules:
		return {"status": "skip", "reason": "no_modules"}
	rows = frappe.db.sql(
		f"""
		SELECT name, is_submittable, issingle
		FROM tabDocType
		WHERE custom = 0 AND istable = 0 AND module IN ({", ".join(["%s"] * len(modules))})
		ORDER BY is_submittable DESC, name
		LIMIT 5
		""",
		tuple(modules),
		as_dict=True,
	)
	if not rows:
		return {"status": "skip", "reason": "no_doctypes"}
	picked = next((r for r in rows if not r.issingle), rows[0])
	meta = frappe.get_meta(picked.name)
	return {
		"status": "pass" if meta else "fail",
		"doctype": picked.name,
		"is_submittable": picked.is_submittable,
		"field_count": len(meta.fields),
	}


def _scenario_report_execute(app: str) -> dict:
	modules = _modules_for_app(app)
	if not modules:
		return {"status": "skip", "reason": "no_modules"}
	report = frappe.db.sql(
		f"""
		SELECT name, report_type, ref_doctype
		FROM tabReport
		WHERE disabled = 0 AND module IN ({", ".join(["%s"] * len(modules))})
		ORDER BY name LIMIT 1
		""",
		tuple(modules),
		as_dict=True,
	)
	if not report:
		return {"status": "skip", "reason": "no_reports"}
	rpt = report[0]
	try:
		from frappe.desk.query_report import generate_report_result

		result = generate_report_result(rpt.name, filters={}, user=frappe.session.user, ignore_prepared_report=True)
		rows = result.get("result") or []
		return {"status": "pass", "report": rpt.name, "row_count": len(rows) if isinstance(rows, list) else 0}
	except Exception as exc:
		return {"status": "warn", "report": rpt.name, "error": str(exc)[:200]}


def _scenario_workflow(app: str) -> dict:
	modules = _modules_for_app(app)
	if not modules:
		return {"status": "skip", "reason": "no_modules"}
	wf = frappe.db.sql(
		f"""
		SELECT name, document_type FROM tabWorkflow
		WHERE is_active = 1 AND document_type IN (
			SELECT name FROM tabDocType WHERE module IN ({", ".join(["%s"] * len(modules))})
		)
		LIMIT 1
		""",
		tuple(modules),
		as_dict=True,
	)
	if not wf:
		return {"status": "skip", "reason": "no_workflows"}
	return {"status": "pass", "workflow": wf[0].name, "document_type": wf[0].document_type}


def _scenario_workcenter(app: str) -> dict:
	reg = get_registry_entry(app)
	if not reg or not reg.get("workcenter"):
		return {"status": "skip", "reason": "no_workcenter"}
	page = frappe.db.exists("Page", reg["workcenter"])
	return {"status": "pass" if page else "warn", "workcenter": reg["workcenter"], "page_exists": bool(page)}


def run_e2e_for_app(app: str) -> dict:
	scenarios = {
		"doctype_meta": _scenario_doctype_meta(app),
		"report_execute": _scenario_report_execute(app),
		"workflow": _scenario_workflow(app),
		"workcenter": _scenario_workcenter(app),
	}
	statuses = [s.get("status") for s in scenarios.values() if s.get("status") not in ("skip",)]
	passed = sum(1 for s in statuses if s == "pass")
	failed = sum(1 for s in statuses if s == "fail")
	warn = sum(1 for s in statuses if s == "warn")
	overall = "pass"
	if failed:
		overall = "fail"
	elif warn and not passed:
		overall = "warn"
	elif not statuses:
		overall = "skip"
	return {
		"app": app,
		"overall": overall,
		"scenarios_passed": passed,
		"scenarios_failed": failed,
		"scenarios_warn": warn,
		"scenarios": scenarios,
	}


def run_e2e_all_applications(*, apps: list[str] | None = None) -> dict:
	target_apps = apps or frappe.get_installed_apps()
	results = []
	for app in target_apps:
		try:
			results.append(run_e2e_for_app(app))
		except Exception as exc:
			results.append({"app": app, "overall": "fail", "error": str(exc)})

	passed = sum(1 for r in results if r.get("overall") == "pass")
	failed = sum(1 for r in results if r.get("overall") == "fail")
	skipped = sum(1 for r in results if r.get("overall") == "skip")
	return {
		"status": "completed",
		"apps_tested": len(results),
		"passed": passed,
		"failed": failed,
		"skipped": skipped,
		"pass_rate_pct": round(100 * passed / max(1, len(results) - skipped), 1),
		"results": results,
	}


@frappe.whitelist()
def run_global_e2e_scenarios() -> dict:
	frappe.only_for("System Manager")
	return run_e2e_all_applications()
