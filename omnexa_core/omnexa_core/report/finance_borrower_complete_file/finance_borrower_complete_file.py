# Copyright (c) 2026, ErpGenEx

import frappe

from omnexa_core.omnexa_core.finance_demo.finance_borrower_dossier import get_dossier_report_data


def execute(filters=None):
	columns, data, message = get_dossier_report_data(filters)
	return columns, data, message, None, None, False
