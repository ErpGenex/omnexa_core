# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Install/bootstrap constants extracted from install.py (phase 3 refactor)."""

SUPPORTED_FRAPPE_MAJOR = 15

REQUIRED_SITE_APPS = [
	"omnexa_accounting",
	"erpgenex_theme_0426",
	"omnexa_backup",
	"omnexa_customer_core",
	"omnexa_einvoice",
	"omnexa_experience",
	"omnexa_fixed_assets",
	"omnexa_hr",
	"omnexa_intelligence_core",
	"omnexa_projects_pm",
	"omnexa_engineering_consulting",
	"omnexa_eng_document_control",
	"omnexa_edms",
	"omnexa_eng_platform_integrations",
	"omnexa_eng_workflow_engine",
	"omnexa_reporting_compliance",
	"omnexa_services",
	"omnexa_setup_intelligence",
	"omnexa_statutory_audit",
	"omnexa_theme_manager",
	"omnexa_trading",
	"omnexa_user_academy",
	"omnexa_n8n_bridge",
]

OPTIONAL_OMNEXA_ENG_STUB_APPS = frozenset(
	{
		"omnexa_eng_document_control",
		"omnexa_edms",
		"omnexa_eng_platform_integrations",
		"omnexa_eng_workflow_engine",
	}
)


def strict_required_site_apps() -> list[str]:
	return [app for app in REQUIRED_SITE_APPS if app not in OPTIONAL_OMNEXA_ENG_STUB_APPS]
