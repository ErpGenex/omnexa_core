# Copyright (c) 2026, ErpGenEx
from pathlib import Path

from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.sap_parity_registry import APP_REGISTRY, get_app_parity_status


class TestSapParityRegistry95(FrappeTestCase):
	def test_all_bench_apps_registered_at_100(self):
		bench = Path(__file__).resolve().parents[4]
		apps = [
			a.strip()
			for a in (bench / "sites" / "apps.txt").read_text().splitlines()
			if a.strip() and a.strip() != "frappe"
		]
		missing = []
		below = []
		for app in apps:
			if app not in APP_REGISTRY:
				missing.append(app)
				continue
			status = get_app_parity_status(app)
			if not status.get("at_100"):
				below.append(f"{app}:{status.get('product_pct')}%")
		self.assertFalse(missing, f"Apps not in registry: {missing}")
		self.assertFalse(below, f"Apps below 100% checklist: {below}")
