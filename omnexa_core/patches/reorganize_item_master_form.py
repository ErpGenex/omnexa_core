# Copyright (c) 2026, ErpGenex and contributors
# License: MIT

"""Reorganize Item master custom fields into tabbed sections."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	_reorganize_item_custom_fields()
	frappe.clear_cache(doctype="Item")


def _reorganize_item_custom_fields():
	for old in ("inventory_enterprise_section", "attachments_section"):
		name = frappe.db.get_value("Custom Field", {"dt": "Item", "fieldname": old})
		if name:
			frappe.delete_doc("Custom Field", name, force=1, ignore_permissions=True)

	fields = {
		"Item": [
			{"fieldname": "item_name_ar", "label": "Item Name (Arabic)", "fieldtype": "Data", "insert_after": "item_name"},
			{"fieldname": "barcode", "label": "Barcode", "fieldtype": "Data", "insert_after": "item_name_ar"},
			{"fieldname": "item_description", "label": "Description", "fieldtype": "Small Text", "insert_after": "barcode"},
			{"fieldname": "standard_selling_rate", "label": "Standard Selling Rate", "fieldtype": "Currency", "insert_after": "is_sales_item"},
			{"fieldname": "default_sales_account", "label": "Default Sales Account", "fieldtype": "Link", "options": "GL Account", "insert_after": "standard_selling_rate"},
			{"fieldname": "standard_purchase_rate", "label": "Standard Purchase Rate", "fieldtype": "Currency", "insert_after": "is_purchase_item"},
			{"fieldname": "default_purchase_account", "label": "Default Purchase Account", "fieldtype": "Link", "options": "GL Account", "insert_after": "standard_purchase_rate"},
			{"fieldname": "default_warehouse", "label": "Default Warehouse", "fieldtype": "Link", "options": "Warehouse", "insert_after": "current_stock_qty"},
			{"fieldname": "reorder_level", "label": "Reorder Level", "fieldtype": "Float", "default": "0", "insert_after": "default_warehouse"},
			{"fieldname": "safety_stock", "label": "Safety Stock", "fieldtype": "Float", "default": "0", "insert_after": "reorder_level"},
			{
				"fieldname": "valuation_method",
				"label": "Valuation Method",
				"fieldtype": "Select",
				"options": "FIFO\nWeighted Average",
				"default": "FIFO",
				"insert_after": "safety_stock",
			},
			{"fieldname": "has_serial_no", "label": "Track Serial Numbers", "fieldtype": "Check", "default": "0", "insert_after": "has_batch_no"},
			{"fieldname": "tab_break_accounts", "label": "Accounts & Costing", "fieldtype": "Tab Break", "insert_after": "requires_dynamic_composition"},
			{"fieldname": "default_expense_account", "label": "Default Expense Account", "fieldtype": "Link", "options": "GL Account", "insert_after": "tab_break_accounts"},
			{"fieldname": "item_cost_center", "label": "Cost Center", "fieldtype": "Link", "options": "Cost Center", "insert_after": "default_expense_account"},
			{"fieldname": "tab_break_attachments", "label": "Attachments", "fieldtype": "Tab Break", "insert_after": "item_cost_center"},
			{"fieldname": "qr_code", "label": "QR Code", "fieldtype": "Data", "insert_after": "tab_break_attachments"},
			{"fieldname": "supporting_attachment", "label": "Supporting Attachment", "fieldtype": "Attach", "insert_after": "qr_code"},
		]
	}
	create_custom_fields(fields, update=True)
	frappe.db.commit()
