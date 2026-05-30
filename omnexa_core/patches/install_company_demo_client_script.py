"""Install DB Client Script so Company demo buttons work even if desk assets are stale."""

from __future__ import annotations

from pathlib import Path

import frappe


SCRIPT_NAME = "ERPGENEX Company Demo Data"


def execute() -> None:
	if not frappe.db.exists("DocType", "Company"):
		return

	script_path = Path(frappe.get_app_path("omnexa_core", "public", "js", "company_demo_data_hub.js"))
	if not script_path.is_file():
		frappe.log_error(f"Missing {script_path}", "Company demo Client Script")
		return

	script_body = script_path.read_text(encoding="utf-8")

	if frappe.db.exists("Client Script", SCRIPT_NAME):
		doc = frappe.get_doc("Client Script", SCRIPT_NAME)
	else:
		doc = frappe.new_doc("Client Script")
		doc.name = SCRIPT_NAME

	doc.dt = "Company"
	doc.view = "Form"
	doc.enabled = 1
	doc.module = "Omnexa Core"
	doc.script = script_body
	doc.save(ignore_permissions=True)
	frappe.db.commit()
