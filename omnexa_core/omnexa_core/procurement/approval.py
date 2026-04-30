from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


def get_required_purchase_approver_role(*, company: str | None, amount: float) -> str | None:
	"""Return approver role by matching `Purchase Approval Rule` thresholds.

	Strategy: pick the *highest* role requirement among matching ranges (min/max).
	"""
	if not company:
		return None
	if not (frappe.db.exists("DocType", "Purchase Approval Rule") and frappe.db.table_exists("tabPurchase Approval Rule")):
		return None

	amount = flt(amount)
	rules = frappe.get_all(
		"Purchase Approval Rule",
		filters={"is_active": 1, "company": company},
		fields=["name", "approver_role", "min_amount", "max_amount"],
		limit_page_length=200,
	)
	if not rules:
		return None

	matches = []
	for r in rules:
		min_a = flt(r.get("min_amount"))
		max_a = flt(r.get("max_amount"))
		if amount < min_a:
			continue
		if max_a and amount > max_a:
			continue
		role = (r.get("approver_role") or "").strip()
		if role:
			matches.append((min_a, max_a, role))

	if not matches:
		return None
	# Prefer the most restrictive rule: highest min_amount.
	matches.sort(key=lambda x: x[0], reverse=True)
	return matches[0][2]


def enforce_purchase_approval(doc):
	"""Enforce approval matrix at submit-time by role check (behind feature flag)."""
	if not getattr(doc, "doctype", None):
		return
	if not doc.meta.has_field("company"):
		return
	company = doc.get("company")
	amount = flt(doc.get("grand_total")) if doc.meta.has_field("grand_total") else 0.0
	role = get_required_purchase_approver_role(company=company, amount=amount)
	if not role:
		return
	# Optional: store role on doc if custom field exists.
	if doc.meta.has_field("required_approver_role"):
		doc.set("required_approver_role", role)

	if "System Manager" in (frappe.get_roles() or []):
		return
	if role not in (frappe.get_roles() or []):
		frappe.throw(
			_("Approval required: role '{0}' must approve this document.").format(role),
			title=_("Compliance"),
		)

