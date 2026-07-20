from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt


def _contains_stock_items(doc) -> bool:
	# Mirror logic in compliance_guard but keep module independent.
	for row in doc.get("items") or []:
		item = row.get("item")
		if not item:
			continue
		try:
			if frappe.db.get_value("Item", item, "is_stock_item"):
				return True
		except Exception:
			continue
	return False


def validate_purchase_invoice_three_way_match(doc, *, allow_services_without_grn: bool = True, tolerance_ratio: float = 0.01):
	"""Best-effort three-way match (PO + GRN + Invoice) without breaking legacy flows.

	- If invoice references a PO, validate that PO is submitted and supplier/company match.
	- If invoice has stock items, require GRN reference (unless allow_services_without_grn=False).
	- If GRN reference exists, validate it is submitted and matches PO (when both present).
	- Validate gross amount does not exceed received amount by tolerance when PO+GRN are present.
	"""
	if not getattr(doc, "doctype", None) or doc.doctype != "Purchase Invoice":
		return
	if cint(doc.get("is_return")):
		return

	po = (doc.get("po_reference") or "").strip() if doc.meta.has_field("po_reference") else ""
	grn = (doc.get("goods_receipt_reference") or "").strip() if doc.meta.has_field("goods_receipt_reference") else ""

	if not po and not grn:
		return

	company = doc.get("company")
	supplier = doc.get("supplier")

	po_row = None
	if po:
		po_row = frappe.db.get_value(
			"Purchase Order",
			po,
			["name", "company", "supplier", "docstatus", "grand_total"],
			as_dict=True,
		)
		if not po_row or po_row.docstatus != 1:
			frappe.throw(_("3-way match: Purchase Order must be submitted."), title=_("Compliance"))
		if company and po_row.company and company != po_row.company:
			frappe.throw(_("3-way match: PO must belong to the same company."), title=_("Compliance"))
		if supplier and po_row.supplier and supplier != po_row.supplier:
			frappe.throw(_("3-way match: Supplier must match the referenced PO."), title=_("Compliance"))

	# IAS 2 / cutoff posture: stock invoices should be backed by receipt.
	if _contains_stock_items(doc):
		if not grn and not allow_services_without_grn:
			frappe.throw(_("3-way match: Stock Purchase Invoice requires Goods Receipt reference."), title=_("Compliance"))
		if not grn:
			# Default enterprise policy: stock invoice should reference GRN; keep as strict but not absolute by flag.
			frappe.throw(_("3-way match: Stock Purchase Invoice requires Goods Receipt reference."), title=_("Compliance"))

	grn_row = None
	if grn:
		grn_row = frappe.db.get_value(
			"Purchase Receipt",
			grn,
			["name", "company", "supplier", "purchase_order", "docstatus", "grand_total"],
			as_dict=True,
		)
		if not grn_row or grn_row.docstatus != 1:
			frappe.throw(_("3-way match: Goods Receipt must be submitted."), title=_("Compliance"))
		if company and grn_row.company and company != grn_row.company:
			frappe.throw(_("3-way match: GRN must belong to the same company."), title=_("Compliance"))
		if supplier and grn_row.supplier and supplier != grn_row.supplier:
			frappe.throw(_("3-way match: Supplier must match the referenced GRN."), title=_("Compliance"))
		if po and grn_row.purchase_order and grn_row.purchase_order != po:
			frappe.throw(_("3-way match: GRN must reference the same PO."), title=_("Compliance"))

	# Amount sanity when both PO + GRN exist (prevent invoicing significantly above receipt).
	if po_row and grn_row:
		inv_total = flt(doc.get("grand_total"))
		grn_total = flt(grn_row.grand_total)
		allowed = grn_total * (1.0 + max(0.0, flt(tolerance_ratio)))
		if inv_total > allowed + 0.0001:
			frappe.throw(
				_(
					"3-way match: Invoice total cannot exceed received amount beyond tolerance. "
					"Received={0}, Invoice={1}"
				).format(grn_total, inv_total),
				title=_("Compliance"),
			)

