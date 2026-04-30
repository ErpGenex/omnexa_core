# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document


class OmnexaSalesSettings(Document):
	pass


def get_sales_settings() -> dict:
	"""Safe getter for runtime checks (returns empty dict if DocType missing)."""
	try:
		if not frappe.db.exists("DocType", "Omnexa Sales Settings"):
			return {}
		return frappe.get_single("Omnexa Sales Settings").as_dict()
	except Exception:
		return {}

