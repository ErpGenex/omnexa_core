# Copyright (c) 2026, ErpGenex and contributors
# License: MIT

"""Seed Product Type master rows for Retail POS category tabs."""

from __future__ import annotations

import frappe

DEFAULT_ROWS = (
	("Traditional Product", "منتجات", 1, 10),
	("Service", "خدمات", 1, 20),
	("Consumable", "مستهلكات", 1, 30),
	("Kit", "باندل", 1, 40),
	("Raw Material", "خامات", 0, 50),
)


def execute():
	if not frappe.db.exists("DocType", "Product Type"):
		return
	for product_type_name, pos_label, show_in_pos, sort_order in DEFAULT_ROWS:
		if frappe.db.exists("Product Type", product_type_name):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Product Type",
				"product_type_name": product_type_name,
				"pos_label": pos_label,
				"show_in_pos": show_in_pos,
				"sort_order": sort_order,
			}
		)
		doc.insert(ignore_permissions=True)
