# Copyright (c) 2026, ErpGenEx
"""SSOT — ErpGenEx app logo file mapping (Docs/Logos/*.jpg → app public/logo.png)."""

from __future__ import annotations

# Catalog tile order from Docs/Logos/ALL.jpeg; logo JPG numbers differ for banking + late tiles.
APP_LOGO_FILES: dict[str, int] = {
	"omnexa_core": 1,
	"omnexa_customer_core": 2,
	"omnexa_intelligence_core": 3,
	"omnexa_setup_intelligence": 4,
	"omnexa_experience": 5,
	"omnexa_n8n_bridge": 6,
	"omnexa_backup": 7,
	"omnexa_theme_manager": 8,
	"erpgenex_theme_0426": 9,
	"omnexa_user_academy": 10,
	"omnexa_finance_engine": 23,
	"omnexa_credit_engine": 22,
	"omnexa_credit_risk": 21,
	"omnexa_alm": 20,
	"omnexa_consumer_finance": 19,
	"omnexa_vehicle_finance": 18,
	"omnexa_mortgage_finance": 17,
	"omnexa_factoring": 16,
	"omnexa_sme_retail_finance": 15,
	"omnexa_sme_microfinance": 14,
	"omnexa_leasing_finance": 13,
	"omnexa_operational_risk": 12,
	"omnexa_accounting": 11,
	"omnexa_healthcare": 24,
	"omnexa_construction": 25,
	"omnexa_engineering_consulting": 26,
	"omnexa_eng_document_control": 27,
	"omnexa_eng_workflow_engine": 28,
	"omnexa_eng_platform_integrations": 29,
	"omnexa_projects_pm": 30,
	"erpgenex_property_mgmt": 31,
	"erpgenex_realestate_dev": 32,
	"erpgenex_realestate_sales": 33,
	"erpgenex_maintenance_core": 34,
	"omnexa_tourism": 45,
	"omnexa_restaurant": 44,
	"omnexa_car_rental": 43,
	"omnexa_education": 42,
	"omnexa_nursery": 41,
	"omnexa_trading": 40,
	"omnexa_manufacturing": 39,
	"omnexa_agriculture": 38,
	"omnexa_services": 37,
	"omnexa_hr": 36,
	"omnexa_fixed_assets": 35,
	"omnexa_einvoice": 46,
	"omnexa_statutory_audit": 47,
	"omnexa_reporting_compliance": 48,
}


def get_logo_url(app: str) -> str:
	return f"/assets/{app}/logo.png"
