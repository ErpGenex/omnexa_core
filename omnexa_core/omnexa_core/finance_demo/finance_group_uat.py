# Copyright (c) 2026, ErpGenEx
"""Automated UAT for Finance Group — replaces manual pilot checklist on demo site."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.finance_demo.finance_group_smoke import (
	FINANCE_PAGES,
	run_finance_group_smoke_audit,
	run_finance_portal_access_audit,
)
from omnexa_core.omnexa_core.finance_demo.finance_role_demo import DEMO_PASSWORD, ROLE_SPECS
from omnexa_core.omnexa_core.finance_demo.finance_vertical_specs import VERTICAL_BPE_SPECS


def _check_page(page: str) -> bool:
	return bool(page and frappe.db.exists("Page", page))


def _check_user(email: str) -> bool:
	return bool(frappe.db.exists("User", email))


def _check_workflow(doctype: str) -> bool:
	return bool(frappe.db.get_value("Workflow", {"document_type": doctype, "is_active": 1
	}, "name"))


def _check_demo_cases(doctype: str, min_count: int = 1) -> bool:
	if not frappe.db.exists("DocType", doctype):
		return False
	return frappe.db.count(doctype) >= min_count


def run_automated_uat() -> dict:
	"""Execute all UAT scenarios programmatically."""
	scenarios: list[dict] = []

	scenarios.append(
		{
			"id": "UAT-01",
			"name": "Finance Group home",
			"passed": bool(_check_page("finance-group") or frappe.db.exists("Workspace", "Finance Group"))}
	)
	scenarios.append({"id": "UAT-02", "name": "Finance Workcenter", "passed": _check_page("finance-workcenter")
	})

	for spec in ROLE_SPECS:
		scenarios.append(
			{
				"id": f"UAT-USER-{spec['email']
	}",
				"name": f"Demo user {spec['email']
	}",
				"passed": _check_user(spec["email"])
	}
		)

	for app, pages in FINANCE_PAGES.items():
		scenarios.append(
			{
				"id": f"UAT-PORTAL-{app
	}",
				"name": f"Portals {app
	}",
				"passed": _check_page(pages[0]) and _check_page(pages[1])
	}
		)

	for app, spec in VERTICAL_BPE_SPECS.items():
		if app not in (frappe.get_installed_apps() or []):
			continue
		dt = spec["case_doctype"]
		if spec.get("skip_seed"):
			scenarios.append(
				{
					"id": f"UAT-WF-{app
	}",
					"name": f"Workflow {spec['workflow_name']
	}",
					"passed": _check_workflow(dt)
	}
			)
			continue
		scenarios.append(
			{
				"id": f"UAT-WF-{app
	}",
				"name": f"Workflow {spec['workflow_name']
	}",
				"passed": _check_workflow(dt) and _check_demo_cases(dt, 1)}
		)

	try:
		from omnexa_core.omnexa_core.finance_demo.finance_stage_gate import get_progress_tracker

		sample_dt = "Consumer Finance Case"
		sample_name = frappe.db.get_value(sample_dt, {}, "name")
		if sample_name:
			tracker = get_progress_tracker(sample_dt, sample_name)
			scenarios.append(
				{
					"id": "UAT-PROGRESS",
					"name": "Progress tracker API",
					"passed": bool(tracker.get("progress"))
	}
			)
		else:
			scenarios.append({"id": "UAT-PROGRESS", "name": "Progress tracker API", "passed": True, "skipped": True
	})
	except Exception as exc:
		scenarios.append({"id": "UAT-PROGRESS", "name": "Progress tracker API", "passed": False, "error": str(exc)
	})

	smoke = run_finance_group_smoke_audit()
	scenarios.append(
		{
			"id": "UAT-SMOKE",
			"name": "Smoke audit 13/13",
			"passed": bool(smoke.get("ok"))
	}
	)

	portals = run_finance_portal_access_audit()
	scenarios.append(
		{
			"id": "UAT-PORTAL-ACCESS",
			"name": "Portal access 26/26",
			"passed": bool(portals.get("ok"))
	}
	)

	passed = sum(1 for s in scenarios if s.get("passed"))
	total = len(scenarios)
	return {
		"ok": passed == total,
		"scenarios_passed": passed,
		"scenarios_total": total,
		"demo_password": DEMO_PASSWORD,
		"scenarios": scenarios
	}


@frappe.whitelist()
def run_finance_group_uat() -> dict:
	frappe.only_for("System Manager")
	return run_automated_uat()
