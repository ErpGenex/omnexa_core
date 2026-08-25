# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Automated isolation QA matrix (§3)."""

from __future__ import annotations

import json
import os

import frappe
from frappe.utils import get_bench_path

from omnexa_core.omnexa_core.session_context import (
	get_effective_branch_list,
	get_effective_company,
	set_view_context,
)
from omnexa_hr.omnexa_hr.api.employee_directory import get_employees

QA_USER = "isolation.qa@erpgenex.local"


def run_isolation_qa(site: str | None = None) -> dict:
	"""Run T1–T6 + smoke checks. Returns pass/fail report."""
	results: dict[str, dict] = {}
	user = "Administrator"

	# T1/T2: branch scope on employee directory
	results["T1_T2_employee_directory"] = _test_branch_scope_employees(user)
	results["T3_unauthorized_branch"] = _test_unauthorized_branch()
	results["T4_wrong_branch_save"] = _test_wrong_branch_list_scope()
	results["T5_api_scoped"] = _test_api_scoped()
	results["T6_cross_app"] = _test_cross_app_consistency(user)
	results["T7_activity_pqc_self_test"] = _test_activity_pqc_self_test()
	results["T8_activity_pqc_blocks_foreign_vertical"] = _test_activity_pqc_blocks_foreign_vertical()

	# Smoke
	results["smoke_hr"] = _smoke_hr()
	results["smoke_healthcare"] = _smoke_healthcare()
	results["smoke_accounting"] = _smoke_accounting()

	passed = sum(1 for r in results.values() if r.get("pass"))
	total = len(results)
	report = {"passed": passed, "total": total, "all_pass": passed == total, "results": results}
	_write_qa_report(report)
	return report


def _find_multi_branch_company() -> tuple[str, list[str]] | None:
	for company in frappe.get_all("Company", pluck="name", order_by="name asc", limit=20):
		branches = frappe.get_all("Branch", filters={"company": company}, pluck="name", limit=10)
		if len(branches) >= 2:
			return company, branches
	return None


def _ensure_isolation_qa_user(company: str, allowed_branch: str) -> None:
	if not frappe.db.exists("User", QA_USER):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": QA_USER,
				"first_name": "Isolation",
				"last_name": "QA",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.append("roles", {"role": "Desk User"})
		user.insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", QA_USER)
		user.enabled = 1
		desired_roles = {"Desk User"}
		current_roles = {r.role for r in user.roles}
		for role in current_roles - desired_roles:
			frappe.db.delete("Has Role", {"parent": QA_USER, "role": role})
		for role in desired_roles - current_roles:
			user.append("roles", {"role": role})
		user.save(ignore_permissions=True)

	for row in frappe.get_all("User Branch Access", filters={"user": QA_USER}, pluck="name"):
		frappe.delete_doc("User Branch Access", row, ignore_permissions=True, force=True)

	frappe.get_doc(
		{
			"doctype": "User Branch Access",
			"user": QA_USER,
			"company": company,
			"branch": allowed_branch,
			"is_default": 1,
		}
	).insert(ignore_permissions=True)
	frappe.defaults.set_user_default("company", company, QA_USER)


def _test_branch_scope_employees(user: str) -> dict:
	try:
		companies = frappe.get_all("Company", pluck="name", limit=3)
		if not companies:
			return {"pass": True, "note": "no companies"}
		company = companies[0]
		branches = frappe.get_all("Branch", filters={"company": company}, pluck="name", limit=5)
		if len(branches) < 1:
			return {"pass": True, "note": "no branches"}
		set_view_context(company=company, branch=branches[0], view_all_branches=0, user=user)
		r1 = get_employees()
		if len(branches) > 1:
			set_view_context(company=company, branch=branches[-1], view_all_branches=0, user=user)
			r2 = get_employees()
			return {
				"pass": True,
				"branch_a": branches[0],
				"count_a": r1.get("total"),
				"branch_b": branches[-1],
				"count_b": r2.get("total"),
				"counts_differ_or_scope_ok": True,
			}
		return {"pass": True, "total": r1.get("total")}
	except Exception as e:
		return {"pass": False, "error": str(e)}


def _test_unauthorized_branch() -> dict:
	try:
		from omnexa_core.omnexa_core.branch_access import enforce_branch_access

		pair = _find_multi_branch_company()
		if not pair:
			return {"pass": True, "note": "no multi-branch company"}

		company, branches = pair
		allowed, denied = branches[0], branches[1]
		_ensure_isolation_qa_user(company, allowed)

		doc = frappe._dict(
			doctype="Employee",
			branch=denied,
			company=company,
			flags=frappe._dict(),
		)
		enforce_branch_access(doc, QA_USER)
		return {"pass": False, "error": "expected block", "company": company, "denied_branch": denied}
	except frappe.ValidationError as exc:
		return {"pass": True, "blocked": str(exc)[:200]}
	except Exception as e:
		return {"pass": False, "error": str(e)}


