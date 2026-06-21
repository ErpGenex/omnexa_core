# Copyright (c) 2026, ErpGenEx
"""Branch-scoped finance group demo — realistic operations simulation (50 clients per app)."""

from __future__ import annotations

import random
from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from omnexa_core.omnexa_core.finance_demo.finance_vertical_bpe import (
	_base_seed_doc,
	sync_all_finance_vertical_bpe,
	sync_vertical_bpe,
)
from omnexa_core.omnexa_core.finance_demo.finance_vertical_specs import VERTICAL_BPE_APPS, VERTICAL_BPE_SPECS, get_spec

DEMO_MARKER = "DEMO-FG"
REPORTING_TAG = "FINANCE-BRANCH-DEMO"

# Spread 50 records across the universal stage-gate pipeline (normal operations mix).
OPERATIONS_PROFILE: list[tuple[str, int, str]] = [
	("Draft", 0, "origination"),
	("Submitted", 0, "origination"),
	("Assigned", 0, "origination"),
	("In Progress", 0, "origination"),
	("Pending Review", 0, "approval"),
	("Pending Approval", 0, "approval"),
	("Approved", 0, "approved"),
	("Completed", 1, "servicing"),
	("Completed", 1, "servicing"),
	("Closed", 1, "closed"),
]

SECTOR_CODES = ("RETAIL", "TRADE", "MANUFACTURING", "SERVICES", "AGRI", "TECH")
CUSTOMER_TYPES = ("Individual", "Corporate", "Corporate", "Individual", "Individual")


def _demo_customer_label(app_prefix: str, idx: int) -> str:
	return f"{DEMO_MARKER} {app_prefix} Client {idx:03d}"


def _profile_row(idx: int) -> tuple[str, int, str]:
	return OPERATIONS_PROFILE[(idx - 1) % len(OPERATIONS_PROFILE)]


def _lifecycle_value(spec: dict, bucket: str) -> str | None:
	field = spec.get("lifecycle_field")
	if not field:
		return None
	dt = spec["case_doctype"]
	if dt == "Leasing Finance Contract":
		return {
			"origination": "APPLICATION",
			"mid": "CREDIT_EVAL",
			"approve": "APPROVAL",
			"approved": "CONTRACT",
			"servicing": "ACTIVE",
			"closed": "TERMINATION",
		}.get(bucket, "APPLICATION")
	if dt == "ALM Daily Run":
		return "FAILED" if bucket in ("origination", "mid") else "SUCCESS"
	if bucket == "servicing":
		return spec.get("lifecycle_disbursed")
	if bucket == "closed":
		return spec.get("lifecycle_closed") or spec.get("lifecycle_disbursed")
	if bucket == "approved":
		return spec.get("lifecycle_disbursed") or spec.get("lifecycle_closed")
	if spec["case_doctype"] == "Microfinance Case":
		if bucket in ("origination", "approval"):
			return "Origination"
		if bucket == "servicing":
			return "Collection"
		if bucket == "closed":
			return "Closed"
		return "Disbursement"
	if spec["case_doctype"] == "Operational Risk Incident":
		if bucket == "closed":
			return "CLOSED"
		if bucket == "servicing":
			return "ACTION_APPROVED"
		return "REPORTED"
	if spec["case_doctype"] == "Credit Decision Case":
		if bucket in ("servicing", "closed", "approved"):
			return "APPROVED"
		return "REVIEW"
	if spec["case_doctype"] == "ALM Daily Run":
		return "FAILED" if bucket in ("origination", "mid") else "SUCCESS"
	if spec["case_doctype"] == "Leasing Finance Contract":
		return {
			"origination": "APPLICATION",
			"mid": "CREDIT_EVAL",
			"approve": "APPROVAL",
			"approved": "CONTRACT",
			"servicing": "ACTIVE",
			"closed": "TERMINATION",
		}.get(bucket, "APPLICATION")
	if spec["case_doctype"] == "Finance Contract Account":
		if bucket == "closed":
			return "CLOSED"
		if bucket in ("servicing", "approved"):
			return "ACTIVE"
		return "DRAFT"
	return "ORIGINATION" if bucket in ("origination", "approval") else "SERVICING"


