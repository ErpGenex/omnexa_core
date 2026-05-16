# Copyright (c) 2026, Omnexa
# License: MIT

"""Shared fixtures for ERPGenex vertical E2E tests."""

from __future__ import annotations

import frappe


def require_company() -> str:
	name = frappe.db.get_value("Company", {}, "name")
	if not name:
		frappe.throw("E2E tests require at least one Company on the site.")
	return name


def require_branch(company: str) -> str:
	branch = frappe.db.get_value("Branch", {"company": company}, "name")
	if not branch:
		frappe.throw(f"E2E tests require a Branch for company {company}.")
	return branch


def ensure_customer(name_suffix: str, company: str) -> str:
	"""Create or reuse a Customer scoped to company with a stable unique code."""
	code = f"E2E-{frappe.scrub(name_suffix)[:40]}"
	existing = frappe.db.get_value("Customer", {"company": company, "customer_code": code}, "name")
	if existing:
		return existing
	cname = f"E2E Cust {name_suffix}"
	doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"company": company,
			"customer_name": cname,
			"customer_code": code,
			"customer_type": "Individual",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_item(company: str) -> str:
	code = "E2E-RE-UNIT-SALE"
	if frappe.db.exists("Item", code):
		return code
	uom = frappe.db.get_value("UOM", {}, "name") or "Nos"
	doc = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": code,
			"item_name": "E2E Real Estate Unit Sale",
			"stock_uom": uom,
			"is_stock_item": 0,
			"is_sales_item": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
