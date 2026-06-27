# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.omnexa_mfa_gate import (
	_required_roles,
	_user_requires_mfa,
	get_mfa_compliance_status,
)


class TestOmnexaMfaGate(FrappeTestCase):
	def test_required_roles_default(self):
		roles = _required_roles()
		self.assertIn("System Manager", roles)
		self.assertIn("Accounts Manager", roles)

	def test_administrator_not_required(self):
		self.assertFalse(_user_requires_mfa("Administrator"))

	def test_mfa_compliance_status(self):
		frappe.set_user("Administrator")
		out = get_mfa_compliance_status()
		self.assertTrue(out.get("ok"))
		self.assertIn("non_compliant_users", out)
		self.assertIn("required_roles", out)
