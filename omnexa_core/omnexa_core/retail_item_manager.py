# Copyright (c) 2026, ErpGenex and contributors
# License: MIT

"""Retail POS — in-screen Item CRUD with full master data."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt

ITEM_FIELDS = [
	"name",
	"item_code",
	"item_name",
	"item_name_ar",
	"item_description",
	"product_type",
	"company",
	"stock_uom",
	"classification_code",
	"barcode",
	"disabled",
	"is_sales_item",
	"show_in_retail_pos",
	"standard_selling_rate",
	"default_sales_account",
	"is_purchase_item",
	"standard_purchase_rate",
	"default_purchase_account",
	"is_stock_item",
	"current_stock_qty",
	"default_warehouse",
	"reorder_level",
	"safety_stock",
	"valuation_method",
	"has_batch_no",
	"has_serial_no",
	"inventory_control_account",
	"manufacturing_role",
	"can_be_manufactured",
	"requires_dynamic_composition",
	"default_expense_account",
	"item_cost_center",
	"qr_code",
]


def _item_row(doc) -> dict[str, Any]:
	return {
		"name": doc.name,
		"item_code": doc.item_code,
		"item_name": doc.item_name,
		"item_name_ar": getattr(doc, "item_name_ar", None),
		"product_type": doc.product_type,
		"barcode": getattr(doc, "barcode", None),
		"standard_selling_rate": flt(getattr(doc, "standard_selling_rate", 0)),
		"is_sales_item": cint(doc.is_sales_item),
		"show_in_retail_pos": cint(getattr(doc, "show_in_retail_pos", 0)),
		"disabled": cint(doc.disabled),
		"default_warehouse": getattr(doc, "default_warehouse", None),
	}


@frappe.whitelist()
def get_retail_items_for_manager(product_type: str | None = None, search: str | None = None):
	filters: dict[str, Any] = {"disabled": 0}
	if product_type and product_type not in ("All", "الكل", "Offers"):
		type_map = {
			"Product": "Traditional Product",
			"Service": "Service",
			"Raw Material": "Raw Material",
			"Consumable": "Consumable",
			"Bundle": "Kit",
		}
		pt = type_map.get(product_type) or product_type
		if pt in type_map.values() or pt in type_map:
			filters["product_type"] = pt
	rows = frappe.get_all(
		"Item",
		filters=filters,
		fields=["name", "item_code", "item_name", "item_name_ar", "product_type", "barcode", "standard_selling_rate", "is_sales_item", "disabled", "default_warehouse"],
		order_by="item_name asc",
		limit_page_length=500,
	)
	if search:
		term = search.strip().lower()
		rows = [
			r
			for r in rows
			if term in (r.item_name or "").lower()
			or term in (r.item_code or "").lower()
			or term in (r.get("barcode") or "").lower()
		]
	return rows


@frappe.whitelist()
def get_retail_item_detail(name: str):
	if not frappe.db.exists("Item", name):
		frappe.throw(_("Item not found."))
	doc = frappe.get_doc("Item", name)
	out = {f: getattr(doc, f, None) for f in ITEM_FIELDS if hasattr(doc, f) or f in ITEM_FIELDS}
	out["name"] = doc.name
	return out


@frappe.whitelist()
def save_retail_item(data: str | dict):
	payload = frappe.parse_json(data) if isinstance(data, str) else data
	if not payload:
		frappe.throw(_("No data provided."))
	name = payload.get("name")
	if name and frappe.db.exists("Item", name):
		doc = frappe.get_doc("Item", name)
	else:
		doc = frappe.new_doc("Item")
	for field in ITEM_FIELDS:
		if field == "name":
			continue
		if field in payload:
			doc.set(field, payload[field])
	if not doc.company:
		from omnexa_core.omnexa_core.retail_pos_invoicing import resolve_retail_pos_company_branch

		doc.company, _branch = resolve_retail_pos_company_branch()
	if not doc.stock_uom:
		doc.stock_uom = frappe.db.get_single_value("Stock Settings", "default_uom") or "Nos"
	if hasattr(doc, "show_in_retail_pos") and cint(doc.is_sales_item) and "show_in_retail_pos" not in payload:
		doc.show_in_retail_pos = 1
	doc.flags.ignore_permissions = True
	if doc.name:
		doc.save()
	else:
		doc.insert()
	return get_retail_item_detail(doc.name)


@frappe.whitelist()
def toggle_retail_item_active(name: str, disabled: int = 0):
	doc = frappe.get_doc("Item", name)
	doc.disabled = cint(disabled)
	doc.flags.ignore_permissions = True
	doc.save()
	return {"name": doc.name, "disabled": doc.disabled}
