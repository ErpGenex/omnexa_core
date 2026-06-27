# Copyright (c) 2026, ErpGenEx
"""Shared finance vertical BPE — workflow, roles, SoD, demo seed (11 apps + MF delegate)."""

from __future__ import annotations

import json
from datetime import date

import frappe
from frappe import _
from frappe.utils import now_datetime

from omnexa_core.omnexa_core.finance_demo.finance_vertical_specs import (
	VERTICAL_BPE_APPS,
	VERTICAL_BPE_SPECS,
	get_spec,
)

from omnexa_core.omnexa_core.finance_demo.finance_stage_gate import (
	SENSITIVE_GATE_ACTIONS,
	UNIVERSAL_STAGE_GATE_STATES,
	UNIVERSAL_STAGE_GATE_TRANSITIONS,
)

SENSITIVE_ACTIONS = SENSITIVE_GATE_ACTIONS

# Legacy alias — stage-gate demo seed rows (7 samples across gate states)
DEMO_WORKFLOW_ROWS = [
	("Draft", "Draft", 0),
	("Submitted", "Submitted", 0),
	("Assigned", "Assigned", 0),
	("In Progress", "In Progress", 0),
	("Pending Approval", "Pending Approval", 0),
	("Completed", "Completed", 1),
	("Closed", "Closed", 1),
]


def _role(prefix: str, suffix: str) -> str:
	return f"{prefix} {suffix}"


def _ensure_workflow_state(state: str, style: str = "Primary") -> None:
	if frappe.db.exists("Workflow State", state):
		return
	frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state, "style": style}).insert(
		ignore_permissions=True
	)


def _ensure_workflow_action(action: str) -> None:
	if frappe.db.exists("Workflow Action Master", action):
		return
	frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
		ignore_permissions=True
	)


def _ensure_custom_field(doctype: str, fieldname: str, fieldtype: str, label: str, module: str, **kwargs) -> None:
	cf = f"{doctype}-{fieldname}"
	if frappe.db.exists("Custom Field", cf):
		return
	doc = {
		"doctype": "Custom Field",
		"dt": doctype,
		"fieldname": fieldname,
		"fieldtype": fieldtype,
		"label": label,
		"module": module,
		"insert_after": kwargs.get("insert_after") or "modified",
	}
	if options := kwargs.get("options"):
		doc["options"] = options
	prev = frappe.flags.in_import
	frappe.flags.in_import = True
	try:
		frappe.get_doc(doc).insert(ignore_permissions=True)
	finally:
		frappe.flags.in_import = prev


def _repair_broken_bpe_custom_fields() -> None:
	"""Fix workflow_state Link fields created without options."""
	for row in frappe.get_all(
		"Custom Field",
		filters={"fieldname": "workflow_state", "fieldtype": "Link"},
		fields=["name", "options", "dt"],
	):
		if row.options:
			continue
		frappe.db.set_value("Custom Field", row.name, "options", "Workflow State", update_modified=False)
	frappe.db.commit()


def ensure_bpe_fields(spec: dict) -> None:
	dt = spec["case_doctype"]
	mod = spec["module"]
	if not frappe.db.exists("DocType", dt):
		return
	_repair_broken_bpe_custom_fields()
	meta = frappe.get_meta(dt)
	if meta.get_field("workflow_state") and meta.get_field("rejection_reason") and meta.get_field("sla_due"):
		return
	meta = frappe.get_meta(dt)
	if not meta.get_field("workflow_state"):
		_ensure_custom_field(
			dt,
			"workflow_state",
			"Data",
			"Workflow State",
			mod,
			insert_after="modified",
		)
	if not meta.get_field("rejection_reason"):
		_ensure_custom_field(dt, "rejection_reason", "Small Text", "Rejection Reason", mod)
	if not meta.get_field("sla_due"):
		_ensure_custom_field(dt, "sla_due", "Datetime", "SLA Due", mod)
	frappe.clear_cache(doctype=dt)


def _is_core_doctype(doctype: str) -> bool:
	"""ERPNext standard DocTypes must not be mutated via DocType.save()."""
	if not frappe.db.exists("DocType", doctype):
		return False
	return not bool(frappe.db.get_value("DocType", doctype, "custom"))


def ensure_submittable(doctype: str) -> None:
	if not frappe.db.exists("DocType", doctype) or _is_core_doctype(doctype):
		return
	if not frappe.db.get_value("DocType", doctype, "is_submittable"):
		frappe.db.set_value("DocType", doctype, "is_submittable", 1, update_modified=False)
		frappe.clear_cache(doctype=doctype)


