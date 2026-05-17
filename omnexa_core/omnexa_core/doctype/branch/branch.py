# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Branch(Document):
	def validate(self):
		self.branch_code = (self.branch_code or "").strip().upper()
		self.branch_name = (self.branch_name or "").strip()
		self._validate_default_vat_rate()
		self._validate_unique_code_per_company()
		self._validate_parent_branch_company()
		self._validate_single_head_office()

	def _validate_default_vat_rate(self):
		if not getattr(self, "default_vat_rate", None):
			return
		try:
			rate = float(self.default_vat_rate)
		except Exception:
			frappe.throw(_("Default VAT Rate must be a number."), title=_("Validation"))
		if rate < 0 or rate > 100:
			frappe.throw(_("Default VAT Rate must be between 0 and 100."), title=_("Validation"))

	def _validate_unique_code_per_company(self):
		if not self.company or not self.branch_code:
			return
		dupe = frappe.db.exists(
			"Branch",
			{
				"company": self.company,
				"branch_code": self.branch_code,
			},
		)
		if dupe and (self.is_new() or dupe != self.name):
			frappe.throw(
				_("Branch Code must be unique within the same company."),
				title=_("Validation"),
			)

	def _validate_parent_branch_company(self):
		if not self.parent_branch:
			return
		if self.parent_branch == self.name:
			frappe.throw(_("Parent Branch cannot be the same as branch."), title=_("Validation"))
		parent_company = frappe.db.get_value("Branch", self.parent_branch, "company")
		if parent_company and parent_company != self.company:
			frappe.throw(
				_("Parent Branch must belong to the same company."),
				title=_("Validation"),
			)

	def _validate_single_head_office(self):
		if not self.is_head_office:
			return
		dupe = frappe.db.exists(
			"Branch",
			{
				"company": self.company,
				"is_head_office": 1,
				"name": ("!=", self.name),
			},
		)
		if dupe:
			frappe.throw(_("Only one head office branch is allowed per company."), title=_("Validation"))
