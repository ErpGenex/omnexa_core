from __future__ import annotations

import frappe
from frappe.utils import cint

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled
from omnexa_core.omnexa_core.procurement.pricing import find_best_supplier_rate


@frappe.whitelist()
def get_best_purchase_rate(
	company: str | None = None,
	supplier: str | None = None,
	item: str | None = None,
	item_code: str | None = None,
	qty: float | int | None = None,
	posting_date: str | None = None,
	currency: str | None = None,
):
	"""Return best rate for purchasing UI (best-effort, non-breaking).

	Feature flag: `global_purchase_contract_pricing` (default: False).
	"""
	if not is_feature_enabled("global_purchase_contract_pricing", default=False):
		return None
	if not company or not supplier:
		return None
	return find_best_supplier_rate(
		company=company,
		supplier=supplier,
		item=item,
		item_code=item_code,
		qty=qty or 1,
		posting_date=posting_date,
		currency=currency,
	)


@frappe.whitelist()
def is_purchase_enterprise_enabled():
	"""Small helper for client-side conditional UX."""
	return {
		"purchase_contract_pricing": cint(is_feature_enabled("global_purchase_contract_pricing", default=False)),
		"purchase_three_way_match": cint(is_feature_enabled("global_purchase_three_way_match", default=True)),
		"purchase_quotation_auto_po": cint(is_feature_enabled("global_purchase_quotation_auto_po", default=False)),
	}


@frappe.whitelist()
def get_best_quotations_for_purchase_request(purchase_request: str):
	"""Return best offers per item for a Purchase Request (best-effort).

	Returns a list of rows with: item/item_code/qty, supplier, quotation, effective_rate, rate, discount_percentage, currency.
	"""
	if not purchase_request:
		return []
	if not frappe.db.exists("Purchase Request", purchase_request):
		return []
	if not (frappe.db.exists("DocType", "Purchase Quotation") and frappe.db.exists("DocType", "Purchase Quotation Item")):
		return []

	pr = frappe.db.get_value("Purchase Request", purchase_request, ["company", "branch"], as_dict=True) or {}
	rows = frappe.db.sql(
		"""
		SELECT
			pq.name AS quotation,
			pq.company,
			pq.branch,
			pq.supplier,
			pq.currency,
			pqi.item,
			pqi.item_code,
			pqi.qty,
			pqi.rate,
			pqi.discount_percentage,
			(pqi.rate * (1 - (IFNULL(pqi.discount_percentage,0) / 100))) AS effective_rate
		FROM `tabPurchase Quotation` pq
		INNER JOIN `tabPurchase Quotation Item` pqi
			ON pqi.parent = pq.name AND pqi.parenttype='Purchase Quotation'
		WHERE pq.docstatus=1
		  AND pq.purchase_request=%(pr)s
		ORDER BY effective_rate ASC, pq.modified DESC
		""",
		{"pr": purchase_request},
		as_dict=True,
	)
	if not rows:
		return []

	best = {}
	for r in rows:
		key = (r.get("item") or "", r.get("item_code") or "", float(r.get("qty") or 0), r.get("currency") or "")
		if key not in best:
			best[key] = r
	# normalize list
	out = []
	for r in best.values():
		out.append(
			{
				"purchase_request": purchase_request,
				"company": r.get("company") or pr.get("company"),
				"branch": r.get("branch") or pr.get("branch"),
				"quotation": r.get("quotation"),
				"supplier": r.get("supplier"),
				"currency": r.get("currency"),
				"item": r.get("item"),
				"item_code": r.get("item_code"),
				"qty": r.get("qty"),
				"rate": r.get("rate"),
				"discount_percentage": r.get("discount_percentage"),
				"effective_rate": r.get("effective_rate"),
			}
		)
	return out


@frappe.whitelist()
def make_purchase_orders_from_best_quotations(purchase_request: str):
	"""Create Purchase Orders grouped by supplier from best quotations (feature-flagged).

	Feature flag: `global_purchase_quotation_auto_po` (default: False).
	"""
	if not is_feature_enabled("global_purchase_quotation_auto_po", default=False):
		return {"created": [], "skipped": "Feature flag disabled"}
	best_rows = get_best_quotations_for_purchase_request(purchase_request)
	if not best_rows:
		return {"created": [], "skipped": "No submitted quotations found"}

	# Group by supplier and create PO per supplier.
	by_supplier = {}
	for r in best_rows:
		sup = r.get("supplier")
		if not sup:
			continue
		by_supplier.setdefault(sup, []).append(r)

	created = []
	for supplier, items in by_supplier.items():
		po = frappe.new_doc("Purchase Order")
		po.company = items[0].get("company")
		if po.meta.has_field("branch"):
			po.branch = items[0].get("branch")
		po.supplier = supplier
		if po.meta.has_field("purchase_request"):
			po.purchase_request = purchase_request
		if po.meta.has_field("currency"):
			po.currency = items[0].get("currency")

		for it in items:
			row = {
				"item": it.get("item"),
				"item_code": it.get("item_code"),
				"qty": it.get("qty") or 1,
				"rate": it.get("rate") or it.get("effective_rate") or 0,
			}
			po.append("items", row)
		po.insert(ignore_permissions=True)
		created.append(po.name)

	return {"created": created}

