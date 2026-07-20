# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Redeploy financial + inventory print templates to all reports."""


def execute():
	import frappe

	from omnexa_core.omnexa_core.report_print.link_reports import link_erpgenex_report_print_assets

	return link_erpgenex_report_print_assets(only_missing_html=False, force_html=True)