def ensure_vertical_roles(spec: dict) -> list[str]:
	prefix = spec["prefix"]
	created = []
	for suffix in ("Field Officer", "Branch Manager", "Disbursement Officer", "Collection Officer", "Risk Analyst"):
		name = _role(prefix, suffix)
		if not frappe.db.exists("Role", name):
			frappe.get_doc({"doctype": "Role", "role_name": name, "desk_access": 1}).insert(ignore_permissions=True)
			created.append(name)
	return created


def sync_case_permissions(spec: dict) -> None:
	dt = spec["case_doctype"]
	if spec.get("standard_doctype") or _is_core_doctype(dt):
		return
	prefix = spec["prefix"]
	desk = spec["desk_role"]
	if not frappe.db.exists("DocType", dt):
		return
	ensure_submittable(dt)
	meta = frappe.get_doc("DocType", dt)
	submittable = bool(meta.is_submittable)
	perms = [
		(_role(prefix, "Field Officer"), dict(create=1, read=1, write=1, submit=0)),
		(_role(prefix, "Branch Manager"), dict(create=0, read=1, write=1, submit=1 if submittable else 0)),
		(_role(prefix, "Disbursement Officer"), dict(create=0, read=1, write=1, submit=1 if submittable else 0)),
		(_role(prefix, "Collection Officer"), dict(create=0, read=1, write=1, submit=0)),
		(_role(prefix, "Risk Analyst"), dict(create=0, read=1, write=1, submit=0)),
		(desk, dict(create=1, read=1, write=1, submit=1 if submittable else 0)),
	]
	existing = {r.role: r for r in meta.permissions}
	for role, p in perms:
		row = {
			"role": role,
			"create": p.get("create", 0),
			"read": p.get("read", 1),
			"write": p.get("write", 0),
			"delete": 0,
			"submit": p.get("submit", 0),
			"cancel": 0,
			"amend": 0,
			"report": 1,
			"export": 1,
			"print": 1,
			"email": 1,
			"share": 1,
		}
		if role in existing:
			doc = existing[role]
			for k, v in row.items():
				if k != "role":
					setattr(doc, k, v)
		else:
			meta.append("permissions", row)
	meta.flags.ignore_permissions = True
	meta.save()
	frappe.clear_cache(doctype=dt)


def _build_states(spec: dict) -> list[dict]:
	prefix = spec["prefix"]
	desk = spec["desk_role"]
	lifecycle_field = spec.get("lifecycle_field")
	lifecycle_disbursed = spec.get("lifecycle_disbursed")
	lifecycle_closed = spec.get("lifecycle_closed")
	states = []
	for state, doc_status, style, role_suffix in UNIVERSAL_STAGE_GATE_STATES:
		_ensure_workflow_state(state, style)
		row = {
			"state": state,
			"doc_status": str(doc_status),
			"style": style,
			"allow_edit": _role(prefix, role_suffix),
		}
		if lifecycle_field and frappe.get_meta(spec["case_doctype"]).get_field(lifecycle_field):
			if state == "Completed" and lifecycle_disbursed:
				row["update_field"] = lifecycle_field
				row["update_value"] = lifecycle_disbursed
			elif state == "Closed" and lifecycle_closed:
				row["update_field"] = lifecycle_field
				row["update_value"] = lifecycle_closed
		states.append(row)
	return states


def _build_transitions(spec: dict) -> list[dict]:
	prefix = spec["prefix"]
	desk = spec["desk_role"]
	p = prefix
	out = []
	seen: set[tuple] = set()
	for state, action, next_state, role_suffix, self_ok in UNIVERSAL_STAGE_GATE_TRANSITIONS:
		_ensure_workflow_action(action)
		for allowed in (_role(p, role_suffix), desk):
			key = (state, action, next_state, allowed)
			if key in seen:
				continue
			seen.add(key)
			out.append(
				{
					"state": state,
					"action": action,
					"next_state": next_state,
					"allowed": allowed,
					"allow_self_approval": self_ok,
				}
			)
		if state == "Pending Approval" and action == "Approve":
			key = (state, action, next_state, "Finance Group Executive")
			if key not in seen:
				seen.add(key)
				out.append(
					{
						"state": state,
						"action": action,
						"next_state": next_state,
						"allowed": "Finance Group Executive",
						"allow_self_approval": 0,
					}
				)
		if state == "Escalated" and action == "Executive Approve":
			key = (state, action, next_state, "Finance Group Executive")
			if key not in seen:
				seen.add(key)
				out.append(
					{
						"state": state,
						"action": action,
						"next_state": next_state,
						"allowed": "Finance Group Executive",
						"allow_self_approval": 0,
					}
				)
	return out


