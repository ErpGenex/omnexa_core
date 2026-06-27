# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class Branch(Document):
	def validate(self):
		self.branch_code = (self.branch_code or "").strip().upper()
		self.branch_name = (self.branch_name or "").strip()
		self._validate_default_vat_rate()
		self._validate_unique_code_per_company()
		self._validate_parent_branch_company()
		self._validate_single_head_office()
		self._validate_eta_einvoice()

	def _validate_eta_einvoice(self):
		if not cint(self.eta_einvoice_enabled):
			return
		meta = self.meta
		if meta.has_field("tax_authority_profile") and meta.has_field("signing_profile"):
			if not self.get("tax_authority_profile") or not self.get("signing_profile"):
				frappe.throw(
					_("Tax Authority Profile and Signing Profile are required when e-invoice is enabled."),
					title=_("E-Invoice"),
				)
			for fieldname in ("tax_authority_profile", "signing_profile"):
				profile = self.get(fieldname)
				if not profile:
					continue
				options = meta.get_field(fieldname).options
				profile_company = frappe.db.get_value(options, profile, "company")
				if profile_company and profile_company != self.company:
					frappe.throw(
						_("{0} must belong to the same company as the branch.").format(
							meta.get_label(fieldname)
						),
						title=_("E-Invoice"),
					)
			return
		if not (self.get("eta_invoice_rin") or "").strip():
			frappe.throw(_("E-Invoice Taxpayer RIN is required when e-invoice is enabled."), title=_("E-Invoice"))
		if not (self.get("eta_invoice_client_id") or "").strip():
			frappe.throw(_("E-Invoice Client ID is required when e-invoice is enabled."), title=_("E-Invoice"))

	def _validate_default_vat_rate(self):
		if not getattr(self, "default_vat_rate", None):
			return
		try:
			rate = float(self.default_vat_rate)
		except Exception:
			frappe.throw(_("Default VAT Rate must be a number."), title=_("Validation"))
		if rate < 0 or rate > 100:
			frappe.throw(_("Default VAT Rate must be between 0 and 100."), title=_("Validation"))

	def _validate_unique_code_per_company(self):
		if not self.company or not self.branch_code:
			return
		dupe = frappe.db.exists(
			"Branch",
			{
				"company": self.company,
				"branch_code": self.branch_code,
			},
		)
		if dupe and (self.is_new() or dupe != self.name):
			frappe.throw(
				_("Branch Code must be unique within the same company."),
				title=_("Validation"),
			)

	def _validate_parent_branch_company(self):
		if not self.parent_branch:
			return
		if self.parent_branch == self.name:
			frappe.throw(_("Parent Branch cannot be the same as branch."), title=_("Validation"))
		parent_company = frappe.db.get_value("Branch", self.parent_branch, "company")
		if parent_company and parent_company != self.company:
			frappe.throw(
				_("Parent Branch must belong to the same company."),
				title=_("Validation"),
			)

	def _validate_single_head_office(self):
		if not self.is_head_office:
			return
		dupe = frappe.db.exists(
			"Branch",
			{
				"company": self.company,
				"is_head_office": 1,
				"name": ("!=", self.name),
			},
		)
		if dupe:
			frappe.throw(_("Only one head office branch is allowed per company."), title=_("Validation"))

	def _run_branch_demo(self, action_key: str, **kwargs):
		from omnexa_core.omnexa_core.branch_demo_api import run_demo_action_for_branch

		return run_demo_action_for_branch(self, action_key, **kwargs)

	def _branch_demo_sim_kwargs(self) -> dict:
		return {
			"include_workspace_seed": cint(self.get("branch_demo_include_workspace_seed") or 1),
			"daily_purchase_invoices": cint(self.get("branch_demo_daily_purchase_invoices") or 10),
			"daily_sales_invoices": cint(self.get("branch_demo_daily_sales_invoices") or 10),
			"employees": cint(self.get("branch_demo_employees") or 5),
			"customers": cint(self.get("branch_demo_customers") or 5),
			"suppliers": cint(self.get("branch_demo_suppliers") or 5),
			"items": cint(self.get("branch_demo_items") or 10),
		}

	def _run_branch_demo_simulation(self, mode: str):
		from omnexa_accounting.utils.production_readiness import enqueue_integrated_demo_simulation

		result = enqueue_integrated_demo_simulation(branch=self.name, mode=mode, **self._branch_demo_sim_kwargs())
		job_id = (result or {}).get("job_id") or "n/a"
		frappe.msgprint(
			_(
				"Integrated demo queued (document chains when enabled + daily invoices, stock, payroll path). Job: {0}<br>Open Production Seed Log for summary when the job completes."
			).format(job_id),
			title=_("Demo simulation"),
			indicator="green",
		)
		return result

	@frappe.whitelist()
	def branch_demo_action_seed_masters(self):
		result = self._run_branch_demo("seed_masters")
		frappe.msgprint(_("Branch demo masters seeded."), indicator="green")
		return result

	@frappe.whitelist()
	def branch_demo_action_seed_with_tx(self):
		result = self._run_branch_demo("seed_with_tx")
		frappe.msgprint(_("Branch demo masters and transactions seeded."), indicator="green")
		return result

	@frappe.whitelist()
	def branch_demo_action_seed_6m(self):
		return self._run_branch_demo_simulation("6m")

	@frappe.whitelist()
	def branch_demo_action_seed_12m(self):
		return self._run_branch_demo_simulation("12m")

	@frappe.whitelist()
	def branch_demo_action_construction_portfolio(self):
		result = self._run_branch_demo("construction_portfolio")
		msg = (result or {}).get("message")
		if msg:
			frappe.msgprint(msg, title=_("Construction demo"), indicator="green")
		return result

	@frappe.whitelist()
	def branch_demo_action_hotel_assets(self):
		result = self._run_branch_demo("hotel_assets")
		frappe.msgprint(
			_("Created {0} hotel demo assets for this branch.").format((result or {}).get("created_count") or 0),
			indicator="green",
		)
		return result

	def _healthcare_demo_kwargs(self) -> dict:
		return {
			"patients": cint(self.get("branch_demo_healthcare_patients")) or 20,
			"include_financial": cint(self.get("branch_demo_healthcare_financial") or 1),
			"force": cint(self.get("branch_demo_healthcare_force") or 0),
		}

	def _finance_demo_kwargs(self) -> dict:
		return {
			"customers": cint(self.get("branch_demo_finance_customers")) or 50,
			"sync_roles": cint(self.get("branch_demo_finance_sync_roles") or 1),
			"force": cint(self.get("branch_demo_finance_force") or 0),
		}

	def _education_demo_kwargs(self) -> dict:
		return {
			"institution_type": self.get("branch_demo_education_institution_type") or "All 5 Types",
			"seed_roles": cint(self.get("branch_demo_education_seed_roles") or 1),
			"sync_laravel": cint(self.get("branch_demo_education_sync_laravel") or 0),
		}

	@frappe.whitelist()
	def branch_demo_action_education(self):
		result = self._run_branch_demo("education", **self._education_demo_kwargs()) or {}
		inst_count = result.get("institutions_seeded") or len(result.get("institutions") or [])
		frappe.msgprint(
			_(
				"EduSphere demo seeded: {0} institution(s) on branch {1}. Open Education Workcenter for role portals."
			).format(inst_count, self.name),
			title=_("EduSphere Education Demo"),
			indicator="green",
		)
		return result

	@frappe.whitelist()
	def branch_demo_action_finance_group(self):
		result = self._run_branch_demo("finance_group", **self._finance_demo_kwargs()) or {}
		if result.get("message") == "already_seeded":
			frappe.msgprint(
				result.get("hint") or _("Finance demo already exists for this branch."),
				title=_("Finance Group demo"),
				indicator="blue",
			)
			return result
		frappe.msgprint(
			_(
				"Finance group demo seeded: {0} cases across {1} apps ({2} clients per app). Open Finance Workcenter to explore portals."
			).format(
				result.get("total_cases") or 0,
				result.get("apps_seeded") or 0,
				result.get("customers_per_app") or 50,
			),
			title=_("Finance Group demo"),
			indicator="green",
		)
		return result

	@frappe.whitelist()
	def branch_demo_action_healthcare_hospital(self):
		result = self._run_branch_demo("healthcare_hospital", **self._healthcare_demo_kwargs()) or {}
		message = result.get("message")
		if message == "already_seeded":
			frappe.msgprint(
				result.get("hint") or _("Healthcare demo already exists for this branch."),
				title=_("Healthcare demo"),
				indicator="blue",
			)
			return result

		patients = result.get("patients") or 0
		web_url = result.get("web_booking_url") or ""
		published = result.get("published_services") or 0
		web_bookings = result.get("web_bookings") or 0
		msg = _("Healthcare hospital demo seeded: {0} patients, {1} web services, {2} online bookings.").format(
			patients,
			published,
			web_bookings,
		)
		if web_url:
			msg += "<br>" + _("Online booking: {0}").format(web_url)
		frappe.msgprint(msg, title=_("Healthcare demo"), indicator="green")
		return result

	@frappe.whitelist()
	def branch_demo_action_reset_dry(self):
		result = self._run_branch_demo("reset_dry")
		frappe.msgprint(_("Dry run complete. See Production Seed Log for details."), indicator="blue")
		return result

	@frappe.whitelist()
	def branch_demo_action_reset_execute(self):
		result = self._run_branch_demo("reset_execute")
		job_id = (result or {}).get("job_id") or "n/a"
		frappe.msgprint(
			_("Branch transaction reset queued. Job: {0}").format(job_id),
			title=_("Reset branch data"),
			indicator="green",
		)
		return result

	@frappe.whitelist()
	def branch_demo_action_wipe_all(self):
		from omnexa_core.omnexa_core.branch_demo_api import wipe_branch_all_data

		confirm_text = (self.get("branch_demo_danger_confirm") or "").strip()
		result = wipe_branch_all_data(self.company, self.name, confirm_text=confirm_text)
		frappe.msgprint(
			_("All branch demo data and transactions have been wiped."),
			title=_("Wipe branch data"),
			indicator="green",
		)
		return result
