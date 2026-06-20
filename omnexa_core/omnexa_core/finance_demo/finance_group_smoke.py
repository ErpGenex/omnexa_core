# Copyright (c) 2026, ErpGenEx
"""Smoke audit for Finance Group — workspaces, pages, gaps, list routes."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.app_uninstall_groups import get_group_apps

MIN_WORKSPACE_LINKS = 25

FINANCE_PAGES: dict[str, tuple[str, str]] = {
	"omnexa_finance_engine": ("fe-executive-dashboard", "fe-servicing-portal"),
	"omnexa_credit_engine": ("ce-executive-dashboard", "ce-servicing-portal"),
	"omnexa_credit_risk": ("rk-executive-dashboard", "rk-servicing-portal"),
	"omnexa_alm": ("al-executive-dashboard", "al-servicing-portal"),
	"omnexa_consumer_finance": ("cf-executive-dashboard", "cf-servicing-portal"),
	"omnexa_vehicle_finance": ("vf-executive-dashboard", "vf-servicing-portal"),
	"omnexa_mortgage_finance": ("mg-executive-dashboard", "mg-servicing-portal"),
	"omnexa_factoring": ("fc-executive-dashboard", "fc-servicing-portal"),
	"omnexa_sme_retail_finance": ("sr-executive-dashboard", "sr-servicing-portal"),
	"omnexa_sme_microfinance": ("mf-executive-dashboard", "mf-servicing-portal"),
	"omnexa_leasing_finance": ("lf-executive-dashboard", "lf-servicing-portal"),
	"omnexa_operational_risk": ("or-executive-dashboard", "or-grc-portal"),
	"omnexa_accounting": ("acct-executive-dashboard", "accounting-close-dashboard"),
}


def _workspace_links(ws_name: str) -> int:
	if not frappe.db.exists("Workspace", ws_name):
		return 0
	return frappe.db.count("Workspace Link", {"parent": ws_name, "parenttype": "Workspace"})


def _gap_status(app: str) -> dict:
	from pathlib import Path

	from frappe.utils import get_bench_path

	for root in (
		Path(get_bench_path()) / "apps" / app / app,
		Path(get_bench_path()) / "apps" / app,
	):
		if not root.is_dir():
			continue
		for py in sorted(root.glob("*_gap_register.py")):
			try:
				return frappe.get_attr(f"{app}.{py.stem}.get_gap_status")()
			except Exception:
				pass
	return {}


def _audit_app(app: str) -> dict:
	from omnexa_core.omnexa_core.workspace_control_tower import _APP_SPECS

	installed = app in (frappe.get_installed_apps() or [])
	spec = _APP_SPECS.get(app, {})
	ws_name = spec.get("workspace", "")
	links = _workspace_links(ws_name) if ws_name else 0
	pages = FINANCE_PAGES.get(app, ("", ""))
	exec_ok = bool(pages[0] and frappe.db.exists("Page", pages[0]))
	serv_ok = bool(pages[1] and frappe.db.exists("Page", pages[1]))
	gaps = _gap_status(app) if installed else {}
	gaps_open = int(gaps.get("gaps_open") or 0) if gaps else -1
	ok = installed and links >= MIN_WORKSPACE_LINKS and exec_ok and serv_ok and (gaps_open == 0 or gaps_open == -1)
	return {
		"app": app,
		"installed": installed,
		"workspace": ws_name,
		"workspace_exists": bool(ws_name and frappe.db.exists("Workspace", ws_name)),
		"workspace_links": links,
		"executive_page": pages[0],
		"executive_ok": exec_ok,
		"servicing_page": pages[1],
		"servicing_ok": serv_ok,
		"gaps_closed": gaps.get("gaps_closed"),
		"gaps_total": gaps.get("gaps_total"),
		"gaps_open": gaps_open,
		"route": f"/app/{frappe.scrub(ws_name)}" if ws_name else "",
		"ok": ok,
	}


@frappe.whitelist()
def run_finance_group_smoke_audit(*, repair_microfinance: int = 0) -> dict:
	"""Audit all Finance Group apps; optionally repair SME Microfinance workspace."""
	frappe.only_for("System Manager")
	if repair_microfinance:
		try:
			from omnexa_sme_microfinance.workspace.mf_workspace import sync_mf_workspace

			sync_mf_workspace()
			frappe.db.commit()
		except Exception as exc:
			frappe.log_error(frappe.get_traceback(), "finance_group_smoke: mf repair")

	try:
		from omnexa_core.omnexa_core.finance_demo.finance_group_workspace import sync_finance_group_home

		sync_finance_group_home()
		from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import sync_finance_group_sidebar

		sync_finance_group_sidebar()
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "finance_group_smoke: fg home sync")

	apps = get_group_apps("finance") + ["omnexa_accounting"]
	results = [_audit_app(a) for a in apps]
	failed = [r for r in results if not r["ok"]]
	return {
		"ok": len(failed) == 0,
		"apps_total": len(apps),
		"apps_passed": len(apps) - len(failed),
		"apps_failed": len(failed),
		"min_workspace_links": MIN_WORKSPACE_LINKS,
		"results": results,
		"failed": failed,
	}


@frappe.whitelist()
def repair_finance_group_workspaces() -> dict:
	"""Re-sync vertical-owned finance workspaces (sidebar links)."""
	frappe.only_for("System Manager")
	repaired: list[str] = []
	errors: list[dict] = []

	syncers = {
		"omnexa_sme_microfinance": "omnexa_sme_microfinance.workspace.mf_workspace.sync_mf_workspace",
		"omnexa_sme_retail_finance": "omnexa_sme_retail_finance.workspace.sr_workspace.sync_sr_workspace_menu",
	}

	for app in get_group_apps("finance") + ["omnexa_accounting"]:
		fn = syncers.get(app)
		if not fn:
			continue
		try:
			frappe.get_attr(fn)()
			repaired.append(app)
		except Exception as exc:
			errors.append({"app": app, "error": str(exc)})

	frappe.db.commit()
	return {"repaired": repaired, "errors": errors}


PORTAL_DEMO_USERS: dict[str, str] = {
	"omnexa_finance_engine": "executive@demo.finance",
	"omnexa_credit_engine": "credit@demo.finance",
	"omnexa_credit_risk": "risk@demo.finance",
	"omnexa_alm": "treasury@demo.finance",
	"omnexa_consumer_finance": "consumer@demo.finance",
	"omnexa_vehicle_finance": "auto@demo.finance",
	"omnexa_mortgage_finance": "mortgage@demo.finance",
	"omnexa_factoring": "factoring@demo.finance",
	"omnexa_sme_retail_finance": "sme@demo.finance",
	"omnexa_sme_microfinance": "micro@demo.finance",
	"omnexa_leasing_finance": "leasing@demo.finance",
	"omnexa_operational_risk": "grc@demo.finance",
	"omnexa_accounting": "accounting@demo.finance",
}


def run_finance_portal_access_audit() -> dict:
	"""Verify each app portal is readable + dashboard API works for its demo user."""
	from frappe.boot import get_allowed_pages

	results: list[dict] = []
	for app, (exec_page, serv_page) in FINANCE_PAGES.items():
		email = PORTAL_DEMO_USERS.get(app)
		if not email or not frappe.db.exists("User", email):
			results.append({"app": app, "ok": False, "reason": "demo_user_missing"})
			continue
		frappe.set_user(email)
		allowed = get_allowed_pages()
		checks: dict[str, bool] = {}
		for page in (exec_page, serv_page):
			page_ok = page in allowed
			api_ok = False
			if page_ok:
				try:
					data = frappe.get_attr(
						"omnexa_core.omnexa_core.finance_demo.finance_portal_desk.get_portal_dashboard"
					)(page=page)
					api_ok = bool(data)
				except Exception:
					api_ok = False
			checks[page] = page_ok and api_ok
		results.append(
			{
				"app": app,
				"user": email,
				"executive_page": exec_page,
				"servicing_page": serv_page,
				"checks": checks,
				"ok": all(checks.values()),
			}
		)
	frappe.set_user("Administrator")
	failed = [r for r in results if not r["ok"]]
	return {
		"ok": len(failed) == 0,
		"portals_total": len(results) * 2,
		"apps_total": len(results),
		"apps_passed": len(results) - len(failed),
		"results": results,
		"failed": failed,
	}


@frappe.whitelist()
def run_finance_portal_access_audit_api() -> dict:
	frappe.only_for("System Manager")
	return run_finance_portal_access_audit()
