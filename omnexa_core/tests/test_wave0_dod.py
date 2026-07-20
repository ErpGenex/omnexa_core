# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Wave 0 Definition-of-Done smoke — omnexa_core."""

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.omnexa_mfa_gate import get_mfa_compliance_status
from omnexa_core.tests.test_helpers import clear_privileged_view_context


class TestWave0DoDCore(FrappeTestCase):
	def setUp(self):
		super().setUp()
		clear_privileged_view_context()

	def test_marketplace_module_importable(self):
		from omnexa_core.omnexa_core import marketplace

		self.assertTrue(callable(getattr(marketplace, "get_marketplace_catalog", None)))

	def test_mfa_gate_status_for_admin(self):
		frappe.set_user("Administrator")
		out = get_mfa_compliance_status()
		self.assertIn("required_roles", out)

	def test_license_gate_module_present(self):
		from omnexa_core.omnexa_core.license_gate import before_request

		self.assertTrue(callable(before_request))

	def test_platform_health_api(self):
		from omnexa_core.omnexa_core.platform_health_api import get_platform_health

		out = get_platform_health()
		self.assertTrue(out.get("ok"))
