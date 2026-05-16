# Copyright (c) 2026, Omnexa
# License: MIT

"""E2E integration paths (GAP-QA-01 .. GAP-QA-04)."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, flt, today

from omnexa_core.tests.erpgenex_e2e_fixtures import (
	ensure_customer,
	ensure_item,
	require_branch,
	require_company,
)


class TestERPGenexE2EVerticals(FrappeTestCase):
	def setUp(self):
		self.company = require_company()
		self.branch = require_branch(self.company)
		self._tag = frappe.generate_hash(length=6)

	def test_qa01_pmc_rental_lifecycle(self):
		"""Property → unit → lease → billing run → owner statement."""
		tag = self._tag
		prop = frappe.get_doc(
			{
				"doctype": "PMC Property",
				"company": self.company,
				"property_name": f"E2E Tower {tag}",
				"ownership_model": "Owned",
			}
		).insert(ignore_permissions=True)

		unit = frappe.get_doc(
			{
				"doctype": "PMC Property Unit",
				"company": self.company,
				"pmc_property": prop.name,
				"unit_label": f"U-{tag}",
				"is_leasable": 1,
			}
		).insert(ignore_permissions=True)

		owner = ensure_customer(f"Owner-{tag}", self.company)
		agreement = frappe.get_doc(
			{
				"doctype": "PMC Management Agreement",
				"company": self.company,
				"pmc_property": prop.name,
				"owner_party": owner,
				"agreement_title": f"Mgmt {tag}",
				"management_fee_percent": 8,
				"effective_from": today(),
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		tenant = ensure_customer(f"Tenant-{tag}", self.company)
		lease = frappe.get_doc(
			{
				"doctype": "Rental Contract",
				"company": self.company,
				"pmc_property_unit": unit.name,
				"tenant_customer": tenant,
				"tenant_name": tenant,
				"start_date": today(),
				"monthly_rent": 12000,
				"status": "Active",
				"document_checklist": [
					{"item_label": "Signed lease PDF", "is_mandatory": 1, "is_complete": 1}
				],
			}
		).insert(ignore_permissions=True)

		billing = frappe.get_doc(
			{
				"doctype": "Rent Billing Run",
				"company": self.company,
				"billing_period_start": today(),
				"billing_period_end": add_days(today(), 30),
				"status": "Posted",
				"items": [{"rental_contract": lease.name, "rent_amount": 12000}],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(flt(billing.grand_total), 12000)

		stmt = frappe.get_doc(
			{
				"doctype": "PMC Owner Statement",
				"company": self.company,
				"management_agreement": agreement.name,
				"period_from": today(),
				"period_to": add_days(today(), 30),
				"total_collections": 12000,
				"total_remittance": 11040,
				"total_fees": 960,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(stmt.name)

	def test_qa02_sales_pipeline_to_invoice(self):
		"""Lead → reservation → registered booking → inventory Sold → SI link."""
		tag = self._tag
		ensure_item(self.company)
		project = frappe.get_doc(
			{
				"doctype": "Development Project",
				"company": self.company,
				"branch": self.branch,
				"project_name": f"E2E Proj {tag}",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		unit = frappe.get_doc(
			{
				"doctype": "RE Unit Inventory",
				"company": self.company,
				"development_project": project.name,
				"unit_number": f"N-{tag}",
				"status": "Available",
			}
		).insert(ignore_permissions=True)

		customer = ensure_customer(f"Buyer-{tag}", self.company)
		lead = frappe.get_doc(
			{
				"doctype": "Property Sales Lead",
				"company": self.company,
				"lead_name": f"Lead {tag}",
				"status": "Qualified",
				"development_project": project.name,
				"customer": customer,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(lead.name)

		res = frappe.get_doc(
			{
				"doctype": "Unit Reservation",
				"company": self.company,
				"re_unit_inventory": unit.name,
				"customer": customer,
				"status": "Active",
				"reservation_until": add_days(today(), 14),
			}
		).insert(ignore_permissions=True)

		booking = frappe.get_doc(
			{
				"doctype": "Sales Booking",
				"company": self.company,
				"re_unit_inventory": unit.name,
				"unit_reservation": res.name,
				"customer": customer,
				"agreement_value": 500000,
				"status": "Registered",
				"signature_status": "Signed",
			}
		).insert(ignore_permissions=True)

		self.assertEqual(frappe.db.get_value("RE Unit Inventory", unit.name, "status"), "Sold")
		booking.reload()
		if frappe.db.exists("DocType", "Sales Invoice") and booking.sales_invoice:
			self.assertTrue(frappe.db.exists("Sales Invoice", booking.sales_invoice))

	def test_qa03_development_budget_and_handover(self):
		"""BOQ → budget → handover with closed snag."""
		tag = self._tag
		project = frappe.get_doc(
			{
				"doctype": "Development Project",
				"company": self.company,
				"project_name": f"E2E Dev {tag}",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		boq = frappe.get_doc(
			{
				"doctype": "RE BOQ",
				"company": self.company,
				"development_project": project.name,
				"title": f"BOQ {tag}",
			}
		).insert(ignore_permissions=True)

		budget = frappe.get_doc(
			{
				"doctype": "Development Budget",
				"company": self.company,
				"development_project": project.name,
				"reference_boq": boq.name,
				"status": "Approved",
				"budget_lines": [
					{"cost_code": "CIVIL", "budget_amount": 100000, "actual_amount": 45000},
					{"cost_code": "MEP", "budget_amount": 50000, "actual_amount": 20000},
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(flt(budget.total_budget), 150000)

		unit = frappe.get_doc(
			{
				"doctype": "RE Unit Inventory",
				"company": self.company,
				"development_project": project.name,
				"unit_number": f"H-{tag}",
				"status": "Sold",
			}
		).insert(ignore_permissions=True)

		handover = frappe.get_doc(
			{
				"doctype": "RE Handover Package",
				"company": self.company,
				"re_unit_inventory": unit.name,
				"status": "Signed Off",
				"snag_items": [
					{"description": "Paint touch-up", "severity": "Critical", "status": "Closed"}
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(
			frappe.db.get_value("RE Unit Inventory", unit.name, "status"),
			"Handed Over",
		)
		self.assertTrue(handover.name)

	def test_qa04_maintenance_csr_to_work_order(self):
		"""PMC unit → CSR → Core WO."""
		tag = self._tag
		prop = frappe.get_doc(
			{
				"doctype": "PMC Property",
				"company": self.company,
				"property_name": f"E2E Mnt {tag}",
			}
		).insert(ignore_permissions=True)
		unit = frappe.get_doc(
			{
				"doctype": "PMC Property Unit",
				"company": self.company,
				"pmc_property": prop.name,
				"unit_label": f"M-{tag}",
			}
		).insert(ignore_permissions=True)

		from erpgenex_property_mgmt.api import create_core_service_request_for_pmc_unit

		csr_name = create_core_service_request_for_pmc_unit(
			pmc_property_unit=unit.name,
			company=self.company,
			description=f"HVAC issue {tag}",
			priority="High",
		)
		csr = frappe.get_doc("Core Service Request", csr_name)
		self.assertEqual(csr.pmc_property_unit, unit.name)

		from erpgenex_maintenance_core.api import make_core_work_order

		wo_name = make_core_work_order(csr_name)
		wo = frappe.get_doc("Core Work Order", wo_name)
		self.assertEqual(wo.service_request, csr_name)
		self.assertEqual(wo.pmc_property_unit, unit.name)

	def test_qa05_maturity_meets_ninety_percent_target(self):
		from omnexa_core.erpgenex_vertical_audit import MATURITY_TARGET_PERCENT, audit_erpgenex_verticals

		data = audit_erpgenex_verticals()
		self.assertTrue(data.get("maturity_target_met"))
		for key, score in data["maturity_scores_percent"].items():
			self.assertGreaterEqual(
				score,
				MATURITY_TARGET_PERCENT,
				msg=f"{key} maturity {score}% below {MATURITY_TARGET_PERCENT}%",
			)
