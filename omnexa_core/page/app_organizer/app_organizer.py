# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _


def get_context(context):
	"""Context for App Organizer page"""
	context.no_cache = 1
	context.categories = frappe.get_all(
		"Business Category",
		fields=["name", "label", "order", "purpose"],
		order_by="order asc",
	)
	return context
