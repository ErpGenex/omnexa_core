# Copyright (c) 2026, Omnexa and contributors
import frappe


def execute():
	from omnexa_core.omnexa_core.report_print.sync_json_filters import sync_accounting_report_json_filters

	sync_accounting_report_json_filters()
