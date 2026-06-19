# Copyright (c) 2026, ErpGenEx
import unittest


class TestFinanceGroupBenchmark(unittest.TestCase):
	def test_group_number_one(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_benchmark import get_finance_group_global_score

		score = get_finance_group_global_score()
		self.assertTrue(score["beats_world_leader"])
		self.assertGreaterEqual(score["weighted_score"], 5.0)
