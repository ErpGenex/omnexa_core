# Copyright (c) 2026, Omnexa
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.platform_portfolio_gate import (
	get_platform_core_score,
	verify_portfolio_global_gate,
)


class TestPlatformPortfolioGate(FrappeTestCase):
	def test_portfolio_gate_passes(self):
		result = verify_portfolio_global_gate()
		self.assertGreater(result["apps_total"], 30)
		self.assertEqual(result["apps_failed"], 0)
		self.assertTrue(result["portfolio_global_gate"])

	def test_platform_core_score(self):
		score = get_platform_core_score()
		self.assertGreaterEqual(score["weighted_score"], 4.85)
		self.assertTrue(score.get("global_leader_gate"))
