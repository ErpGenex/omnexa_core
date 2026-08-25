# Copyright (c) 2026, ErpGenEx
"""Wave 8 — Single source of truth for business activities, app bundles, and isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import frappe

from omnexa_core.omnexa_core.app_activity import activity_for_app
from omnexa_core.omnexa_core.app_visibility import COMPANY_ACTIVITY_ALLOWED, PLATFORM_APP_SLUGS

# Financial / inventory / sales / purchase / reporting platform (always integrated, never uninstalled).
FINANCIAL_CORE_APPS: frozenset[str] = frozenset(
	{
		"omnexa_accounting",
		"omnexa_einvoice",
		"omnexa_reporting_compliance",
		"omnexa_customer_core",
		"omnexa_statutory_audit",
	}
)

INVENTORY_SALES_APPS: frozenset[str] = frozenset(
	{
		"omnexa_trading",
		"omnexa_manufacturing",
		"omnexa_services",
	}
)

PLATFORM_STACK_APPS: frozenset[str] = frozenset(PLATFORM_APP_SLUGS) | FINANCIAL_CORE_APPS | frozenset(
	{
		"omnexa_core",
		"omnexa_hr",
		"omnexa_projects_pm",
		"omnexa_fixed_assets",
		"omnexa_setup_intelligence",
		"omnexa_experience",
		"omnexa_n8n_bridge",
		"omnexa_intelligence_core",
		"omnexa_user_academy",
		"omnexa_backup",
		"omnexa_ai_employee",
		"omnexa_theme_manager",
		"omnexa_edms",
		"erpgenex_saas",
		"erpgenex_demo_studio",
		"erpgenex_theme_0426",
	}
)


@dataclass(frozen=True)
class ActivitySpec:
	id: str
	label_en: str
	label_ar: str
	vertical_apps: tuple[str, ...] = ()
	coa_extension_key: str = "General"
	saas_bundle_key: str | None = None
	allowed_app_labels: frozenset[str] = frozenset()

	def apps_for_site(self) -> list[str]:
		"""Platform + financial core + vertical apps (installed-only filtering applied by caller)."""
		seen: set[str] = set()
		out: list[str] = []
		for app in (*PLATFORM_STACK_APPS, *FINANCIAL_CORE_APPS, *self.vertical_apps):
			if app in seen:
				continue
			seen.add(app)
			out.append(app)
		return out


# Canonical activities — keys match Company.business_activity normalization where possible.
ACTIVITIES: dict[str, ActivitySpec] = {
	"General": ActivitySpec(
		id="General",
		label_en="General",
		label_ar="عام",
		saas_bundle_key="عام",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["General"],
	),
	"Healthcare": ActivitySpec(
		id="Healthcare",
		label_en="Healthcare",
		label_ar="الرعاية الصحية",
		vertical_apps=("omnexa_healthcare",),
		coa_extension_key="Healthcare",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Healthcare"],
	),
	"Education": ActivitySpec(
		id="Education",
		label_en="Education",
		label_ar="التعليم",
		vertical_apps=("omnexa_education", "omnexa_nursery"),
		coa_extension_key="Education",
		saas_bundle_key="تعليمي",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Education"],
	),
	"Construction": ActivitySpec(
		id="Construction",
		label_en="Construction",
		label_ar="المقاولات",
		vertical_apps=(
			"omnexa_construction",
			"omnexa_engineering_consulting",
			"omnexa_eng_document_control",
			"omnexa_eng_platform_integrations",
			"omnexa_eng_workflow_engine",
		),
		coa_extension_key="Construction",
		saas_bundle_key="مقاولات",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Construction"],
	),
	"Financial Services": ActivitySpec(
		id="Financial Services",
		label_en="Financial Services",
		label_ar="الخدمات المالية",
		vertical_apps=(
			"omnexa_finance_engine",
			"omnexa_credit_engine",
			"omnexa_credit_risk",
			"omnexa_alm",
			"omnexa_consumer_finance",
			"omnexa_vehicle_finance",
			"omnexa_mortgage_finance",
			"omnexa_factoring",
			"omnexa_sme_retail_finance",
			"omnexa_sme_microfinance",
			"omnexa_leasing_finance",
			"omnexa_operational_risk",
		),
		coa_extension_key="Financial Services",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Financial Services"],
	),
	"Trading": ActivitySpec(
		id="Trading",
		label_en="Trading",
		label_ar="التجارة",
		vertical_apps=("omnexa_trading",),
		coa_extension_key="Trading",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Trading"],
	),
	"Manufacturing": ActivitySpec(
		id="Manufacturing",
		label_en="Manufacturing",
		label_ar="التصنيع",
		vertical_apps=("omnexa_manufacturing", "omnexa_trading"),
		coa_extension_key="Manufacturing",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Manufacturing"],
	),
	"Agriculture": ActivitySpec(
		id="Agriculture",
		label_en="Agriculture",
		label_ar="الزراعة",
		vertical_apps=("omnexa_agriculture",),
		coa_extension_key="Agriculture",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Agriculture"],
	),
	"Tourism": ActivitySpec(
		id="Tourism",
		label_en="Tourism",
		label_ar="السياحة",
		vertical_apps=("omnexa_tourism", "omnexa_car_rental"),
		coa_extension_key="Tourism",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Tourism"],
	),
	"Bakeries": ActivitySpec(
		id="Bakeries",
		label_en="Bakeries",
		label_ar="المخابز",
		vertical_apps=("omnexa_restaurant",),
		coa_extension_key="Bakeries",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Bakeries"],
	),
	"Services": ActivitySpec(
		id="Services",
		label_en="Services",
		label_ar="الخدمات",
		vertical_apps=("omnexa_services",),
		coa_extension_key="Services",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Services"],
	),
	"Real Estate": ActivitySpec(
		id="Real Estate",
		label_en="Real Estate",
		label_ar="العقارات",
		vertical_apps=(
			"erpgenex_realestate_dev",
			"erpgenex_realestate_sales",
			"erpgenex_property_mgmt",
			"erpgenex_maintenance_core",
		),
		coa_extension_key="Real Estate",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["General"] | frozenset({"ErpGenEx"}),
	),
	"Statutory Audit": ActivitySpec(
		id="Statutory Audit",
		label_en="Statutory Audit",
		label_ar="المراجعة القانونية",
		vertical_apps=("omnexa_statutory_audit",),
		coa_extension_key="Statutory Audit",
		allowed_app_labels=COMPANY_ACTIVITY_ALLOWED["Statutory Audit"],
	),
}

SAAS_ACTIVITY_VERTICALS: dict[str, tuple[str, ...]] = {
	spec.saas_bundle_key: spec.vertical_apps
	for spec in ACTIVITIES.values()
	if spec.saas_bundle_key
}

# Whitelisted cross-app imports for integration (vertical → platform only).
INTEGRATION_IMPORT_WHITELIST: frozenset[str] = frozenset(
	{
		"omnexa_core",
		"omnexa_accounting",
		"omnexa_customer_core",
		"omnexa_reporting_compliance",
		"omnexa_einvoice",
		"frappe",
	}
)

INTEGRATION_COMMANDS: frozenset[str] = frozenset(
	{
		"accounting.create_sales_invoice",
		"accounting.create_purchase_invoice",
		"accounting.create_journal_entry",
		"accounting.create_payment_entry",
		"inventory.create_stock_entry",
		"inventory.create_delivery_note",
		"inventory.create_purchase_receipt",
		"reporting.get_financial_snapshot",
		"reporting.get_inventory_snapshot",
	}
)


def list_activities() -> list[str]:
	return sorted(ACTIVITIES.keys())


def get_activity(activity_id: str | None) -> ActivitySpec:
	key = (activity_id or "General").strip()
	if key in ACTIVITIES:
		return ACTIVITIES[key]
	for spec in ACTIVITIES.values():
		if spec.label_ar == key or spec.label_en == key:
			return spec
	return ACTIVITIES["General"]


def resolve_company_activity(company: str | None) -> ActivitySpec:
	if not company or not frappe.db.exists("Company", company):
		return ACTIVITIES["General"]
	from omnexa_core.omnexa_core.company_activity_utils import first_company_activity_value

	raw = first_company_activity_value(company) or "General"
	from omnexa_core.omnexa_core.app_visibility import _normalize_company_activity

	return get_activity(_normalize_company_activity(raw))


def apps_allowed_for_activity(activity_id: str) -> set[str]:
	spec = get_activity(activity_id)
	installed = set(frappe.get_installed_apps() or [])
	keep: set[str] = set()
	for app in installed:
		if app in PLATFORM_STACK_APPS or app in FINANCIAL_CORE_APPS:
			keep.add(app)
			continue
		if activity_for_app(app) in spec.allowed_app_labels:
			keep.add(app)
		if app in spec.vertical_apps:
			keep.add(app)
	return keep


def app_in_activity_registry(app: str) -> bool:
	if app in PLATFORM_STACK_APPS or app in FINANCIAL_CORE_APPS:
		return True
	label = activity_for_app(app)
	for spec in ACTIVITIES.values():
		if app in spec.vertical_apps or label in spec.allowed_app_labels:
			return True
	return False


def get_financial_core_apps() -> list[str]:
	installed = set(frappe.get_installed_apps() or [])
	return sorted(app for app in FINANCIAL_CORE_APPS if app in installed)


def activity_registry_export() -> dict[str, Any]:
	return {
		"activities": len(ACTIVITIES),
		"platform_stack": sorted(PLATFORM_STACK_APPS),
		"financial_core": sorted(FINANCIAL_CORE_APPS),
		"inventory_sales": sorted(INVENTORY_SALES_APPS),
		"integration_commands": sorted(INTEGRATION_COMMANDS),
		"saas_bundles": {k: list(v) for k, v in SAAS_ACTIVITY_VERTICALS.items()},
	}


@frappe.whitelist()
def get_activity_registry() -> dict[str, Any]:
	frappe.only_for("System Manager")
	return activity_registry_export()
