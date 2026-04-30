from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled


@frappe.whitelist()
def execute_stock_transfer_request(transfer_request: str):
	"""Create and submit Stock Entry from approved Stock Transfer Request."""
	if not transfer_request or not frappe.db.exists("Stock Transfer Request", transfer_request):
		frappe.throw(_("Stock Transfer Request not found."))

	doc = frappe.get_doc("Stock Transfer Request", transfer_request)
	if doc.docstatus != 1:
		frappe.throw(_("Stock Transfer Request must be submitted before execution."))
	if doc.executed_stock_entry:
		return {"stock_entry": doc.executed_stock_entry, "already_executed": 1}

	se = frappe.new_doc("Stock Entry")
	se.company = doc.company
	se.branch = doc.branch
	se.posting_date = doc.request_date
	se.purpose = "Material Transfer"
	se.from_warehouse = doc.from_warehouse
	se.to_warehouse = doc.to_warehouse
	se.reference = doc.name
	if se.meta.has_field("transfer_request"):
		se.transfer_request = doc.name
	for r in doc.items or []:
		se.append(
			"items",
			{
				"item": r.item,
				"item_code": r.item_code,
				"qty": r.qty,
				"uom": r.uom,
				"s_warehouse": doc.from_warehouse,
				"t_warehouse": doc.to_warehouse,
				"batch_no": r.batch_no,
				"serial_no": r.serial_no,
			},
		)
	se.insert(ignore_permissions=True)
	se.submit()

	doc.db_set("executed_stock_entry", se.name, update_modified=False)
	doc.db_set("status", "Completed", update_modified=False)
	return {"stock_entry": se.name, "already_executed": 0}


@frappe.whitelist()
def get_reorder_suggestions(company: str | None = None, branch: str | None = None, limit: int = 100):
	"""Return low-stock / reorder suggestions by Item thresholds."""
	limit = max(1, min(cint(limit or 100), 500))
	if not frappe.db.exists("DocType", "Item"):
		return []

	filters = {"disabled": 0, "is_stock_item": 1}
	if company and frappe.get_meta("Item").has_field("company"):
		filters["company"] = company
	items = frappe.get_all(
		"Item",
		filters=filters,
		fields=["name", "item_code", "item_name", "current_stock_qty", "reorder_level", "safety_stock"],
		limit_page_length=5000,
	)
	out = []
	for it in items:
		rl = float(it.get("reorder_level") or 0)
		ss = float(it.get("safety_stock") or 0)
		threshold = max(rl, ss)
		if threshold <= 0:
			continue
		qty = float(it.get("current_stock_qty") or 0)
		if qty <= threshold:
			out.append(
				{
					"item": it.get("name"),
					"item_code": it.get("item_code"),
					"item_name": it.get("item_name"),
					"current_stock_qty": qty,
					"reorder_level": rl,
					"safety_stock": ss,
					"suggested_qty": max(0.0, threshold - qty),
				}
			)
	out.sort(key=lambda x: (x["suggested_qty"], x["item_code"] or ""), reverse=True)
	return out[:limit]


@frappe.whitelist()
def create_purchase_request_from_reorder(
	company: str,
	branch: str | None = None,
	limit: int = 100,
	min_suggested_qty: float = 0.0001,
):
	"""Create Purchase Request from reorder suggestions (feature-flagged)."""
	if not is_feature_enabled("global_inventory_auto_purchase_request", default=False):
		return {"created": None, "skipped": "Feature flag disabled"}
	suggestions = get_reorder_suggestions(company=company, branch=branch, limit=limit)
	rows = [s for s in suggestions if float(s.get("suggested_qty") or 0) >= float(min_suggested_qty or 0)]
	if not rows:
		return {"created": None, "skipped": "No reorder suggestions"}

	if not frappe.db.exists("DocType", "Purchase Request"):
		return {"created": None, "skipped": "Purchase Request DocType missing"}

	pr = frappe.new_doc("Purchase Request")
	pr.company = company
	if pr.meta.has_field("branch") and branch:
		pr.branch = branch
	if pr.meta.has_field("required_by"):
		pr.required_by = frappe.utils.today()
	if pr.meta.has_field("remarks"):
		pr.remarks = "Auto-generated from inventory reorder suggestions"
	for s in rows:
		pr.append(
			"items",
			{
				"item_code": s.get("item_code") or "",
				"qty": s.get("suggested_qty") or 0,
				"purpose": "Reorder trigger",
			},
		)
	pr.insert(ignore_permissions=True)
	return {"created": pr.name, "item_count": len(rows)}


@frappe.whitelist()
def inventory_feature_flags():
	return {
		"inventory_controls": cint(is_feature_enabled("global_inventory_controls", default=True)),
		"prevent_negative_stock": cint(is_feature_enabled("global_inventory_prevent_negative_stock", default=True)),
	}

