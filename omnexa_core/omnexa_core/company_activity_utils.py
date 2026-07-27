from __future__ import annotations

import frappe

COMPANY_ACTIVITY_FIELDS = (
	"business_activity",
	"industry_sector",
	"production_demo_activity",
)


def company_activity_fields() -> tuple[str, ...]:
	"""Return Company activity columns that exist on the current site."""
	return tuple(field for field in COMPANY_ACTIVITY_FIELDS if frappe.db.has_column("Company", field))


def get_company_activity_row(company: str | None) -> dict:
	"""Fetch only the activity columns that exist for a Company row."""
	if not company or not frappe.db.exists("Company", company):
		return {}
	fields = company_activity_fields()
	if not fields:
		return {}
	row = frappe.db.get_value("Company", company, list(fields), as_dict=True)
	return row or {}


def first_company_activity_value(company: str | None) -> str:
	"""Return the first non-empty activity value stored on Company."""
	row = get_company_activity_row(company)
	for field in company_activity_fields():
		val = (row.get(field) or "").strip()
		if val and val.lower() not in ("", "general"):
			return val
	return "General"


def company_activity_matches(company: str | None, expected: str) -> bool:
	"""Check whether any available Company activity column matches the expected value."""
	if not company or not expected:
		return False
	row = get_company_activity_row(company)
	if not row:
		return False
	for field in company_activity_fields():
		if (row.get(field) or "").strip() == expected:
			return True
	return False
