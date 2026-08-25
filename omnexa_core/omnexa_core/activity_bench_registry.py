# Copyright (c) 2026, ErpGenEx
"""Wave 10 — Activity bench site registry (dedicated sites + erpgenex lanes)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frappe

from frappe.utils import get_bench_path

from omnexa_core.omnexa_core.activity_registry import ACTIVITIES, FINANCIAL_CORE_APPS, PLATFORM_STACK_APPS, get_activity


PRIMARY_SITE = "erpgenex.local.site"

INFRA_APPS = frozenset(
	{
		"frappe",
		"omnexa_core",
		"omnexa_backup",
		"erpgenex_theme_0426",
	}
)


@dataclass(frozen=True)
class ActivityBenchLane:
	activity_id: str
	site: str
	company_abbr: str
	company_name: str
	vertical_apps: tuple[str, ...]
	test_app: str
	test_module: str | None = None
	legacy_site: str | None = None

	def apps_for_lane(self) -> list[str]:
		spec = get_activity(self.activity_id)
		seen: set[str] = set()
		out: list[str] = []
		for app in (*INFRA_APPS, *PLATFORM_STACK_APPS, *FINANCIAL_CORE_APPS, *spec.vertical_apps):
			if app in seen or app == "frappe":
				continue
			seen.add(app)
			out.append(app)
		return out


ACTIVITY_BENCH_LANES: tuple[ActivityBenchLane, ...] = (
	ActivityBenchLane(
		activity_id="Healthcare",
		site="healthcare.local.site",
		company_abbr="AB-HC",
		company_name="Activity Bench Healthcare",
		vertical_apps=("omnexa_healthcare",),
		test_app="omnexa_healthcare",
		test_module="omnexa_healthcare.tests.test_integration_bus",
	),
	ActivityBenchLane(
		activity_id="Construction",
		site="construction.local.site",
		company_abbr="AB-CON",
		company_name="Activity Bench Construction",
		vertical_apps=("omnexa_construction", "omnexa_engineering_consulting"),
		test_app="omnexa_construction",
		test_module="omnexa_construction.tests.test_integration_bus",
	),
	ActivityBenchLane(
		activity_id="Financial Services",
		site="finance.local.site",
		company_abbr="AB-FIN",
		company_name="Activity Bench Financial Services",
		vertical_apps=("omnexa_finance_engine", "omnexa_factoring"),
		test_app="omnexa_finance_engine",
		test_module="omnexa_finance_engine.tests.test_integration_bus",
	),
	ActivityBenchLane(
		activity_id="Trading",
		site="trading.local.site",
		company_abbr="AB-TRD",
		company_name="Activity Bench Trading",
		vertical_apps=("omnexa_trading",),
		test_app="omnexa_trading",
		test_module="omnexa_trading.tests.test_integration_bus",
	),
	ActivityBenchLane(
		activity_id="Education",
		site="education.local.site",
		company_abbr="AB-EDU",
		company_name="Activity Bench Education",
		vertical_apps=("omnexa_education", "omnexa_nursery"),
		test_app="omnexa_education",
		test_module="omnexa_education.tests.test_integration_bus",
	),
)


def site_exists(site: str) -> bool:
	return (Path(get_bench_path()) / "sites" / site).is_dir()


def dedicated_site_ready(site: str) -> bool:
	return site_exists(site) and _site_db_ok(site)


def _site_db_ok(site: str) -> bool:
	import subprocess
	from frappe.utils import get_bench_path

	proc = subprocess.run(
		["bench", "--site", site, "list-apps"],
		cwd=get_bench_path(),
		capture_output=True,
		text=True,
	)
	return proc.returncode == 0 and "frappe" in proc.stdout


def list_physical_sites() -> list[str]:
	root = Path(get_bench_path()) / "sites"
	return sorted(
		p.name
		for p in root.iterdir()
		if p.is_dir() and (p / "site_config.json").is_file() and not p.name.startswith(".")
	)


def lane_for_activity(activity_id: str) -> ActivityBenchLane | None:
	for lane in ACTIVITY_BENCH_LANES:
		if lane.activity_id == activity_id:
			return lane
	return None


def registry_export() -> dict:
	return {
		"primary_site": PRIMARY_SITE,
		"lanes": [
			{
				"activity_id": lane.activity_id,
				"site": lane.site,
				"site_exists": site_exists(lane.site),
				"site_ready": dedicated_site_ready(lane.site),
				"company_abbr": lane.company_abbr,
				"test_app": lane.test_app,
				"vertical_apps": list(lane.vertical_apps),
			}
			for lane in ACTIVITY_BENCH_LANES
		],
		"physical_sites": list_physical_sites(),
		"activities": list(ACTIVITIES.keys()),
	}


@frappe.whitelist()
def get_activity_bench_registry() -> dict:
	frappe.only_for("System Manager")
	return registry_export()
