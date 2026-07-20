# Copyright (c) 2026, ErpGenex and contributors
# License: MIT

"""Add Show in Retail POS on Item and hide demo/simulation items by default."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Item": [
				{
					"fieldname": "show_in_retail_pos",
					"label": "Show in Retail POS",
					"fieldtype": "Check",
					"default": "0",
					"insert_after": "is_sales_item",
					"description": "When enabled, this item appears in the Retail POS product grid.",
				}
			]
		},
		update=True,
	)
	_backfill_show_in_retail_pos()
	frappe.db.commit()
	frappe.clear_cache(doctype="Item")


def _backfill_show_in_retail_pos():
	if not frappe.db.has_column("Item", "show_in_retail_pos"):
		return
	frappe.db.sql(
		"""
		UPDATE `tabItem`
		SET show_in_retail_pos = 0
		WHERE IFNULL(disabled, 0) = 0
		  AND (
			item_code LIKE 'SIM-%%'
			OR item_code LIKE 'DEMO-%%'
			OR item_code LIKE 'OMNEXA-DEMO%%'
			OR item_name LIKE 'Simulation %%'
		  )
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabItem`
		SET show_in_retail_pos = 1
		WHERE IFNULL(disabled, 0) = 0
		  AND IFNULL(is_sales_item, 0) = 1
		  AND item_code NOT LIKE 'SIM-%%'
		  AND item_code NOT LIKE 'DEMO-%%'
		  AND item_code NOT LIKE 'OMNEXA-DEMO%%'
		  AND IFNULL(item_name, '') NOT LIKE 'Simulation %%'
		"""
	)
