# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Site-wide admin tools — purge companies/branches (System Manager only)."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_core.omnexa_core.branch_access import user_can_wipe_company


def _assert_admin() -> None:
	if not user_can_wipe_company():
		frappe.throw(_("Only System Manager or Administrator can run site purge."), frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def purge_all_branches(confirm_text: str | None = None) -> dict:
	"""Delete every branch on the site (after per-branch data wipe)."""
	_assert_admin()
	if (confirm_text or "").strip().upper() != "DELETE ALL BRANCHES":
		frappe.throw(_('Type exactly "DELETE ALL BRANCHES" to confirm.'))

	from omnexa_core.omnexa_core.branch_demo_api import wipe_branch_all_data

	results = []
	for row in frappe.get_all("Branch", fields=["name", "company"], order_by="creation desc"):
		try:
			wipe_branch_all_data(row.company, row.name, confirm_text="DELETE ALL")
		except Exception:
			pass
		try:
			frappe.delete_doc("Branch", row.name, force=1, ignore_permissions=True)
			results.append(row.name)
		except Exception as exc:
			frappe.log_error(title=f"Purge branch {row.name}", message=str(exc))

	frappe.db.commit()
	frappe.clear_cache()
	return {"deleted_branches": results, "count": len(results)}


@frappe.whitelist(methods=["POST"])
def purge_all_companies(confirm_text: str | None = None) -> dict:
	"""Delete every company (full wipe + company record)."""
	_assert_admin()
	if (confirm_text or "").strip().upper() != "DELETE ALL COMPANIES":
		frappe.throw(_('Type exactly "DELETE ALL COMPANIES" to confirm.'))

	from omnexa_accounting.utils.production_readiness import enqueue_wipe_company_all_data

	deleted = []
	for company in frappe.get_all("Company", pluck="name", order_by="creation desc"):
		try:
			enqueue_wipe_company_all_data(company=company, branch=None, confirm_text="DELETE ALL")
		except Exception:
			try:
				from omnexa_accounting.utils.production_readiness import purge_company_for_deletion

				purge_company_for_deletion(company)
			except Exception:
				pass
		try:
			frappe.delete_doc("Company", company, force=1, ignore_permissions=True)
			deleted.append(company)
		except Exception as exc:
			frappe.log_error(title=f"Purge company {company}", message=str(exc))

	frappe.db.commit()
	frappe.clear_cache()
	return {"deleted_companies": deleted, "count": len(deleted)}


@frappe.whitelist()
def get_site_entity_counts() -> dict:
	_assert_admin()
	return {
		"companies": frappe.db.count("Company"),
		"branches": frappe.db.count("Branch"),
		"users": frappe.db.count("User", {"enabled": 1, "name": ["not in", ["Guest", "Administrator"]]}),
	}


ACTIVITY_DEMO_SPECS: tuple[tuple[str, str, str], ...] = (
	("General", "عام", "DGEN"),
	("Healthcare", "الرعاية الصحية", "DHLT"),
	("Education", "التعليم", "DEDU"),
	("Construction", "المقاولات", "DCON"),
	("Engineering Consulting", "الاستشارات الهندسية", "DENG"),
	("Financial Services", "الخدمات المالية", "DFIN"),
	("Trading", "التجارة", "DTRD"),
	("Manufacturing", "التصنيع", "DMFG"),
	("Agriculture", "الزراعة", "DAGR"),
	("Tourism", "السياحة", "DTOU"),
	("Hotel Assets", "أصول الفنادق", "DHOT"),
	("Bakeries", "المخابز", "DBAK"),
	("Services", "الخدمات", "DSVC"),
	("Statutory Audit", "التدقيق القانوني", "DAUD"),
)

# Stored on Company fields — must match Select options where applicable.
ACTIVITY_PROFILE_VALUES: dict[str, str] = {
	"Hotel Assets": "Hotel Assets (إدارة أصول الفنادق)",
	"Bakeries": "Bakeries (المخابز والحلويات)",
}


def _activity_profile_value(activity: str) -> str:
	return ACTIVITY_PROFILE_VALUES.get(activity, activity)


def _delete_company_fully(company: str) -> dict:
	"""Wipe transactions/masters then remove company record."""
	from omnexa_accounting.utils.production_readiness import purge_company_for_deletion, wipe_company_all_data

	result = {"company": company, "deleted": False}
	if not frappe.db.exists("Company", company):
		return result
	try:
		result["wipe"] = wipe_company_all_data(
			company=company, branch=None, confirm_text="DELETE ALL", user="Administrator"
		)
	except Exception as exc:
		result["wipe_error"] = str(exc)
		frappe.log_error(frappe.get_traceback(), f"Rebuild demos: wipe {company}")
	try:
		result["purge"] = purge_company_for_deletion(company)
	except Exception as exc:
		result["purge_error"] = str(exc)
		frappe.log_error(frappe.get_traceback(), f"Rebuild demos: purge {company} for deletion")
	try:
		frappe.delete_doc("Company", company, ignore_permissions=True, force=1)
		result["deleted"] = True
	except Exception as exc:
		result["delete_error"] = str(exc)
		frappe.log_error(frappe.get_traceback(), f"Rebuild demos: delete company {company}")
	frappe.db.commit()
	return result


def _trim_non_head_branches(company: str) -> list[str]:
	"""Keep only head-office branch on the main company."""
	from omnexa_core.omnexa_core.branch_demo_api import wipe_branch_all_data

	removed: list[str] = []
	for branch in frappe.get_all(
		"Branch", filters={"company": company, "is_head_office": 0}, pluck="name", order_by="creation desc"
	):
		try:
			wipe_branch_all_data(company, branch, confirm_text="DELETE BRANCH")
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Rebuild demos: wipe branch {branch}")
		try:
			frappe.delete_doc("Branch", branch, ignore_permissions=True, force=1)
			removed.append(branch)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Rebuild demos: delete branch {branch}")
	frappe.db.commit()
	return removed


def _create_activity_demo_company(activity: str, ar_label: str, abbr: str, currency: str, country: str) -> dict:
	from omnexa_core.install import (
		_apply_company_profile_fields,
		_ensure_branch,
		_ensure_company,
		_ensure_starter_chart_of_accounts,
		_seed_demo_data,
		ensure_company_branding_fields,
	)

	ensure_company_branding_fields()
	company_name = f"شركة تجريبية — {ar_label}"
	branch_name = f"الفرع الرئيسي — {ar_label}"
	branch_code = "HO"

	company = _ensure_company(company_name, abbr, currency, country, tax_id="")
	profile_activity = _activity_profile_value(activity)
	_apply_company_profile_fields(company, business_activity=profile_activity, industry_sector=profile_activity)
	branch = _ensure_branch(company, branch_name, branch_code, tax_id="")
	_ensure_starter_chart_of_accounts(company=company, branch=branch, activity=activity)
	_seed_demo_data(company=company, branch=branch, activity=activity)

	extra: dict = {}
	try:
		extra = _seed_enhanced_activity_demo(company, branch, activity)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Rebuild demos: enhanced seed {activity}")

	frappe.db.commit()
	return {
		"activity": activity,
		"company": company,
		"branch": branch,
		"company_name": company_name,
		"enhanced": extra,
	}


def _seed_enhanced_activity_demo(company: str, branch: str, activity: str) -> dict:
	"""Activity-specific demo layers on top of generic seed."""
	installed = set(frappe.get_installed_apps() or [])
	out: dict = {}

	prev_company = frappe.defaults.get_user_default("Company")
	prev_branch = frappe.defaults.get_user_default("Branch")
	frappe.db.set_default("Company", company)
	frappe.db.set_default("Branch", branch)

	try:
		if activity == "Healthcare" and "omnexa_healthcare" in installed:
			from omnexa_healthcare.utils.branch_demo_seed import seed_healthcare_hospital_demo

			out["healthcare"] = seed_healthcare_hospital_demo(
				company=company, branch=branch, patients=15, force=1, include_financial=1
			)

		if activity == "Construction" and "omnexa_construction" in installed:
			from omnexa_construction.utils.demo_seed import seed_construction_portfolio_demo

			out["construction"] = seed_construction_portfolio_demo(company=company, branch=branch, force=1)

		if activity == "Hotel Assets" and "omnexa_fixed_assets" in installed:
			from omnexa_fixed_assets.api import seed_hotel_demo_assets_from_company

			out["hotel_assets"] = seed_hotel_demo_assets_from_company(
				company=company, branch=branch, count=25, with_transfer=1, with_rfid=0
			)

		if activity == "Financial Services":
			from omnexa_core.omnexa_core.finance_demo.finance_branch_demo_seed import seed_finance_group_branch_demo

			out["finance"] = seed_finance_group_branch_demo(
				app="omnexa_leasing_finance", company=company, branch=branch, force=1
			)
	except Exception as exc:
		out["error"] = str(exc)
		frappe.log_error(frappe.get_traceback(), f"Enhanced demo seed failed: {activity} / {company}")
	finally:
		if prev_company:
			frappe.db.set_default("Company", prev_company)
		if prev_branch:
			frappe.db.set_default("Branch", prev_branch)

	return out


@frappe.whitelist(methods=["POST"])
def rebuild_activity_demo_companies(
	keep_company: str | None = None,
	confirm_text: str | None = None,
) -> dict:
	"""Delete all companies/branches except main HQ, then create one demo company per business activity."""
	_assert_admin()
	frappe.only_for("System Manager")
	normalized = " ".join((confirm_text or "").strip().upper().split())
	if normalized not in {"REBUILD ACTIVITY DEMOS", "REBUILDACTIVITYDEMOS"}:
		frappe.throw(
			_('Type exactly "REBUILD ACTIVITY DEMOS" to confirm.'),
			title=_("Rebuild Activity Demo Companies"),
		)

	main = (keep_company or "").strip() or frappe.db.get_single_value("Global Defaults", "default_company")
	if not main or not frappe.db.exists("Company", main):
		main = frappe.db.get_value("Company", {}, "name", order_by="creation asc")
	if not main:
		frappe.throw(_("No main company found on site."))

	currency = frappe.db.get_value("Company", main, "default_currency") or "EGP"
	country = frappe.db.get_value("Company", main, "country") or "Egypt"

	deleted_companies: list[dict] = []
	for company in frappe.get_all("Company", pluck="name", order_by="creation desc"):
		if company == main:
			continue
		deleted_companies.append(_delete_company_fully(company))

	trimmed_branches = _trim_non_head_branches(main)

	created: list[dict] = []
	errors: list[dict] = []
	for activity, ar_label, abbr in ACTIVITY_DEMO_SPECS:
		if frappe.db.exists("Company", {"abbr": abbr}):
			deleted_companies.append(_delete_company_fully(frappe.db.get_value("Company", {"abbr": abbr}, "name")))
		try:
			created.append(_create_activity_demo_company(activity, ar_label, abbr, currency, country))
		except Exception as exc:
			errors.append({"activity": activity, "error": str(exc)})
			frappe.log_error(frappe.get_traceback(), f"Rebuild demos: create {activity}")

	frappe.db.set_default("Company", main)
	head_branch = frappe.db.get_value("Branch", {"company": main, "is_head_office": 1}, "name")
	if head_branch:
		frappe.db.set_default("Branch", head_branch)
	if frappe.db.exists("DocType", "Global Defaults"):
		frappe.db.set_single_value("Global Defaults", "default_company", main)

	frappe.db.commit()
	frappe.clear_cache()

	return {
		"ok": not errors,
		"main_company": main,
		"main_branch": head_branch,
		"deleted_companies": deleted_companies,
		"trimmed_branches_on_main": trimmed_branches,
		"created_activity_companies": created,
		"errors": errors,
		"totals": {
			"companies": frappe.db.count("Company"),
			"branches": frappe.db.count("Branch"),
		},
	}
