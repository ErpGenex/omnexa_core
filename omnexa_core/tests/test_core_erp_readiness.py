from frappe.tests.utils import FrappeTestCase

from omnexa_core.core_erp_readiness import get_core_erp_readiness_snapshot


class TestCoreERPReadiness(FrappeTestCase):
	def test_snapshot_shape(self):
		out = get_core_erp_readiness_snapshot()
		self.assertIn("summary", out)
		self.assertIn("process_checks", out)
		self.assertIn("must_pass_matrix", out)
		self.assertIn("readiness_score", out["summary"])
		self.assertIsInstance(out["process_checks"], list)
		self.assertIsInstance(out["must_pass_matrix"], list)

