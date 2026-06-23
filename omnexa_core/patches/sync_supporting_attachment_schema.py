# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Remove attachment custom fields from queue/log doctypes and sync MySQL schema."""

from __future__ import annotations

import frappe

from omnexa_core.install import _skip_supporting_attachment_doctype, _sync_doctype_database_schema


def execute():
	_cleanup_queue_attachment_custom_fields()
	_sync_doctypes_with_supporting_attachment()


def _cleanup_queue_attachment_custom_fields() -> None:
	rows = frappe.get_all(
		"Custom Field",
		filters={"fieldname": ["in", ["supporting_attachment", "attachments_section"]]},
		fields=["name", "dt"],
	)
	for row in rows:
		if not _skip_supporting_attachment_doctype(row.dt):
			continue
		frappe.delete_doc("Custom Field", row.name, force=1, ignore_permissions=True)
		_sync_doctype_database_schema(row.dt)


def _sync_doctypes_with_supporting_attachment() -> None:
	doctypes = frappe.db.sql_list(
		"""
		SELECT DISTINCT dt
		FROM `tabCustom Field`
		WHERE fieldname = 'supporting_attachment'
		"""
	)
	for dt in doctypes:
		_sync_doctype_database_schema(dt)