def _principal_for_index(idx: int) -> float:
	base = 25000 + (idx % 10) * 7500
	return flt(base + random.randint(0, 5000), 2)


def _term_months(idx: int) -> int:
	return [12, 18, 24, 36, 48, 60][idx % 6]


def _ensure_customer_profile(
	company: str,
	branch: str,
	customer_code: str,
	customer_name: str,
	idx: int,
) -> str | None:
	if not frappe.db.exists("DocType", "Customer Profile"):
		return None
	if frappe.db.exists("Customer Profile", {"customer_code": customer_code, "company": company}):
		return frappe.db.get_value("Customer Profile", {"customer_code": customer_code, "company": company}, "name")
	doc = frappe.get_doc(
		{
			"doctype": "Customer Profile",
			"customer_code": customer_code,
			"customer_name": customer_name,
			"customer_type": CUSTOMER_TYPES[idx % len(CUSTOMER_TYPES)],
			"company": company,
			"branch": branch,
			"mobile_no": f"+20 10{idx:08d}"[:15],
			"email": f"demo.fg.{idx:03d}@erpgenex.local",
			"credit_limit": _principal_for_index(idx) * 1.2,
			"risk_score": 40 + (idx % 55),
			"status": "Active",
		}
	)
	doc.flags.ignore_branch_access = True
	doc.insert(ignore_permissions=True)
	return doc.name


def _enrich_case_doc(doc_dict: dict, spec: dict, idx: int, bucket: str) -> None:
	meta = frappe.get_meta(spec["case_doctype"])
	principal = _principal_for_index(idx)
	term = _term_months(idx)

	def set_if(field: str, value):
		if meta.get_field(field):
			doc_dict[field] = value

	set_if("principal", principal)
	set_if("term_months", term)
	set_if("annual_rate", flt(10 + (idx % 8) + random.random() * 2, 2))
	set_if("sector_code", SECTOR_CODES[idx % len(SECTOR_CODES)])
	set_if("business_name", f"{doc_dict.get(spec['seed_label_field'], 'Demo')} Trading Co.")
	set_if("member_count", 5 + (idx % 6))
	set_if("group_maturity_cycles", 1 + (idx % 3))
	set_if("collection_rate", 88 + (idx % 12))
	set_if("invoice_face_value", principal * 1.5)
	set_if("advance_rate", 75 + (idx % 20))
	set_if("collateral_value", principal * 1.25)
	set_if("property_value", principal * 4)
	set_if("annual_revenue", principal * 3)
	set_if("risk_score", 35 + (idx % 60))
	set_if("ifrs9_stage", ["STAGE_1", "STAGE_1", "STAGE_2", "STAGE_3"][idx % 4])
	set_if("collection_stage", ["CURRENT", "CURRENT", "30_DPD", "60_DPD", "90_DPD"][idx % 5])
	set_if("delinquency_days", [0, 0, 15, 45, 75][idx % 5])
	set_if("decision_status", "APPROVED" if bucket in ("servicing", "closed", "approved") else "REVIEW")
	if spec["case_doctype"] == "ALM Daily Run":
		set_if("run_status", "SUCCESS" if bucket in ("servicing", "closed", "approved") else "FAILED")
	set_if("impact_score", 1 + (idx % 5))
	set_if("likelihood_score", 1 + (idx % 4))
	lifecycle = _lifecycle_value(spec, bucket)
	if lifecycle and spec.get("lifecycle_field"):
		set_if(spec["lifecycle_field"], lifecycle)


