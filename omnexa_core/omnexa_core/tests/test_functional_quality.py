# Copyright (c) 2026, Omnexa
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.functional_quality import functional_gates
from omnexa_core.omnexa_core.world_class import certify_app


class TestFunctionalQuality(FrappeTestCase):
	def test_structural_gates_for_core(self):
		cert = certify_app("omnexa_core")
		for key in (
			"session_audit_script",
			"session_scope_test",
			"vertical_dashboard",
			"session_context_live",
		):
			self.assertTrue(cert["gates"][key], key)

	def test_functional_meta_shape(self):
		meta = functional_gates("omnexa_core")
		self.assertIn("full_test_suite", meta)
		self.assertIn("no_open_p0_gaps", meta)
