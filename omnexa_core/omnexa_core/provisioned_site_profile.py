# Copyright (c) 2026, ErpGenEx
"""Post-provisioning Company profile on tenant sites (no erpgenex_saas required)."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.activity_registry import get_activity


def normalize_provisioned_business_activity(raw: str | None) -> str:
	text = (raw or "").strip()
	if not text:
		return "General"
	return get_activity(text).id


def _ensure_marketplace_activity_filter_on() -> None:
	if not frappe.db.exists("DocType", "Omnexa Marketplace Settings"):
		return
	from omnexa_core.omnexa_core.app_visibility import _ensure_settings_doc

	_ensure_settings_doc()
	frappe.db.set_single_value("Omnexa Marketplace Settings", "filter_desk_by_company_activity", 1)


@frappe.whitelist()
def apply_company_activity_profile(business_activity: str | None = None) -> dict:
	"""Set Company activity + strict desk filtering after SaaS site creation."""
	canonical = normalize_provisioned_business_activity(business_activity)
	companies = frappe.get_all("Company", pluck="name", order_by="creation asc")
	if not companies:
		default_company = frappe.db.get_single_value("Global Defaults", "default_company")
		if default_company:
			companies = [default_company]

	from omnexa_core.install import _apply_company_profile_fields

	for company in companies:
		_apply_company_profile_fields(company, canonical, canonical)
		if frappe.db.has_column("Company", "strict_activity_menu_filtering"):
			frappe.db.set_value(
				"Company",
				company,
				"strict_activity_menu_filtering",
				1,
				update_modified=False,
			)

	try:
		_ensure_marketplace_activity_filter_on()
		from omnexa_core.omnexa_core.app_visibility import clear_desk_visibility_cache

		clear_desk_visibility_cache()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Provisioned site activity profile")

	frappe.db.commit()
	return {"company_activity": canonical, "companies_updated": companies}
