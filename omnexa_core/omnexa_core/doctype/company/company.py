# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Company(Document):
	def validate(self):
		self._validate_production_demo_branch()
		self._validate_fiscal_year_start_month()

	def before_insert(self):
		self._prevent_circular_parent()

	def before_save(self):
		self._prevent_circular_parent()

	def after_insert(self):
		self._ensure_head_office_branch()

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

	def _validate_fiscal_year_start_month(self):
		if not self.get("fiscal_year_start_month"):
			return
		try:
			m = int(self.fiscal_year_start_month)
		except Exception:
			frappe.throw(_("Fiscal year start month must be between 1 and 12."), title=_("Validation"))
		if m < 1 or m > 12:
			frappe.throw(_("Fiscal year start month must be between 1 and 12."), title=_("Validation"))

	def _validate_production_demo_branch(self):
		if not getattr(self, "production_demo_branch", None):
			return
		b_company = frappe.db.get_value("Branch", self.production_demo_branch, "company")
		if not b_company:
			frappe.throw(_("Branch does not exist."), title=_("Validation"))
		if b_company != self.name:
			frappe.throw(_("Demo / reset branch must belong to this company."), title=_("Validation"))

	def _ensure_head_office_branch(self):
		if not self.enable_branches:
			return
		if frappe.db.exists("Branch", {"company": self.name, "is_head_office": 1}):
			return
		branch = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": self.name,
				"branch_name": f"{self.abbr} Head Office",
				"branch_code": "HO",
				"status": "Active",
				"is_head_office": 1,
			}
		)
		branch.insert(ignore_permissions=True)
