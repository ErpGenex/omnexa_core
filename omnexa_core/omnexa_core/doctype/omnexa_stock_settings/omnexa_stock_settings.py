# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document


class OmnexaStockSettings(Document):
	pass


def get_stock_settings() -> dict:
	"""Safe getter for runtime checks (returns empty dict if DocType missing)."""
	try:
		if not frappe.db.exists("DocType", "Omnexa Stock Settings"):
			return {}
		return frappe.get_single("Omnexa Stock Settings").as_dict()
	except Exception:
		return {}

