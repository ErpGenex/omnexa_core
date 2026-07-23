# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Business Categories Configuration for ERPGenex Applications Sidebar Organization"""

from __future__ import annotations

import frappe


BUSINESS_CATEGORIES = {
	"core_erp": {
		"order": 10,
		"label": "Core ERP",
		"purpose": "Core ERP operations",
		"workspaces": [
			"Stock",
			"HR",
			"Fixed Assets",
			"Maintenance Core",
		]},
	"projects_services": {
		"order": 20,
		"label": "Projects & Services",
		"purpose": "Projects, maintenance services and engineering services",
		"workspaces": [
			"projects",
			"Services",
			"engineering-consulting",
		]},
	"customer_management": {
		"order": 30,
		"label": "Customer Management",
		"purpose": "Customers, organizations and master entities",
		"workspaces": [
			"CRM",
		]},
	"finance_group": {
		"order": 40,
		"label": "Finance Group",
		"purpose": "Financial institutions and lending solutions",
		"workspaces": [
			"Finance Engine",
			"Finance Engine Governance",
			"Factoring",
			"Factoring Governance",
			"Leasing Finance",
			"Leasing Finance Governance",
			"Mortgage Finance",
			"Mortgage Finance Governance",
			"Operational Risk",
			"Operational Risk Governance",
			"SME Microfinance",
			"SME Retail Finance",
			"Statutory Audit",
			"Vehicle Finance",
			"Vehicle Finance Governance",
		]},
	"real_estate_construction": {
		"order": 50,
		"label": "Real Estate & Construction",
		"purpose": "Real estate development and property management",
		"workspaces": [
			"Property Management",
			"RE Marketing",
			"RE Development",
		]},
	"engineering": {
		"order": 60,
		"label": "Engineering",
		"purpose": "Engineering consulting and technical projects",
		"workspaces": [
			"engineering-consulting",
		]},
	"manufacturing_trading": {
		"order": 70,
		"label": "Manufacturing & Trading",
		"purpose": "Manufacturing, production and trading",
		"workspaces": [
			"Manufacturing",
			"Trading",
		]},
	"industry_solutions": {
		"order": 80,
		"label": "Industry Solutions",
		"purpose": "Industry-specific business solutions",
		"workspaces": [
			"Healthcare",
			"Education",
			"Restaurant",
			"Tourism",
			"Car Rental",
			"Nursery",
		]},
	"ai_intelligence": {
		"order": 90,
		"label": "AI & Intelligence",
		"purpose": "Artificial intelligence platform",
		"workspaces": []
	},
	"documents_digital_integration": {
		"order": 100,
		"label": "Documents & Digital Integration",
		"purpose": "Document management and integrations",
		"workspaces": [
			"Electronic Archive",
			"E-Invoice",
		]},
	"platform_administration": {
		"order": 110,
		"label": "Platform & Administration",
		"purpose": "Platform administration and management",
		"workspaces": [
			"ERPGenex SaaS",
			"Experience",
			"Theme Manager",
		]},
}


def get_workspace_category(workspace_name: str) -> str | None:
	"""Get the business category for a given workspace"""
	for category_id, category_data in BUSINESS_CATEGORIES.items():
		if workspace_name in category_data["workspaces"]:
			return category_id
	return None


def get_category_workspaces(category_id: str) -> list[str]:
	"""Get all workspaces in a category"""
	return BUSINESS_CATEGORIES.get(category_id, {}).get("workspaces", [])


@frappe.whitelist()
def get_business_categories() -> dict:
	"""Get all business categories with their workspaces"""
	result = {}

	for category_id, category_data in BUSINESS_CATEGORIES.items():
		result[category_id] = {
			"order": category_data["order"],
			"label": category_data["label"],
			"purpose": category_data["purpose"],
			"workspaces": category_data["workspaces"]
	}

	return result
