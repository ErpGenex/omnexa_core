# Copyright (c) 2026, ErpGenEx
"""Generic approval workflow engine for Global Excellence boost."""

from __future__ import annotations

import frappe


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


def _state(state, doc_status, *, allow_edit="All", style="Primary", update_field=None, update_value=None):
	_ensure_workflow_state(state, style)
	row = {"state": state, "doc_status": str(doc_status), "style": style, "allow_edit": allow_edit}
	if update_field:
		row["update_field"] = update_field
		row["update_value"] = update_value
	return row


def _transition(state, action, next_state, allowed="System Manager"):
	_ensure_workflow_action(action)
	_ensure_workflow_state(state)
	_ensure_workflow_state(next_state)
	return {
		"state": state,
		"action": action,
		"next_state": next_state,
		"allowed": allowed,
		"allow_self_approval": 1,
	}


def _workflow_state_field(doctype: str) -> str | None:
	meta = frappe.get_meta(doctype)
	if meta.has_field("workflow_state"):
		return "workflow_state"
	if meta.has_field("status") and meta.get_field("status").fieldtype in ("Select", "Data"):
		return "status"
	return None


def ensure_workflow_state_custom_field(doctype: str) -> bool:
	"""Add workflow_state Link field when missing so approval workflows can attach."""
	if not frappe.db.exists("DocType", doctype):
		return False
	if _workflow_state_field(doctype):
		return True
	meta = frappe.get_meta(doctype)
	if meta.issingle or meta.istable:
		return False
	if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": "workflow_state"}):
		frappe.clear_cache(doctype=doctype)
		return True

	insert_after = None
	for candidate in ("amended_from", "status", "naming_series"):
		if meta.has_field(candidate):
			insert_after = candidate
			break
	if not insert_after and meta.fields:
		insert_after = meta.fields[0].fieldname

	doc = frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": "workflow_state",
			"label": "Workflow State",
			"fieldtype": "Link",
			"options": "Workflow State",
			"insert_after": insert_after,
			"allow_on_submit": 1 if meta.is_submittable else 0,
			"no_copy": 1,
		}
	)
	frappe.flags.ignore_validate = True
	try:
		doc.insert(ignore_permissions=True)
	except Exception:
		frappe.db.rollback()
		return False
	finally:
		frappe.flags.ignore_validate = False
	frappe.clear_cache(doctype=doctype)
	return True


def ensure_standard_approval_workflow(doctype: str, *, workflow_name: str | None = None) -> str | None:
	"""Draft → Pending Approval → Approved (+ Rejected) for business DocTypes."""
	if not frappe.db.exists("DocType", doctype):
		return None
	state_field = _workflow_state_field(doctype)
	if not state_field:
		return None
	meta = frappe.get_meta(doctype)
	is_submittable = bool(meta.is_submittable)
	wf_name = workflow_name or f"{doctype} Approval"
	if frappe.db.exists("Workflow", wf_name):
		frappe.db.set_value("Workflow", wf_name, "is_active", 1)
		return wf_name

	if is_submittable:
		states = [
			_state("Draft", 0),
			_state("Pending Approval", 0, allow_edit="System Manager", style="Warning"),
			_state("Approved", 1, allow_edit="System Manager", style="Success"),
			_state("Cancelled", 2, allow_edit="System Manager", style="Danger"),
		]
		transitions = [
			_transition("Draft", "Submit for Approval", "Pending Approval"),
			_transition("Pending Approval", "Approve", "Approved"),
			_transition("Approved", "Cancel", "Cancelled"),
		]
	else:
		states = [
			_state("Draft", 0),
			_state("Pending Approval", 0, allow_edit="System Manager", style="Warning"),
			_state("Approved", 0, allow_edit="System Manager", style="Success"),
			_state("Rejected", 0, allow_edit="System Manager", style="Danger"),
		]
		transitions = [
			_transition("Draft", "Submit for Approval", "Pending Approval"),
			_transition("Pending Approval", "Approve", "Approved"),
			_transition("Pending Approval", "Reject", "Rejected"),
		]

	wf = frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": wf_name,
			"document_type": doctype,
			"is_active": 1,
			"override_status": 0,
			"workflow_state_field": state_field,
			"send_email_alert": 0,
			"states": states,
			"transitions": transitions,
		}
	)
	wf.insert(ignore_permissions=True)
	return wf_name


def sync_workflows_for_app(modules: list[str], *, target: int = 7) -> list[str]:
	"""Ensure up to `target` workflows for an app's business DocTypes."""
	if not modules:
		return []
	existing = frappe.db.sql(
		f"""
		SELECT DISTINCT document_type FROM tabWorkflow
		WHERE document_type IN (
			SELECT name FROM tabDocType
			WHERE custom = 0 AND istable = 0 AND module IN ({", ".join(["%s"] * len(modules))})
		)
		""",
		tuple(modules),
		pluck=True,
	)
	created: list[str] = []
	if len(existing) >= target:
		return created

	rows = frappe.db.sql(
		f"""
		SELECT name, is_submittable FROM tabDocType
		WHERE custom = 0 AND istable = 0 AND module IN ({", ".join(["%s"] * len(modules))})
		ORDER BY is_submittable DESC, name
		""",
		tuple(modules),
		as_dict=True,
	)
	for row in rows:
		if len(existing) + len(created) >= target:
			break
		if row.name in existing:
			continue
		try:
			if not row.is_submittable and not _workflow_state_field(row.name):
				ensure_workflow_state_custom_field(row.name)
			if not row.is_submittable and not _workflow_state_field(row.name):
				continue
			name = ensure_standard_approval_workflow(row.name)
			if name:
				created.append(name)
				frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			continue
	frappe.clear_cache(doctype="Workflow")
	return created
