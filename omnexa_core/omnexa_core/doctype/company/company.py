# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Company(Document):
	def validate(self):
		self._validate_fiscal_year_start_month()

	def before_insert(self):
		self._prevent_circular_parent()

	def before_save(self):
		self._prevent_circular_parent()

	def after_insert(self):
		self._ensure_head_office_branch()

	def on_update(self):
		self._clear_desk_visibility_cache_if_activity_changed()

	def _clear_desk_visibility_cache_if_activity_changed(self):
		prev = self.get_doc_before_save()
		if not prev:
			return
		keys = ("business_activity", "industry_sector", "production_demo_activity")
		if any((prev.get(k) or "") != (self.get(k) or "") for k in keys):
			try:
				from omnexa_core.omnexa_core.app_visibility import clear_desk_visibility_cache

				clear_desk_visibility_cache()
			except Exception:
				pass

	def on_trash(self):
		from omnexa_core.omnexa_core.branch_access import user_can_wipe_company

		if not user_can_wipe_company():
			return
		try:
			from omnexa_accounting.utils.production_readiness import purge_company_for_deletion

			purge_company_for_deletion(self.name)
		except ImportError:
			pass

	def _prevent_circular_parent(self):
		if not self.parent_company:
			return
		if self.parent_company == self.name:
			frappe.throw(_("Parent Company cannot be the same as the company."), title=_("Validation"))
		walk = self.parent_company
		depth = 0
		while walk and depth < 32:
			if walk == self.name:
				frappe.throw(_("Circular parent company chain is not allowed."), title=_("Validation"))
			walk = frappe.db.get_value("Company", walk, "parent_company")
			depth += 1

	def _validate_fiscal_year_start_month(self):
		if not self.get("fiscal_year_start_month"):
			return
		try:
			m = int(self.fiscal_year_start_month)
		except Exception:
			frappe.throw(_("Fiscal year start month must be between 1 and 12."), title=_("Validation"))
		if m < 1 or m > 12:
			frappe.throw(_("Fiscal year start month must be between 1 and 12."), title=_("Validation"))

	def _ensure_head_office_branch(self):
		if not self.enable_branches:
			return
		if frappe.db.exists("Branch", {"company": self.name, "is_head_office": 1}):
			return
		branch = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": self.name,
				"branch_name": f"{self.abbr} Head Office",
				"branch_code": "HO",
				"status": "Active",
				"is_head_office": 1,
			}
		)
		branch.insert(ignore_permissions=True, ignore_mandatory=True)

	def _coa_activity(self) -> str:
		return (self.get("production_demo_activity") or self.get("industry_sector") or "General").strip() or "General"

	def _run_coa_action(self, action_key: str):
		from omnexa_core.omnexa_core.company_demo_api import run_coa_action_for_company

		result = run_coa_action_for_company(self.name, action_key, activity=self._coa_activity())
		if isinstance(result, dict):
			msg = result.get("message")
			if msg:
				frappe.msgprint(msg, title=_("Chart of accounts"), indicator="green")
		return result

	@frappe.whitelist()
	def demo_action_coa_generate(self):
		return self._run_coa_action("coa_generate")

	@frappe.whitelist()
	def demo_action_ifrs_fill_gl(self):
		return self._run_coa_action("ifrs_fill_gl")

	@frappe.whitelist()
	def demo_action_coa_resync(self):
		return self._run_coa_action("coa_resync_labels")

	@frappe.whitelist()
	def demo_action_reset_dry(self):
		from omnexa_accounting.utils.production_readiness import reset_transactions

		result = reset_transactions(company=self.name, branch=None, dry_run=1)
		frappe.msgprint(
			_("Dry run complete for all branches. See Production Seed Log."),
			indicator="blue",
		)
		return result

	@frappe.whitelist()
	def demo_action_reset_execute(self):
		from omnexa_accounting.utils.production_readiness import enqueue_reset_transactions

		result = enqueue_reset_transactions(company=self.name, branch=None, limit=0, batch_size=200)
		job_id = (result or {}).get("job_id") or "n/a"
		frappe.msgprint(
			_("Company-wide transaction reset queued. Job: {0}").format(job_id),
			title=_("Reset company data"),
			indicator="green",
		)
		return result

	@frappe.whitelist()
	def demo_action_wipe_all(self, confirm_text: str | None = None):
		from omnexa_accounting.utils.production_readiness import enqueue_wipe_company_all_data

		confirm = (confirm_text or self.get("demo_danger_confirm") or "").strip()
		result = enqueue_wipe_company_all_data(company=self.name, branch=None, confirm_text=confirm)
		job_id = (result or {}).get("job_id") or "n/a"
		frappe.msgprint(
			_("Company wipe queued. Job: {0}. Check Production Seed Log when complete.").format(job_id),
			title=_("Wipe company data"),
			indicator="green",
		)
		return result
