from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, cint


def _rule_applies(rule: dict, doc, amount: float) -> bool:
	if not cint(rule.get("is_active")):
		return False
	if (rule.get("doctype_name") or "") != (doc.doctype or ""):
		return False
	if rule.get("company") and rule.get("company") != doc.get("company"):
		return False
	if rule.get("branch") and doc.meta.has_field("branch") and rule.get("branch") != doc.get("branch"):
		return False
	entry_type = (rule.get("entry_type") or "").strip()
	if entry_type:
		doc_entry_type = ""
		if doc.meta.has_field("entry_type"):
			doc_entry_type = (doc.get("entry_type") or "").strip()
		elif doc.meta.has_field("payment_purpose"):
			doc_entry_type = (doc.get("payment_purpose") or "").strip()
		if entry_type.lower() != doc_entry_type.lower():
			return False
	min_amount = flt(rule.get("min_amount"))
	max_amount = flt(rule.get("max_amount"))
	if amount < min_amount:
		return False
	if max_amount and amount > max_amount:
		return False
	return True


def _doc_amount(doc) -> float:
	if doc.doctype == "Journal Entry":
		return sum(flt(r.get("debit")) for r in (doc.get("accounts") or []))
	if doc.doctype == "Payment Entry":
		return flt(doc.get("paid_amount"))
	return 0.0


def enforce_posting_rules(doc):
	"""Apply matched Finance Posting Rule constraints to JE/Payment."""
	if not getattr(doc, "doctype", None):
		return
	if doc.doctype not in {"Journal Entry", "Payment Entry"}:
		return
	if not (frappe.db.exists("DocType", "Finance Posting Rule") and frappe.db.table_exists("tabFinance Posting Rule")):
		return

	rules = frappe.get_all(
		"Finance Posting Rule",
		filters={"is_active": 1, "doctype_name": doc.doctype},
		fields=[
			"name",
			"is_active",
			"doctype_name",
			"company",
			"branch",
			"entry_type",
			"min_amount",
			"max_amount",
			"required_cost_center",
			"required_project",
			"enforce_reference",
		],
		limit_page_length=500,
	)
	if not rules:
		return

	amount = _doc_amount(doc)
	matched = [r for r in rules if _rule_applies(r, doc, amount)]
	if not matched:
		return

	for rule in matched:
		if cint(rule.get("required_cost_center")):
			if doc.doctype == "Journal Entry":
				for row in doc.get("accounts") or []:
					if not (row.get("cost_center") or "").strip():
						frappe.throw(
							_("Finance rule {0}: Cost Center is required for all lines.").format(rule.get("name")),
							title=_("Compliance"),
						)
			elif doc.doctype == "Payment Entry":
				# best-effort: reference lines can carry CC in some setups; fallback to header custom field if exists
				if doc.meta.has_field("cost_center") and not (doc.get("cost_center") or "").strip():
					frappe.throw(
						_("Finance rule {0}: Cost Center is required.").format(rule.get("name")),
						title=_("Compliance"),
					)
		if cint(rule.get("required_project")):
			if doc.doctype == "Journal Entry":
				for row in doc.get("accounts") or []:
					if not (row.get("project") or "").strip():
						frappe.throw(
							_("Finance rule {0}: Project is required for all lines.").format(rule.get("name")),
							title=_("Compliance"),
						)
		if cint(rule.get("enforce_reference")):
			ref = (doc.get("reference") or "").strip() if doc.meta.has_field("reference") else ""
			ext = (doc.get("external_reference") or "").strip() if doc.meta.has_field("external_reference") else ""
			if not (ref or ext):
				frappe.throw(
					_("Finance rule {0}: Reference or External Reference is required.").format(rule.get("name")),
					title=_("Compliance"),
				)

