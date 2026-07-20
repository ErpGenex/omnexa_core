# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Install/bootstrap constants extracted from install.py (phase 3 refactor)."""

SUPPORTED_FRAPPE_MAJOR = 15

# Minimal platform stack ensured before marketplace / core bootstrap (no vertical chains).
BASIC_PLATFORM_APPS = [
	"frappe",
	"omnexa_core",
	"omnexa_accounting",
	"omnexa_fixed_assets",
	"omnexa_hr",
	"omnexa_projects_pm",
	"omnexa_ai_employee",
	"omnexa_customer_core",
	"omnexa_einvoice",
	"omnexa_experience",
	"omnexa_intelligence_core",
	"omnexa_n8n_bridge",
	"omnexa_user_academy",
	"omnexa_theme_manager",
	"omnexa_statutory_audit",
	"erpgenex_theme_0426",
	"omnexa_backup",
]

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
	"omnexa_ai_employee",
	"omnexa_statutory_audit",
	"omnexa_theme_manager",
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
