# Copyright (c) 2026, Omnexa
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.world_class import certify_app


class TestFunctionalWorldClassGate(FrappeTestCase):
	"""Run after WAVE7_TEST_SWEEP.json is fresh — validates 6-gate functional 100."""

	def test_core_functional_world_class(self):
		cert = certify_app("omnexa_core")
		self.assertTrue(cert["gates"]["full_test_suite"], cert.get("functional"))
		self.assertTrue(cert["gates"]["no_open_p0_gaps"], cert.get("functional"))
		self.assertTrue(cert["world_class_gate"], cert)
