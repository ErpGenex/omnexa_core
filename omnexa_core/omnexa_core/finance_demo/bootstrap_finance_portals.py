# Copyright (c) 2026, ErpGenEx
"""Bootstrap finance role portal pages to use Journey factory."""

from __future__ import annotations

from pathlib import Path

BENCH = Path(__file__).resolve().parents[5]

PORTAL_JS = '''frappe.pages["{page}"].on_page_load = function (wrapper) {{
\tfunction boot() {{
\t\tif (window.omnexa_finance && omnexa_finance.bootPortalPage) {{
\t\t\tomnexa_finance.bootPortalPage(wrapper, "{page}");
\t\t\treturn;
\t\t}}
\t\tfrappe.require("/assets/omnexa_core/js/finance_portal_page_boot.js", function () {{
\t\t\tomnexa_finance.bootPortalPage(wrapper, "{page}");
\t\t}});
\t}}
\tboot();
}};
'''

# page_name -> relative path under apps/
PORTAL_FILES: dict[str, str] = {
	"fe-servicing-portal": "omnexa_finance_engine/omnexa_finance_engine/omnexa_finance_engine/page/fe_servicing_portal/fe_servicing_portal.js",
	"fe-executive-dashboard": "omnexa_finance_engine/omnexa_finance_engine/omnexa_finance_engine/page/fe_executive_dashboard/fe_executive_dashboard.js",
	"ce-servicing-portal": "omnexa_credit_engine/omnexa_credit_engine/omnexa_credit_engine/page/ce_servicing_portal/ce_servicing_portal.js",
	"ce-executive-dashboard": "omnexa_credit_engine/omnexa_credit_engine/omnexa_credit_engine/page/ce_executive_dashboard/ce_executive_dashboard.js",
	"rk-servicing-portal": "omnexa_credit_risk/omnexa_credit_risk/omnexa_credit_risk/page/rk_servicing_portal/rk_servicing_portal.js",
	"rk-executive-dashboard": "omnexa_credit_risk/omnexa_credit_risk/omnexa_credit_risk/page/rk_executive_dashboard/rk_executive_dashboard.js",
	"al-servicing-portal": "omnexa_alm/omnexa_alm/omnexa_alm/page/al_servicing_portal/al_servicing_portal.js",
	"al-executive-dashboard": "omnexa_alm/omnexa_alm/omnexa_alm/page/al_executive_dashboard/al_executive_dashboard.js",
	"cf-servicing-portal": "omnexa_consumer_finance/omnexa_consumer_finance/omnexa_consumer_finance/page/cf_servicing_portal/cf_servicing_portal.js",
	"cf-executive-dashboard": "omnexa_consumer_finance/omnexa_consumer_finance/omnexa_consumer_finance/page/cf_executive_dashboard/cf_executive_dashboard.js",
	"vf-servicing-portal": "omnexa_vehicle_finance/omnexa_vehicle_finance/omnexa_vehicle_finance/page/vf_servicing_portal/vf_servicing_portal.js",
	"vf-executive-dashboard": "omnexa_vehicle_finance/omnexa_vehicle_finance/omnexa_vehicle_finance/page/vf_executive_dashboard/vf_executive_dashboard.js",
	"mg-servicing-portal": "omnexa_mortgage_finance/omnexa_mortgage_finance/omnexa_mortgage_finance/page/mg_servicing_portal/mg_servicing_portal.js",
	"mg-executive-dashboard": "omnexa_mortgage_finance/omnexa_mortgage_finance/omnexa_mortgage_finance/page/mg_executive_dashboard/mg_executive_dashboard.js",
	"fc-servicing-portal": "omnexa_factoring/omnexa_factoring/omnexa_factoring/page/fc_servicing_portal/fc_servicing_portal.js",
	"fc-executive-dashboard": "omnexa_factoring/omnexa_factoring/omnexa_factoring/page/fc_executive_dashboard/fc_executive_dashboard.js",
	"sr-servicing-portal": "omnexa_sme_retail_finance/omnexa_sme_retail_finance/omnexa_sme_retail_finance/page/sr_servicing_portal/sr_servicing_portal.js",
	"sr-executive-dashboard": "omnexa_sme_retail_finance/omnexa_sme_retail_finance/omnexa_sme_retail_finance/page/sr_executive_dashboard/sr_executive_dashboard.js",
	"mf-servicing-portal": "omnexa_sme_microfinance/omnexa_sme_microfinance/omnexa_sme_microfinance/page/mf_servicing_portal/mf_servicing_portal.js",
	"mf-executive-dashboard": "omnexa_sme_microfinance/omnexa_sme_microfinance/omnexa_sme_microfinance/page/mf_executive_dashboard/mf_executive_dashboard.js",
	"lf-servicing-portal": "omnexa_leasing_finance/omnexa_leasing_finance/omnexa_leasing_finance/page/lf_servicing_portal/lf_servicing_portal.js",
	"lf-executive-dashboard": "omnexa_leasing_finance/omnexa_leasing_finance/omnexa_leasing_finance/page/lf_executive_dashboard/lf_executive_dashboard.js",
	"or-grc-portal": "omnexa_operational_risk/omnexa_operational_risk/omnexa_operational_risk/page/or_grc_portal/or_grc_portal.js",
	"or-executive-dashboard": "omnexa_operational_risk/omnexa_operational_risk/omnexa_operational_risk/page/or_executive_dashboard/or_executive_dashboard.js",
	"acct-executive-dashboard": "omnexa_accounting/omnexa_accounting/omnexa_accounting/page/acct_executive_dashboard/acct_executive_dashboard.js",
	"accounting-close-dashboard": "omnexa_accounting/omnexa_accounting/omnexa_accounting/page/accounting_close_dashboard/accounting_close_dashboard.js"
	}


def bootstrap_finance_portal_pages() -> list[str]:
	from omnexa_core.omnexa_core.finance_demo.finance_portal_registry import export_portal_registry_js

	updated: list[str] = []
	export_portal_registry_js()
	for page, rel in PORTAL_FILES.items():
		path = BENCH / "apps" / rel
		if not path.is_file():
			continue
		path.write_text(PORTAL_JS.format(page=page), encoding="utf-8")
		updated.append(str(path))
	return updated
