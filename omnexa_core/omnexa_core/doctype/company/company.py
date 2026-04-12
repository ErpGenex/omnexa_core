# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Company(Document):
	def validate(self):
		if self.eta_einvoice_enabled and not (self.rin or "").strip():
			frappe.throw(_("RIN is required when ETA e-Invoice is enabled."), title=_("Validation"))

	def before_insert(self):
		self._prevent_circular_parent()

	def before_save(self):
		self._prevent_circular_parent()

	def _prevent_circular_parent(self):
		if not self.parent_company:
			return
		if self.parent_company == self.name:
			frappe.throw(_("Parent Company cannot be the same as the company."), title=_("Validation"))
		walk = self.parent_company
		depth = 0
		while walk and depth < 32:
			if walk == self.name:
				frappe.throw(_("Circular parent company chain is not allowed."), title=_("Validation"))
			walk = frappe.db.get_value("Company", walk, "parent_company")
			depth += 1