def _deactivate_other_workflows(doctype: str, keep_name: str) -> None:
	for row in frappe.get_all("Workflow", filters={"document_type": doctype}, fields=["name", "is_active"]):
		if row.name == keep_name or not row.is_active:
			continue
		frappe.db.set_value("Workflow", row.name, "is_active", 0, update_modified=False)


def sync_vertical_workflow(spec: dict) -> str:
	dt = spec["case_doctype"]
	name = spec["workflow_name"]
	if not frappe.db.exists("DocType", dt):
		return ""
	states = _build_states(spec)
	transitions = _build_transitions(spec)
	if frappe.db.exists("Workflow", name):
		wf = frappe.get_doc("Workflow", name)
	else:
		wf = frappe.new_doc("Workflow")
		wf.workflow_name = name
		wf.document_type = dt
		wf.workflow_state_field = "workflow_state"
	wf.is_active = 1
	wf.override_status = 0
	wf.send_email_alert = 1
	wf.set("states", [])
	wf.set("transitions", [])
	for s in states:
		wf.append("states", s)
	for t in transitions:
		wf.append("transitions", t)
	wf.flags.ignore_permissions = True
	if wf.get("name"):
		wf.save()
	else:
		wf.insert()
	_deactivate_other_workflows(dt, name)
	frappe.clear_cache(doctype=dt)
	return name


def before_workflow_action(doc, method=None, action=None):
	"""Shared SoD guard — wired from omnexa_core hooks."""
	action = action or (frappe.form_dict or {}).get("action") or ""
	if action not in SENSITIVE_ACTIONS:
		return
	if doc.owner == frappe.session.user and action in ("Approve", "Final Approve", "Executive Approve", "Complete"):
		frappe.throw(_("Segregation of Duties: you cannot {0} a record you created.").format(action))


