# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.platform_health_api import get_platform_health


class TestPlatformHealthApi(FrappeTestCase):
	def test_platform_health(self):
		frappe.set_user("Administrator")
		out = get_platform_health()
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("app"), "omnexa_core")
		self.assertIn("benchmark", out)
		self.assertIn("operations", out)
