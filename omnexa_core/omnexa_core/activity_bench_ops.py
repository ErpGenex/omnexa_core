# Copyright (c) 2026, ErpGenEx
"""Wave 10 — Provision, inspect, and develop activity bench lanes."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from omnexa_core.omnexa_core.activity_bench_registry import (
	ACTIVITY_BENCH_LANES,
	PRIMARY_SITE,
	ActivityBenchLane,
	dedicated_site_ready,
	lane_for_activity,
	site_exists,
)
from omnexa_core.omnexa_core.activity_registry import get_activity
from omnexa_core.omnexa_core.company_activity_utils import company_activity_fields


def _set_company_activity(company: str, activity_id: str) -> None:
	activity = get_activity(activity_id).id
	for field in company_activity_fields():
		if frappe.db.has_column("Company", field):
			frappe.db.set_value("Company", company, field, activity, update_modified=False)
	if frappe.db.has_column("Company", "strict_activity_menu_filtering"):
		frappe.db.set_value("Company", company, "strict_activity_menu_filtering", 1, update_modified=False)


def _ensure_branch(company: str, branch_code: str) -> str:
	existing_ho = frappe.db.get_value("Branch", {"company": company, "is_head_office": 1}, "name")
	if existing_ho:
		return existing_ho
	filters = {"company": company}
	if frappe.db.has_column("Branch", "branch_code"):
		filters["branch_code"] = branch_code
	else:
		filters["branch_name"] = branch_code
	name = frappe.db.get_value("Branch", filters, "name")
	if name:
		return name
	payload = {
		"doctype": "Branch",
		"company": company,
		"branch_name": branch_code,
		"is_head_office": 1,
		"status": "Active",
	}
	if frappe.db.has_column("Branch", "branch_code"):
		payload["branch_code"] = branch_code
	doc = frappe.get_doc(payload)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_erpgenex_lane_company(lane: ActivityBenchLane) -> dict[str, Any]:
	"""Create or refresh activity-scoped benchmark company on the primary portfolio site."""
	company_name = lane.company_name
	existing = frappe.db.get_value("Company", {"abbr": lane.company_abbr}, "name")
	if existing:
		company = existing
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": company_name,
				"abbr": lane.company_abbr,
				"default_currency": frappe.db.get_value("Company", {}, "default_currency") or "EGP",
				"country": frappe.db.get_value("Company", {}, "country") or "Egypt",
			}
		)
		doc.insert(ignore_permissions=True)
		company = doc.name

	_set_company_activity(company, lane.activity_id)
	branch = _ensure_branch(company, f"{lane.company_abbr}-HO")
	frappe.db.commit()
	return {
		"lane": lane.activity_id,
		"mode": "erpgenex_company",
		"site": PRIMARY_SITE,
		"company": company,
		"branch": branch,
		"activity_id": lane.activity_id,
	}


def inspect_lane(lane: ActivityBenchLane, *, site: str | None = None) -> dict[str, Any]:
	target_site = site or (lane.site if site_exists(lane.site) else PRIMARY_SITE)
	installed = set(frappe.get_installed_apps() or [])
	required = set(lane.apps_for_lane())
	missing_apps = sorted(required - installed - {"frappe"})
	vertical_ok = all(app in installed for app in lane.vertical_apps)
	company_info = {}
	if target_site == PRIMARY_SITE:
		company = frappe.db.get_value("Company", {"abbr": lane.company_abbr}, "name")
		if company:
			row = frappe.db.get_value(
				"Company",
				company,
				["name", "company_name"] + list(company_activity_fields()),
				as_dict=True,
			)
			company_info = row or {"name": company}
	return {
		"activity_id": lane.activity_id,
		"target_site": target_site,
		"dedicated_site_exists": site_exists(lane.site),
		"dedicated_site_ready": dedicated_site_ready(lane.site),
		"vertical_apps_installed": vertical_ok,
		"missing_apps": missing_apps,
		"company": company_info,
		"ready": vertical_ok and not missing_apps,
	}


def develop_erpgenex_lane(lane: ActivityBenchLane) -> dict[str, Any]:
	"""Ensure company + migrate hooks for an activity lane on the primary site."""
	out = ensure_erpgenex_lane_company(lane)
	try:
		from omnexa_core.install import before_tests

		before_tests()
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Activity bench before_tests: {lane.activity_id}")

	# Activity-specific demo seeds when available
	company = out["company"]
	branch = out.get("branch")
	if lane.activity_id == "Healthcare" and "omnexa_healthcare" in frappe.get_installed_apps():
		try:
			from omnexa_healthcare.utils.branch_demo_seed import seed_healthcare_clinic_demo

			seed_healthcare_clinic_demo(company=company, branch=branch)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Activity bench healthcare seed")
	elif lane.activity_id == "Financial Services":
		try:
			from omnexa_core.omnexa_core.finance_demo.finance_vertical_bpe import seed_all_finance_vertical_demos

			seed_all_finance_vertical_demos()
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Activity bench finance seed")

	frappe.db.commit()
	out["inspection"] = inspect_lane(lane)
	out["developed"] = True
	return out


def inspect_all_lanes() -> dict[str, Any]:
	lanes = [inspect_lane(lane) for lane in ACTIVITY_BENCH_LANES]
	ready = sum(1 for row in lanes if row.get("ready"))
	return {
		"primary_site": PRIMARY_SITE,
		"total_lanes": len(lanes),
		"ready_lanes": ready,
		"lanes": lanes,
	}


def develop_dedicated_site(lane: ActivityBenchLane) -> dict[str, Any]:
	"""Install platform + vertical apps on a dedicated bench site."""
	import subprocess
	from frappe.utils import get_bench_path

	site = lane.site
	if not site_exists(site) or not dedicated_site_ready(lane.site):
		if site_exists(site) and not dedicated_site_ready(lane.site):
			return {"site": site, "developed": False, "reason": "site_db_broken_reprovision"}
		return {"site": site, "developed": False, "reason": "site_missing"}

	bench = get_bench_path()
	apps = ["frappe", *lane.apps_for_lane()]
	installed = set(frappe.get_installed_apps() or []) if frappe.local.site == site else set()
	results: list[dict] = []

	for app in apps:
		if app in installed:
			continue
		proc = subprocess.run(
			["bench", "--site", site, "install-app", app],
			cwd=bench,
			capture_output=True,
			text=True,
		)
		results.append({"app": app, "ok": proc.returncode == 0, "tail": (proc.stderr or proc.stdout)[-200:]})

	subprocess.run(["bench", "--site", site, "migrate"], cwd=bench, capture_output=True)
	return {"site": site, "activity_id": lane.activity_id, "installs": results, "developed": True}


def develop_all_lanes() -> dict[str, Any]:
	results = [develop_erpgenex_lane(lane) for lane in ACTIVITY_BENCH_LANES]
	dedicated = []
	for lane in ACTIVITY_BENCH_LANES:
		if site_exists(lane.site):
			dedicated.append(develop_dedicated_site(lane))
	return {
		"developed": len(results),
		"lanes": results,
		"dedicated_sites": dedicated,
		"inspection": inspect_all_lanes(),
	}


@frappe.whitelist()
def develop_activity_bench_lane(activity_id: str) -> dict[str, Any]:
	frappe.only_for("System Manager")
	lane = lane_for_activity(activity_id)
	if not lane:
		frappe.throw(_("Unknown activity bench lane: {0}").format(activity_id))
	return develop_erpgenex_lane(lane)


@frappe.whitelist()
def inspect_activity_bench_lanes() -> dict[str, Any]:
	frappe.only_for("System Manager")
	return inspect_all_lanes()