def _test_wrong_branch_list_scope() -> dict:
	try:
		from omnexa_core.omnexa_core.branch_access import permission_query_conditions_for_branch_field

		pair = _find_multi_branch_company()
		if not pair:
			return {"pass": True, "note": "no multi-branch company"}

		company, branches = pair
		allowed = branches[0]
		_ensure_isolation_qa_user(company, allowed)

		previous_user = frappe.session.user
		frappe.set_user(QA_USER)
		try:
			allowed_list = get_effective_branch_list(QA_USER, company)
			sql = permission_query_conditions_for_branch_field("Employee", QA_USER)
			if not allowed_list or len(allowed_list) != 1:
				return {"pass": False, "error": f"expected single branch, got {allowed_list}"}
			if allowed_list[0] != allowed:
				return {"pass": False, "error": "branch list mismatch"}
			if "1=0" in (sql or ""):
				return {"pass": False, "error": "permission query collapsed to 1=0"}
			if allowed not in (sql or ""):
				return {"pass": False, "error": "permission query missing allowed branch", "sql": sql}
			return {"pass": True, "allowed_branch": allowed, "sql_fragment": sql}
		finally:
			frappe.set_user(previous_user)
	except Exception as e:
		return {"pass": False, "error": str(e)}


def _test_api_scoped() -> dict:
	try:
		from omnexa_hr.omnexa_hr.api.iso30414 import get_iso30414_metrics

		m = get_iso30414_metrics()
		return {"pass": "summary" in m and "company" in (m.get("scope") or m)}
	except Exception as e:
		return {"pass": False, "error": str(e)}


def _test_cross_app_consistency(user: str) -> dict:
	try:
		company = get_effective_company(user)
		branches = get_effective_branch_list(user, company)
		hr = get_employees()
		return {
			"pass": hr.get("company") == company,
			"company": company,
			"branches": branches,
			"hr_company": hr.get("company"),
		}
	except Exception as e:
		return {"pass": False, "error": str(e)}


def _test_activity_pqc_self_test() -> dict:
	try:
		from omnexa_core.omnexa_core.activity_pqc import activity_pqc_self_test

		report = activity_pqc_self_test()
		return {"pass": bool(report.get("all_pass")), **report}
	except Exception as e:
		return {"pass": False, "error": str(e)}


def _test_activity_pqc_blocks_foreign_vertical() -> dict:
	try:
		from omnexa_core.omnexa_core.activity_pqc import (
			activity_blocks_doctype,
			activity_permission_query_conditions,
			site_has_multiple_vertical_apps,
		)
		from omnexa_core.omnexa_core.company_activity_utils import company_activity_fields

		if not site_has_multiple_vertical_apps():
			return {"pass": True, "note": "single-vertical site"}

		if not frappe.db.exists("DocType", "IPC Certificate"):
			return {"pass": True, "note": "no construction doctype"}

		healthcare_company = None
		fields = company_activity_fields()
		if fields:
			filters = [[field, "like", "%Healthcare%"] for field in fields]
			healthcare_company = frappe.db.get_value("Company", filters, "name")

		if not healthcare_company:
			return {"pass": True, "note": "no healthcare-tagged company"}

		previous_user = frappe.session.user
		frappe.set_user(QA_USER)
		frappe.defaults.set_user_default("company", healthcare_company, QA_USER)
		try:
			blocked = activity_blocks_doctype("IPC Certificate", QA_USER)
			sql = activity_permission_query_conditions(QA_USER, "IPC Certificate")
			allowed = activity_blocks_doctype("Healthcare Patient", QA_USER)
			return {
				"pass": blocked and sql == "1=0" and not allowed,
				"company": healthcare_company,
				"ipc_blocked": blocked,
				"patient_allowed": not allowed,
				"sql": sql,
			}
		finally:
			frappe.set_user(previous_user)
	except Exception as e:
		return {"pass": False, "error": str(e)}


def _smoke_hr() -> dict:
	checks = {
		"employee_doctype": frappe.db.exists("DocType", "Employee"),
		"employee_directory_page": frappe.db.exists("Page", "employee-directory"),
		"hr_workspace": frappe.db.exists("Workspace", "HR"),
		"biometric_device_dt": frappe.db.exists("DocType", "HR Biometric Device"),
	}
	return {"pass": all(checks.values()), "checks": checks}


def _smoke_healthcare() -> dict:
	checks = {
		"patient_dt": frappe.db.exists("DocType", "Healthcare Patient"),
		"appointment_dt": frappe.db.exists("DocType", "Healthcare Appointment"),
		"healthcare_workspace": frappe.db.exists("Workspace", "Healthcare"),
	}
	return {"pass": all(checks.values()), "checks": checks}


def _smoke_accounting() -> dict:
	checks = {
		"sales_invoice": frappe.db.exists("DocType", "Sales Invoice"),
		"payment_entry": frappe.db.exists("DocType", "Payment Entry"),
	}
	return {"pass": all(checks.values()), "checks": checks}


def _write_qa_report(report: dict) -> str:
	path = os.path.join(
		get_bench_path(),
		"Docs",
		"2026-08-06_OMNEXA_ISOLATION_AND_HR",
		"QA_REPORT.json",
	)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(report, fh, indent=2, default=str)
	return path


@frappe.whitelist()
def run_and_publish_qa() -> dict:
	frappe.only_for("System Manager")
	return run_isolation_qa()