def _existing_demo_count(spec: dict, company: str, branch: str) -> int:
	dt = spec["case_doctype"]
	label_field = spec["seed_label_field"]
	if not frappe.db.exists("DocType", dt):
		return 0
	filters = {label_field: ("like", f"{DEMO_MARKER}%")}
	meta = frappe.get_meta(dt)
	if meta.get_field("company"):
		filters["company"] = company
	if meta.get_field("branch"):
		filters["branch"] = branch
	return frappe.db.count(dt, filters)


def _delete_branch_demo(spec: dict, company: str, branch: str) -> int:
	dt = spec["case_doctype"]
	label_field = spec["seed_label_field"]
	if not frappe.db.exists("DocType", dt):
		return 0
	filters = {label_field: ("like", f"{DEMO_MARKER}%")}
	meta = frappe.get_meta(dt)
	if meta.get_field("company"):
		filters["company"] = company
	if meta.get_field("branch"):
		filters["branch"] = branch
	names = frappe.get_all(dt, filters=filters, pluck="name")
	for name in names:
		try:
			doc = frappe.get_doc(dt, name)
			if doc.meta.is_submittable and doc.docstatus == 1:
				doc.cancel()
			frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"finance_branch_demo_delete:{dt}:{name}")
	return len(names)


def seed_vertical_branch_simulation(
	app: str,
	company: str,
	branch: str,
	customers: int = 50,
	force: int = 0,
) -> dict:
	spec = get_spec(app)
	if not spec or spec.get("skip_seed"):
		return {"ok": True, "app": app, "skipped": True, "count": 0}
	if app not in set(frappe.get_installed_apps() or []):
		return {"ok": False, "app": app, "reason": "not_installed"}

	customers = max(1, min(cint(customers) or 50, 200))
	sync_vertical_bpe(app)

	if spec.get("delegate_seed") and app == "omnexa_sme_microfinance":
		from omnexa_sme_microfinance.mf_demo_seed import seed_microfinance_branch_demo

		return seed_microfinance_branch_demo(
			company=company, branch=branch, groups=customers, force=force, marker=DEMO_MARKER
		)

	dt = spec["case_doctype"]
	if not frappe.db.exists("DocType", dt):
		return {"ok": False, "app": app, "reason": "doctype_missing", "doctype": dt}

	existing = _existing_demo_count(spec, company, branch)
	if existing and not cint(force):
		return {
			"ok": True,
			"app": app,
			"message": "already_seeded",
			"count": existing,
			"hint": _("Finance demo already exists for {0} on this branch ({1} records). Enable Rebuild to re-seed.").format(
				app, existing
			),
		}

	if cint(force):
		_delete_branch_demo(spec, company, branch)

	label_field = spec["seed_label_field"]
	prefix = spec["seed_prefix"].replace("Demo ", "").strip() or spec["prefix"]
	created: list[str] = []
	profiles: list[str] = []
	today = date.today()

	for idx in range(1, customers + 1):
		label = _demo_customer_label(prefix, idx)
		if frappe.db.exists(dt, {label_field: label}):
			continue
		wf_state, docstatus, bucket = _profile_row(idx)
		payload = _base_seed_doc(spec, label, company, branch)
		payload[label_field] = label
		_enrich_case_doc(payload, spec, idx, bucket)

		if dt in ("ALM Daily Run", "Credit Risk Portfolio Stress Run"):
			run_date = (today - timedelta(days=idx % 30)).isoformat()
			if frappe.get_meta(dt).get_field("run_date"):
				payload["run_date"] = run_date
			if frappe.get_meta(dt).get_field("valuation_date"):
				payload["valuation_date"] = run_date
			if frappe.get_meta(dt).get_field("run_reference"):
				payload["run_reference"] = f"{DEMO_MARKER}-{prefix}-{idx:03d}"

		customer_code = f"FG-{prefix}-{idx:03d}"
		profile = _ensure_customer_profile(company, branch, customer_code, label, idx)
		if profile:
			profiles.append(profile)

		doc = frappe.get_doc(payload)
		doc.flags.ignore_branch_access = True
		doc.insert(ignore_permissions=True)
		if doc.meta.get_field("workflow_state"):
			frappe.db.set_value(dt, doc.name, "workflow_state", wf_state, update_modified=False)
		if doc.meta.get_field("sla_due"):
			frappe.db.set_value(dt, doc.name, "sla_due", now_datetime(), update_modified=False)
		if docstatus and doc.meta.is_submittable:
			doc.reload()
			doc.docstatus = 1
			doc.save(ignore_permissions=True)
		created.append(doc.name)

	frappe.db.commit()
	return {
		"ok": True,
		"app": app,
		"brand": spec.get("brand"),
		"created": created,
		"count": len(created),
		"profiles": len(profiles),
	}


