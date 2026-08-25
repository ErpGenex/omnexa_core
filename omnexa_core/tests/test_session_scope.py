# Copyright (c) 2026, Omnexa
from frappe.tests.utils import FrappeTestCase


class TestSessionScope(FrappeTestCase):
	def test_vertical_dashboard(self):
		from omnexa_core.vertical_dashboard_api import get_vertical_dashboard

		out = get_vertical_dashboard()
		self.assertEqual(out.get("app"), "omnexa_core")
		self.assertIn("uses_session_context", out)
