# Copyright (c) 2026, ErpGenEx
"""Finance Group app registry — logos, routes, marketing names (SSOT)."""

from __future__ import annotations

import frappe

# Catalog tile # from Docs/Logos/Logos.png (banking row 11–22; FinTruth is Core platform #23)
BANKING_FINANCE_APPS: list[str] = [
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
]

FINANCE_APP_REGISTRY: list[dict] = [
	{
		"app": "omnexa_finance_engine",
		"tile": 11,
		"marketing_en": "FinanceCore",
		"marketing_ar": "FinanceCore",
		"workspace": "Finance Engine",
		"exec_page": "fe-executive-dashboard",
		"serv_page": "fe-servicing-portal",
		"icon": "bank"
	},
	{
		"app": "omnexa_credit_engine",
		"tile": 12,
		"marketing_en": "CreditPulse",
		"marketing_ar": "CreditPulse",
		"workspace": "Credit Engine",
		"exec_page": "ce-executive-dashboard",
		"serv_page": "ce-servicing-portal",
		"icon": "dashboard"
	},
	{
		"app": "omnexa_credit_risk",
		"tile": 13,
		"marketing_en": "RiskGuard",
		"marketing_ar": "RiskGuard",
		"workspace": "Credit Risk",
		"exec_page": "rk-executive-dashboard",
		"serv_page": "rk-servicing-portal",
		"icon": "trending-up"
	},
	{
		"app": "omnexa_alm",
		"tile": 14,
		"marketing_en": "TreasuryALM",
		"marketing_ar": "TreasuryALM",
		"workspace": "ALM",
		"exec_page": "al-executive-dashboard",
		"serv_page": "al-servicing-portal",
		"icon": "stock"
	},
	{
		"app": "omnexa_consumer_finance",
		"tile": 15,
		"marketing_en": "RetailLend",
		"marketing_ar": "RetailLend",
		"workspace": "Consumer Finance",
		"exec_page": "cf-executive-dashboard",
		"serv_page": "cf-servicing-portal",
		"icon": "shopping-cart"
	},
	{
		"app": "omnexa_vehicle_finance",
		"tile": 16,
		"marketing_en": "AutoLend",
		"marketing_ar": "AutoLend",
		"workspace": "Vehicle Finance",
		"exec_page": "vf-executive-dashboard",
		"serv_page": "vf-servicing-portal",
		"icon": "car"
	},
	{
		"app": "omnexa_mortgage_finance",
		"tile": 17,
		"marketing_en": "HomeLend",
		"marketing_ar": "HomeLend",
		"workspace": "Mortgage Finance",
		"exec_page": "mg-executive-dashboard",
		"serv_page": "mg-servicing-portal",
		"icon": "home"
	},
	{
		"app": "omnexa_factoring",
		"tile": 18,
		"marketing_en": "FactorFlow",
		"marketing_ar": "FactorFlow",
		"workspace": "Factoring",
		"exec_page": "fc-executive-dashboard",
		"serv_page": "fc-servicing-portal",
		"icon": "file"
	},
	{
		"app": "omnexa_sme_retail_finance",
		"tile": 19,
		"marketing_en": "SMECapital",
		"marketing_ar": "SMECapital",
		"workspace": "SME Retail Finance",
		"exec_page": "sr-executive-dashboard",
		"serv_page": "sr-servicing-portal",
		"icon": "organization"
	},
	{
		"app": "omnexa_sme_microfinance",
		"tile": 20,
		"marketing_en": "MicroCapital",
		"marketing_ar": "MicroCapital",
		"workspace": "SME Microfinance",
		"exec_page": "mf-executive-dashboard",
		"serv_page": "mf-servicing-portal",
		"icon": "users"
	},
	{
		"app": "omnexa_leasing_finance",
		"tile": 21,
		"marketing_en": "LeaseMaster",
		"marketing_ar": "LeaseMaster",
		"workspace": "Leasing Finance",
		"exec_page": "lf-executive-dashboard",
		"serv_page": "lf-servicing-portal",
		"icon": "tool"
	},
	{
		"app": "omnexa_operational_risk",
		"tile": 22,
		"marketing_en": "OpRisk",
		"marketing_ar": "OpRisk",
		"workspace": "Operational Risk",
		"exec_page": "or-executive-dashboard",
		"serv_page": "or-grc-portal",
		"icon": "quality"
	},
]

# FinTruth — Core platform GL (NOT a child of Finance Group sidebar).
CORE_ACCOUNTING_REGISTRY: dict = {
	"app": "omnexa_accounting",
	"tile": 23,
	"marketing_en": "FinTruth",
	"marketing_ar": "FinTruth",
	"workspace": "Accounting",
	"exec_page": "acct-executive-dashboard",
	"serv_page": "accounting-close-dashboard",
	"icon": "accounting",
	"parent": "core"
	}


def get_full_finance_catalog() -> list[dict]:
	"""Banking verticals + platform accounting entry (for portals/marketing only)."""
	return [*FINANCE_APP_REGISTRY, CORE_ACCOUNTING_REGISTRY]


def get_registry_entry(app: str) -> dict | None:
	for row in FINANCE_APP_REGISTRY:
		if row["app"] == app:
			return row
	return None


def get_app_route(workspace: str) -> str:
	return f"/app/{frappe.scrub(workspace)}"


def get_servicing_portal_route(app: str) -> str:
	"""Default desk entry — finance servicing portal page (not workspace slug)."""
	for row in get_full_finance_catalog():
		if row.get("app") == app and row.get("serv_page"):
			return f"/app/{row['serv_page']}"
	return get_app_route((get_registry_entry(app) or {}).get("workspace") or app)


def get_logo_url(app: str) -> str:
	return f"/assets/{app}/logo.png"


def get_installed_registry() -> list[dict]:
	installed = set(frappe.get_installed_apps() or [])
	out = []
	for row in FINANCE_APP_REGISTRY:
		if row["app"] in installed:
			item = dict(row)
			item["route"] = get_servicing_portal_route(row["app"])
			item["logo_url"] = get_logo_url(row["app"])
			out.append(item)
	return out
