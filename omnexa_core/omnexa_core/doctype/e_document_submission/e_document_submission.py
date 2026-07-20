# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EDocumentSubmission(Document):
	def validate(self):
		uuid = (self.authority_uuid or "").strip()
		if not uuid:
			return
		duplicate = frappe.db.get_value(
			"E-Document Submission",
			filters={"authority_uuid": uuid, "name": ("!=", self.name)},
			fieldname="name",
		)
		if duplicate:
			frappe.throw(
				_("Authority UUID {0} is already linked to {1}").format(uuid, duplicate),
				title=_("Duplicate UUID"),
			)

	def before_cancel(self):
		frappe.throw(_("E-Document Submission records cannot be cancelled."), title=_("Not Allowed"))
