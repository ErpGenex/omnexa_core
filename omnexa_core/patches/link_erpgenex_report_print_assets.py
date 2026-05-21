# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Deploy ERPGENEX print HTML + letter head on all ErpGenEx Script Reports."""

import frappe


def execute() -> None:
	from omnexa_core.omnexa_core.report_print.link_reports import link_erpgenex_report_print_assets

	link_erpgenex_report_print_assets()
	frappe.clear_cache()