def _demo_finance_product() -> str | None:
	if not frappe.db.exists("DocType", "Finance Product"):
		return None
	name = "Demo Finance Product"
	if frappe.db.exists("Finance Product", name):
		return name
	try:
		doc = frappe.get_doc(
			{
				"doctype": "Finance Product",
				"product_name": name,
				"product_code": "DEMO-FE",
				"country_code": "INTL",
				"currency": frappe.defaults.get_global_default("currency") or "USD",
				"status": "ACTIVE",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		return frappe.db.get_value("Finance Product", {}, "name")


def _base_seed_doc(spec: dict, label: str, company: str | None, branch: str | None) -> dict:
	dt = spec["case_doctype"]
	doc = {"doctype": dt}
	meta = frappe.get_meta(dt)
	today = date.today().isoformat()

	def set_if(field: str, value):
		if meta.get_field(field):
			doc[field] = value

	set_if("customer_name", label)
	set_if("incident_title", label)
	set_if("run_name", label)
	set_if("run_reference", label)
	set_if("business_name", f"{label} LLC")
	set_if("principal", 50000)
	set_if("term_months", 24)
	set_if("country_code", "INTL")
	set_if("company", company)
	set_if("branch", branch)
	set_if("run_date", today)
	set_if("valuation_date", today)
	set_if("scenario_payload", json.dumps({"demo": True}))
	set_if("result_json", json.dumps({"demo": True, "status": "ok"}))
	set_if("input_hash", "demo-seed")
	set_if("run_status", "SUCCESS")
	set_if("collateral_value", 60000)
	set_if("invoice_face_value", 75000)
	set_if("advance_rate", 80)
	set_if("debtor_id", "DEB-DEMO-001")
	set_if("portfolio_id", "PORT-DEMO")
	set_if("lease_type", "FINANCE")
	set_if("currency", frappe.defaults.get_global_default("currency") or "USD")
	set_if("discount_rate", 8.5)
	set_if("residual_value", 5000)
	set_if("event_type", "PROCESS_FAILURE")
	if dt == "Operational Risk Incident":
		set_if("status", "REPORTED")
	set_if("incident_date", today)
	set_if("description", "Demo incident for GRC simulation")
	set_if("required_controls", "KYC,AML,DUAL_APPROVAL")
	set_if("sla_due", now_datetime())
	set_if("annual_rate", 12.5)
	set_if("periods", 24)
	set_if("start_date", today)
	set_if("first_due_date", today)
	set_if("property_value", 250000)
	set_if("sector_code", "RETAIL")
	set_if("impact_score", 3)
	set_if("likelihood_score", 2)
	set_if("velocity_score", 2)
	set_if("control_effectiveness", 70)
	set_if("amortization", "ANNUITY")
	set_if("payment_frequency", "MONTHLY")
	product = _demo_finance_product()
	if product and meta.get_field("product"):
		doc["product"] = product
	if meta.get_field("currency") and "currency" not in doc:
		doc["currency"] = frappe.defaults.get_global_default("currency") or "USD"
	return doc


def seed_vertical_demo(app: str, company: str | None = None, branch: str | None = None) -> dict:
	spec = get_spec(app)
	if spec and spec.get("delegate_seed"):
		return frappe.get_attr(spec["delegate_seed"])(company=company, branch=branch)
	if spec and spec.get("skip_seed"):
		return {"ok": True, "app": app, "created": [], "count": 0, "skipped": True}
	if not spec:
		return {"ok": False, "reason": "unknown_app"}
	dt = spec["case_doctype"]
	if not frappe.db.exists("DocType", dt):
		return {"ok": False, "reason": "doctype_missing", "doctype": dt}
	label_field = spec["seed_label_field"]
	prefix = spec["seed_prefix"]
	created = []
	for idx, (label_suffix, workflow_state, docstatus) in enumerate(DEMO_WORKFLOW_ROWS, start=1):
		label = f"{prefix} {label_suffix} #{idx}"
		if frappe.db.exists(dt, {label_field: label}):
			continue
		payload = _base_seed_doc(spec, label, company, branch)
		payload[label_field] = label
		doc = frappe.get_doc(payload)
		doc.insert(ignore_permissions=True)
		if doc.meta.get_field("workflow_state"):
			frappe.db.set_value(dt, doc.name, "workflow_state", workflow_state, update_modified=False)
		if docstatus and doc.meta.is_submittable:
			doc.reload()
			doc.docstatus = 1
			doc.save(ignore_permissions=True)
		created.append(doc.name)
	frappe.db.commit()
	return {"ok": True, "app": app, "created": created, "count": len(created)}


def sync_vertical_bpe(app: str) -> dict:
	spec = get_spec(app)
	if not spec:
		return {"ok": False, "reason": "unknown_app"}
	if app not in set(frappe.get_installed_apps() or []):
		return {"ok": False, "reason": "not_installed"}
	ensure_bpe_fields(spec)
	roles = ensure_vertical_roles(spec)
	sync_case_permissions(spec)
	wf = sync_vertical_workflow(spec)
	out = {"ok": True, "app": app, "workflow": wf, "roles_created": roles, "stage_gate": True}
	if app == "omnexa_sme_microfinance":
		try:
			from omnexa_sme_microfinance.mf_report import ensure_microfinance_portfolio_report

			out["report"] = ensure_microfinance_portfolio_report()
		except Exception:
			pass
	return out


@frappe.whitelist()
def sync_all_finance_vertical_bpe() -> dict:
	frappe.only_for("System Manager")
	results = []
	for app in VERTICAL_BPE_APPS:
		try:
			results.append(sync_vertical_bpe(app))
		except Exception as exc:
			frappe.log_error(frappe.get_traceback(), f"sync_vertical_bpe:{app}")
			results.append({"ok": False, "app": app, "error": str(exc)})
	frappe.db.commit()
	return {"ok": True, "results": results, "stage_gate_version": "14-state-universal"}


@frappe.whitelist()
def seed_all_finance_vertical_demos(company: str | None = None, branch: str | None = None) -> dict:
	frappe.only_for("System Manager")
	from omnexa_core.omnexa_core.finance_demo.finance_role_demo import _resolve_demo_company_branch

	company, branch = _resolve_demo_company_branch(company, branch)
	sync_all_finance_vertical_bpe()
	apps = list(VERTICAL_BPE_APPS)
	out = []
	for app in apps:
		if app not in set(frappe.get_installed_apps() or []):
			continue
		try:
			out.append(seed_vertical_demo(app, company, branch))
		except Exception as exc:
			frappe.log_error(frappe.get_traceback(), f"seed_vertical_demo:{app}")
			out.append({"ok": False, "app": app, "error": str(exc)})
	frappe.db.commit()
	return {"ok": True, "company": company, "branch": branch, "seeds": out}
