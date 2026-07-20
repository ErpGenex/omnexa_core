# Copyright (c) 2026, ErpGenEx
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.vertical_parity import VERTICALS, preview_for_vertical


class TestSapParityVertical(FrappeTestCase):
	def test_all_wave_c_verticals_registered(self):
		self.assertGreaterEqual(len(VERTICALS), 14)

	def test_hr_net_pay(self):
		out = preview_for_vertical("hr", gross_pay=10000, deductions=1500)
		self.assertEqual(out["kpi"]["net_pay"], 8500)

	def test_manufacturing_wo_cost(self):
		out = preview_for_vertical("manufacturing", labor_cost=100, material_cost=200, overhead=50)
		self.assertEqual(out["kpi"]["work_order_cost"], 350)

	def test_tourism_occupancy(self):
		out = preview_for_vertical("tourism", rooms_available=100, rooms_occupied=75, average_daily_rate=200)
		self.assertEqual(out["kpi"]["occupancy_rate"], 0.75)

	def test_projects_pm_evm(self):
		out = preview_for_vertical("projects_pm", planned_value=100, earned_value=90, actual_cost=95)
		self.assertAlmostEqual(out["kpi"]["cpi"], 0.9474, places=3)
