# Copyright (c) 2026, ErpGenEx

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class FinanceBorrowerCaseDocument(Document):
	def validate(self):
		if self.attachment and self.verification_status == "Pending Upload":
			self.verification_status = "Uploaded"
		if self.attachment and self.verification_status == "Uploaded" and not self.uploaded_on:
			self.uploaded_by = self.uploaded_by or frappe.session.user
			self.uploaded_on = self.uploaded_on or now_datetime()

	def before_save(self):
		if self.verification_status in ("E-Approved", "Paper Approved") and not self.attachment:
			frappe.throw(_("Cannot approve a document without an attachment."))
