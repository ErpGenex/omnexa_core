# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe

from omnexa_core.omnexa_core.report_print.infer_report_filters import sync_all_erpgenex_report_json_filters


def execute():
	sync_all_erpgenex_report_json_filters(only_empty=True)
