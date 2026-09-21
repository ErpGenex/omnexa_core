# Copyright (c) 2026, ErpGenEx
"""Regression: portal icons must be distinct per healthcare menu item."""

from __future__ import annotations

import unittest

from omnexa_core.vertical_workcenter.portal_icon_resolver import resolve_portal_icon_meta


class TestPortalIconDistinctness(unittest.TestCase):
	def test_healthcare_workcenter_pages_not_all_heart(self):
		pages = [
			("healthcare-lab-workbench", "Lab Workbench"),
			("healthcare-pharmacy-desk", "Pharmacy Desk"),
			("healthcare-radiology-worklist", "Radiology Worklist"),
			("healthcare-er-board", "ER Board"),
			("healthcare-bed-map", "Visual Bed Map"),
			("healthcare-dental-chart", "Interactive Dental Chart"),
			("healthcare-patient-queue", "Patient Queue"),
			("healthcare-appointment-calendar", "Appointment Calendar"),
			("healthcare-nursing-portal", "Nursing Portal"),
			("healthcare-physician-workbench", "Physician Workbench"),
			("healthcare-telehealth-room", "Telehealth Video Room"),
			("healthcare-dicom-viewer", "DICOM Viewer"),
		]
		metas = [resolve_portal_icon_meta("omnexa_healthcare", "Page", p, lbl) for p, lbl in pages]
		svgs = [m["icon_svg"] for m in metas]
		# Must not collapse to a single icon
		self.assertGreaterEqual(len(set(svgs)), 8, svgs)
		# Lab / pharmacy / radiology must differ from each other
		by_page = {p: m["icon_svg"] for (p, _), m in zip(pages, metas)}
		self.assertNotEqual(by_page["healthcare-lab-workbench"], by_page["healthcare-pharmacy-desk"])
		self.assertNotEqual(by_page["healthcare-lab-workbench"], by_page["healthcare-radiology-worklist"])
		self.assertNotEqual(by_page["healthcare-er-board"], by_page["healthcare-appointment-calendar"])

	def test_healthcare_prefix_does_not_force_heart(self):
		meta = resolve_portal_icon_meta("omnexa_healthcare", "Page", "healthcare-lab-workbench", "Lab")
		self.assertNotEqual(meta["icon_svg"], "es-line-heart")

	def test_healthcare_does_not_match_car_vehicle_icon(self):
		"""Regression: substring 'car' inside 'healthcare' must not map to vehicle/move."""
		meta = resolve_portal_icon_meta(
			"omnexa_healthcare", "DocType", "Healthcare Facility Profile", "Facility Profile"
		)
		self.assertNotEqual(meta["icon_svg"], "es-line-move")

	def test_organization_setup_icons_are_distinct(self):
		items = [
			("Healthcare Facility Profile", "Facility Profile"),
			("Healthcare Department", "Department"),
			("Healthcare Specialty", "Specialty"),
			("Healthcare Icd10 Code", "ICD-10 Codes"),
			("Healthcare Icd11 Code", "ICD-11 Codes"),
			("Healthcare Cpt Code", "CPT Codes"),
			("Healthcare Home Visit Request", "Home Visits"),
			("Healthcare Disaster Recovery Plan", "DR Runbooks"),
			("Healthcare Sso Provider", "SSO Providers"),
			("Healthcare Pacs Endpoint", "PACS Endpoints"),
			("Healthcare Remote Monitoring Reading", "RPM Readings"),
			("Healthcare Medical Tourism Case", "Medical Tourism"),
		]
		metas = [
			resolve_portal_icon_meta("omnexa_healthcare", "DocType", link_to, label)
			for link_to, label in items
		]
		svgs = [m["icon_svg"] for m in metas]
		self.assertGreaterEqual(len(set(svgs)), 9, svgs)
		self.assertNotIn("es-line-move", svgs)


if __name__ == "__main__":
	unittest.main()
