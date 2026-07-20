# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class UserBranchAccess(Document):
	def validate(self):
		self._validate_branch_company()
		self._validate_unique_user_branch()

	def _validate_branch_company(self):
		branch_company = frappe.db.get_value("Branch", self.branch, "company")
		if not branch_company:
			frappe.throw(_("Selected branch does not exist."), title=_("Validation"))
		if branch_company != self.company:
			frappe.throw(_("Branch must belong to the same company."), title=_("Validation"))

	def _validate_unique_user_branch(self):
		dupe = frappe.db.exists(
			"User Branch Access",
			{"user": self.user, "company": self.company, "branch": self.branch
	},
		)
		if dupe and (self.is_new() or dupe != self.name):
			frappe.throw(_("This user already has access to the selected branch."), title=_("Validation"))