@frappe.whitelist()
def seed_finance_group_branch_demo(
	company: str | None = None,
	branch: str | None = None,
	customers: int = 50,
	sync_roles: int = 1,
	force: int = 0,
) -> dict:
	"""Seed realistic finance-group operations demo for one branch (50 clients per vertical app)."""
	frappe.only_for("System Manager")
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Company is required"))
	if not branch or not frappe.db.exists("Branch", branch):
		frappe.throw(_("Branch is required"))
	if frappe.db.get_value("Branch", branch, "company") != company:
		frappe.throw(_("Branch does not belong to this company"))

	customers = max(1, min(cint(customers) or 50, 200))
	sync_all_finance_vertical_bpe()

	if cint(sync_roles):
		try:
			from omnexa_core.omnexa_core.finance_demo.finance_role_demo import seed_finance_role_demo

			seed_finance_role_demo(company=company, branch=branch)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "seed_finance_group_branch_demo:roles")

	if cint(force):
		reset_finance_demo_for_branch(company, branch, dry_run=0)
		force = 0

	results = []
	total_cases = 0
	total_profiles = 0
	for app in VERTICAL_BPE_APPS:
		try:
			row = seed_vertical_branch_simulation(
				app, company, branch, customers=customers, force=cint(force)
			)
			results.append(row)
			total_cases += cint(row.get("count") or 0)
			total_profiles += cint(row.get("profiles") or 0)
		except Exception as exc:
			frappe.log_error(frappe.get_traceback(), f"seed_finance_group_branch_demo:{app}")
			results.append({"ok": False, "app": app, "error": str(exc)})

	frappe.db.set_value(
		"Branch",
		branch,
		"branch_demo_activity",
		"Financial Services",
		update_modified=False,
	)
	frappe.db.commit()

	return {
		"ok": True,
		"company": company,
		"branch": branch,
		"customers_per_app": customers,
		"apps_seeded": len([r for r in results if r.get("ok") and not r.get("skipped")]),
		"total_cases": total_cases,
		"customer_profiles": total_profiles,
		"results": results,
		"tag": REPORTING_TAG,
	}


def reset_finance_demo_for_branch(company: str, branch: str, dry_run: int = 0) -> dict:
	deleted = {}
	for app, spec in VERTICAL_BPE_SPECS.items():
		if spec.get("skip_seed"):
			continue
		if dry_run:
			deleted[app] = _existing_demo_count(spec, company, branch)
		else:
			deleted[app] = _delete_branch_demo(spec, company, branch)

	profiles = 0
	if not dry_run and frappe.db.exists("DocType", "Customer Profile"):
		names = frappe.get_all(
			"Customer Profile",
			filters={"company": company, "branch": branch, "customer_code": ("like", "FG-%")},
			pluck="name",
		)
		for name in names:
			frappe.delete_doc("Customer Profile", name, force=1, ignore_permissions=True)
		profiles = len(names)
		frappe.db.commit()

	return {"ok": True, "dry_run": cint(dry_run), "deleted": deleted, "customer_profiles": profiles}
