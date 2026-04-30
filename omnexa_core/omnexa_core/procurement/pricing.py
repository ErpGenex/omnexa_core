from __future__ import annotations

import frappe
from frappe.utils import getdate, flt


def find_best_supplier_rate(
	*,
	company: str,
	supplier: str,
	item: str | None = None,
	item_code: str | None = None,
	qty: float | int = 1,
	posting_date=None,
	currency: str | None = None,
) -> dict | None:
	"""Return best contract rate for supplier/item (best-effort).

	Data source:
	- `Supplier Contract` + `Supplier Contract Item` (omnexa_accounting)

	Returns:
	- dict with keys: rate, discount_percentage, currency, contract, contract_item
	"""
	if not company or not supplier:
		return None

	dt_ok = frappe.db.exists("DocType", "Supplier Contract") and frappe.db.exists("DocType", "Supplier Contract Item")
	if not dt_ok:
		return None

	qty = flt(qty or 1)
	qty = max(0.0, qty)
	pd = getdate(posting_date) if posting_date else getdate()

	filters = {
		"company": company,
		"supplier": supplier,
		"is_active": 1,
		"docstatus": 1,
	}
	if currency:
		filters["currency"] = currency

	# Parent contract filters done via join. We keep item matching on child.
	item_filters = []
	if item:
		item_filters.append(("sci.item", "=", item))
	if item_code:
		item_filters.append(("sci.item_code", "=", item_code))
	if not item_filters:
		return None

	# Pick lowest effective rate among valid contracts.
	rows = frappe.db.sql(
		"""
		SELECT
			sc.name AS contract,
			sc.currency AS currency,
			sc.valid_from,
			sc.valid_to,
			sci.name AS contract_item,
			sci.item,
			sci.item_code,
			sci.min_qty,
			sci.rate,
			sci.discount_percentage
		FROM `tabSupplier Contract` sc
		INNER JOIN `tabSupplier Contract Item` sci
			ON sci.parent = sc.name AND sci.parenttype='Supplier Contract'
		WHERE sc.company=%(company)s
		  AND sc.supplier=%(supplier)s
		  AND sc.is_active=1
		  AND sc.docstatus=1
		  AND (sc.valid_from IS NULL OR sc.valid_from='' OR sc.valid_from <= %(pd)s)
		  AND (sc.valid_to IS NULL OR sc.valid_to='' OR sc.valid_to >= %(pd)s)
		  AND (sci.min_qty IS NULL OR sci.min_qty=0 OR sci.min_qty <= %(qty)s)
		  AND ( (sci.item IS NOT NULL AND sci.item!='' AND ({item_where}))
		        OR (sci.item_code IS NOT NULL AND sci.item_code!='' AND ({code_where})) )
		  {currency_clause}
		ORDER BY (sci.rate * (1 - (IFNULL(sci.discount_percentage,0)/100))) ASC
		LIMIT 25
		""".format(
			item_where=" OR ".join(["(sci.item=%(item)s)"] if item else ["0=1"]),
			code_where=" OR ".join(["(sci.item_code=%(item_code)s)"] if item_code else ["0=1"]),
			currency_clause="AND sc.currency=%(currency)s" if currency else "",
		),
		{
			"company": company,
			"supplier": supplier,
			"pd": pd,
			"qty": qty,
			"item": item,
			"item_code": item_code,
			"currency": currency,
		},
		as_dict=True,
	)
	if not rows:
		return None

	best = rows[0]
	return {
		"rate": flt(best.get("rate")),
		"discount_percentage": flt(best.get("discount_percentage")),
		"currency": best.get("currency"),
		"contract": best.get("contract"),
		"contract_item": best.get("contract_item"),
	}

