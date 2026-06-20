# Copyright (c) 2026, ErpGenEx
"""Universal Stage-Gate Framework — 14 mandatory banking states (Tier-1 parity)."""

from __future__ import annotations

import frappe

# Phase 4 — mandatory states (no automatic transitions; each via explicit action)
UNIVERSAL_STAGE_GATE_STATES: list[tuple[str, int, str, str]] = [
	# state, docstatus, style, allow_edit_role_suffix
	("Draft", 0, "Primary", "Field Officer"),
	("Submitted", 0, "Info", "Field Officer"),
	("Assigned", 0, "Info", "Branch Manager"),
	("In Progress", 0, "Warning", "Field Officer"),
	("Pending Review", 0, "Warning", "Branch Manager"),
	("Pending Approval", 0, "Warning", "Branch Manager"),
	("Approved", 0, "Success", "Disbursement Officer"),
	("Returned", 0, "Danger", "Field Officer"),
	("Rejected", 0, "Danger", "Field Officer"),
	("Escalated", 0, "Danger", "Risk Analyst"),
	("Completed", 1, "Success", "Collection Officer"),
	("Cancelled", 0, "Danger", "Branch Manager"),
	("Closed", 1, "Success", "Branch Manager"),
]

# Maker → Checker → Approver explicit actions only
UNIVERSAL_STAGE_GATE_TRANSITIONS: list[tuple[str, str, str, str, int]] = [
	# state, action, next_state, allowed_role_suffix, self_approval
	("Draft", "Submit", "Submitted", "Field Officer", 1),
	("Submitted", "Assign", "Assigned", "Branch Manager", 0),
	("Assigned", "Start Work", "In Progress", "Field Officer", 0),
	("In Progress", "Send for Review", "Pending Review", "Field Officer", 1),
	("Pending Review", "Complete Review", "Pending Approval", "Branch Manager", 0),
	("Pending Review", "Return for Rework", "Returned", "Branch Manager", 0),
	("Returned", "Resume Work", "In Progress", "Field Officer", 0),
	("Pending Approval", "Approve", "Approved", "Branch Manager", 0),
	("Pending Approval", "Approve", "Approved", "Risk Analyst", 0),
	("Pending Approval", "Final Approve", "Approved", "Branch Manager", 0),
	("Pending Approval", "Reject", "Rejected", "Branch Manager", 0),
	("Pending Approval", "Escalate", "Escalated", "Risk Analyst", 0),
	("Escalated", "Executive Approve", "Approved", "Branch Manager", 0),
	("Approved", "Complete", "Completed", "Disbursement Officer", 0),
	("Completed", "Close", "Closed", "Branch Manager", 0),
	("Draft", "Cancel", "Cancelled", "Branch Manager", 0),
	("Submitted", "Cancel", "Cancelled", "Branch Manager", 0),
	("In Progress", "Cancel", "Cancelled", "Branch Manager", 0),
]

PROGRESS_TRACKER_STEPS: list[tuple[str, str, str]] = [
	("registration", "Customer Registration", "تسجيل العميل"),
	("kyc", "KYC", "اعرف عميلك"),
	("aml", "AML", "مكافحة غسل الأموال"),
	("scoring", "Scoring", "التسجيل الائتماني"),
	("risk", "Risk Assessment", "تقييم المخاطر"),
	("field", "Field Visit", "زيارة ميدانية"),
	("committee", "Committee", "اللجنة"),
	("approval", "Approval", "الاعتماد"),
	("contract", "Contract", "العقد"),
	("disbursement", "Disbursement", "الصرف"),
	("collection", "Collection", "التحصيل"),
	("closure", "Closure", "الإغلاق"),
]

# Map workflow_state → progress step index (approximate)
STATE_TO_PROGRESS: dict[str, int] = {
	"Draft": 0,
	"Submitted": 1,
	"Assigned": 2,
	"In Progress": 3,
	"Pending Review": 5,
	"Pending Approval": 7,
	"Approved": 8,
	"Completed": 9,
	"Closed": 11,
	"Returned": 3,
	"Rejected": 7,
	"Escalated": 7,
	"Cancelled": 0,
}

SENSITIVE_GATE_ACTIONS = frozenset(
	{"Complete Review", "Approve", "Final Approve", "Executive Approve", "Complete", "Close", "Reject"}
)


@frappe.whitelist()
def get_progress_tracker(doctype: str, name: str) -> dict:
	"""Visual progress tracker + timeline for stage-gate requests."""
	doc = frappe.get_doc(doctype, name)
	ws = getattr(doc, "workflow_state", None) or "Draft"
	current_idx = STATE_TO_PROGRESS.get(ws, 0)
	steps = []
	for idx, (key, en, ar) in enumerate(PROGRESS_TRACKER_STEPS):
		if idx < current_idx:
			status = "Completed"
		elif idx == current_idx:
			status = "In Progress" if ws not in ("Rejected", "Returned") else ws
		else:
			status = "Waiting"
		steps.append({"key": key, "label_en": en, "label_ar": ar, "status": status})
	timeline = []
	for row in frappe.get_all(
		"Version",
		filters={"ref_doctype": doctype, "docname": name},
		fields=["creation", "owner", "data"],
		order_by="creation desc",
		limit=50,
	):
		timeline.append(
			{
				"date": row.creation,
				"time": row.creation,
				"action": "Update",
				"user": row.owner,
				"role": frappe.db.get_value("Has Role", {"parent": row.owner, "parenttype": "User"}, "role") or "",
				"department": "",
				"status": ws,
				"comments": "",
			}
		)
	for row in frappe.get_all(
		"Comment",
		filters={"reference_doctype": doctype, "reference_name": name, "comment_type": "Comment"},
		fields=["creation", "owner", "content"],
		order_by="creation desc",
		limit=20,
	):
		timeline.append(
			{
				"date": row.creation,
				"time": row.creation,
				"action": "Comment",
				"user": row.owner,
				"role": "",
				"department": "",
				"status": ws,
				"comments": row.content,
			}
		)
	timeline.sort(key=lambda x: x["date"], reverse=True)
	return {
		"request": name,
		"doctype": doctype,
		"current_stage": ws,
		"current_owner": getattr(doc, "owner", ""),
		"current_department": getattr(doc, "branch", None) or getattr(doc, "company", None) or "",
		"sla_due": getattr(doc, "sla_due", None),
		"risk_level": getattr(doc, "risk_band", None) or getattr(doc, "risk_grade", None) or "",
		"approval_status": ws,
		"progress": steps,
		"timeline": timeline,
	}
