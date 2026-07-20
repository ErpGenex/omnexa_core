import json

from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core import ops_weekly_health


class TestOpsWeeklyHealth(FrappeTestCase):
	def test_collect_ops_health_shape(self):
		data = ops_weekly_health.collect_ops_health()
		self.assertIsInstance(data, dict)
		self.assertIn("errors_error_log_24h", data)
		self.assertIn("errors_error_log_7d", data)
		self.assertIn("top_error_methods", data)
		self.assertIsInstance(data["top_error_methods"], list)
		self.assertIn("scheduler", data)
		self.assertIn("queues", data)
		line = json.dumps(data, default=str)
		self.assertTrue(line)
