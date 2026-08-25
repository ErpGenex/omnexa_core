import frappe
from omnexa_core.omnexa_core.vertical_dashboard import build_vertical_dashboard_payload

@frappe.whitelist()
def get_vertical_dashboard(company=None):
	return build_vertical_dashboard_payload("omnexa_core", company=company)
