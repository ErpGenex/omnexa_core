# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document


class OmnexaAccountingSettings(Document):
	pass


def get_accounting_settings() -> dict:
	"""Safe getter for runtime checks (returns empty dict if DocType missing)."""
	try:
		if not frappe.db.exists("DocType", "Omnexa Accounting Settings"):
			return {}
		return frappe.get_single("Omnexa Accounting Settings").as_dict()
	except Exception:
		return {}

