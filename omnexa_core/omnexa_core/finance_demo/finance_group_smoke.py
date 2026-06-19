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
