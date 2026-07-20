# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Fix legacy EG / Arabic onboarding keys + Workspace content references after Workspace labels were finalized."""

from __future__ import annotations

import frappe

from omnexa_core.workspace_onboarding_sync import onboarding_name_for

# (old Module Onboarding `name`, canonical onboarding key)
_LEGACY_ONBOARDING_MO: tuple[tuple[str, str], ...] = (
	("ERPGENEX — EG Property Management", onboarding_name_for("Property Management")),
	("ERPGENEX — EG RE Development", onboarding_name_for("RE Development")),
	("ERPGENEX — EG RE Marketing", onboarding_name_for("RE Marketing")),
	(onboarding_name_for("إدارة العقارات"), onboarding_name_for("Property Management")),
	(onboarding_name_for("تطوير العقارات"), onboarding_name_for("RE Development")),
	(onboarding_name_for("تسويق العقارات"), onboarding_name_for("RE Marketing")),
)

_EG_IN_TITLE = (
	("EG Property Management", "Property Management"),
	("EG RE Development", "RE Development"),
	("EG RE Marketing", "RE Marketing"),
)


def _rename_or_drop_module_onboarding(old: str, new: str) -> None:
	if not frappe.db.exists("Module Onboarding", old):
		return
	try:
		if frappe.db.exists("Module Onboarding", new):
			frappe.delete_doc("Module Onboarding", old, ignore_permissions=True, force=True)
		else:
			frappe.rename_doc("Module Onboarding", old, new, force=True, merge=False)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Omnexa: Module Onboarding realign `{old}` -> `{new}`",
		)


def _rewrite_workspace_onboarding_refs() -> None:
	for row in frappe.get_all("Workspace", fields=["name", "content"]):
		content = row.content or ""
		if not content or "onboarding_name" not in content:
			continue
		next_content = content
		for old, new in _LEGACY_ONBOARDING_MO:
			if old in next_content:
				next_content = next_content.replace(old, new)
		if next_content != content:
			frappe.db.set_value("Workspace", row.name, "content", next_content)


def _scrub_module_onboarding_titles() -> None:
	for row in frappe.get_all("Module Onboarding", fields=["name", "title"]):
		title = row.title or ""
		fixed = title
		for needle, canon in _EG_IN_TITLE:
			if needle in fixed:
				fixed = fixed.replace(needle, canon)
		if fixed.startswith("ERPGENEX ·"):
			fixed = fixed.split(" · ", 1)[-1].strip()
		if fixed != title:
			frappe.db.set_value("Module Onboarding", row.name, "title", fixed)


def execute() -> None:
	for old, new in _LEGACY_ONBOARDING_MO:
		_rename_or_drop_module_onboarding(old, new)
	_rewrite_workspace_onboarding_refs()
	_scrub_module_onboarding_titles()
	frappe.db.commit()
	frappe.clear_cache()
