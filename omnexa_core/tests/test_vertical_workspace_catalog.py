# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.vertical_workspace_catalog import (
	GLOBAL_MIN_LINKS,
	get_effective_workspace_sections,
	get_workspace_catalog_stats,
)
from omnexa_tourism.workspace.tour_workspace import WORKSPACE_SECTIONS as TOURISM_SECTIONS


class TestVerticalWorkspaceCatalog(FrappeTestCase):
	def test_tourism_catalog_meets_global_min(self):
		stats = get_workspace_catalog_stats("omnexa_tourism", TOURISM_SECTIONS)
		self.assertGreaterEqual(stats["links_catalogued"], GLOBAL_MIN_LINKS)
		self.assertTrue(stats["meets_global_min"])

	def test_effective_sections_dedupe_links(self):
		sections = get_effective_workspace_sections("omnexa_tourism", TOURISM_SECTIONS)
		keys: set[tuple[str, str]] = set()
		for _section, items in sections:
			for link_type, link_to, _label in items:
				key = (link_type, link_to)
				self.assertNotIn(key, keys)
				keys.add(key)

	def test_finance_engine_catalog_on_site(self):
		if "omnexa_finance_engine" not in frappe.get_installed_apps():
			self.skipTest("omnexa_finance_engine not installed")
		from omnexa_finance_engine.workspace.fe_workspace import WORKSPACE_SECTIONS

		stats = get_workspace_catalog_stats("omnexa_finance_engine", WORKSPACE_SECTIONS)
		self.assertGreaterEqual(stats["links_catalogued"], GLOBAL_MIN_LINKS)
