# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe


def execute():
	from omnexa_core.omnexa_core.branch_field_sweep import sweep_branch_fields_for_apps

	sweep_branch_fields_for_apps()
	frappe.db.commit()
