# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestEDocumentSubmission(FrappeTestCase):
	def test_duplicate_authority_uuid_rejected(self):
		uuid = "eta-uuid-test-0001"
		d1 = frappe.new_doc("E-Document Submission")
		d1.reference_doctype = "User"
		d1.reference_name = "Administrator"
		d1.payload_hash = "hash-a"
		d1.authority_status = "Draft"
		d1.authority_uuid = uuid
		d1.insert(ignore_permissions=True)

		d2 = frappe.new_doc("E-Document Submission")
		d2.reference_doctype = "User"
		d2.reference_name = "Administrator"
		d2.payload_hash = "hash-b"
		d2.authority_status = "Draft"
		d2.authority_uuid = uuid
		with self.assertRaises(frappe.ValidationError):
			d2.insert(ignore_permissions=True)
