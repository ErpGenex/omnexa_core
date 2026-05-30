"""Company Demo data tab — server-side action registry (works without fragile client bundles)."""

from __future__ import annotations

import frappe
from frappe import _


def _assert_system_manager() -> None:
	if "System Manager" not in (frappe.get_roles() or []) and frappe.session.user != "Administrator":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _installed() -> set[str]:
	return set(frappe.get_installed_apps() or [])


@frappe.whitelist()
def get_demo_action_specs(company: str) -> list[dict]:
	"""Return button metadata for the Company Demo data tab."""
	_assert_system_manager()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} not found").format(company))

	specs: list[dict] = []
	apps = _installed()

	if "omnexa_accounting" in apps:
		specs.extend(
			[
				{
					"key": "coa_generate",
					"group": _("Production demo"),
					"label": _("Generate professional COA"),
				},
				{
					"key": "ifrs_fill_gl",
					"group": _("IFRS defaults"),
					"label": _("Fill default GLs from CoA (by account number)"),
				},
				{
					"key": "coa_resync_labels",
					"group": _("Production demo"),
					"label": _("Resync COA labels (names from template)"),
				},
				{
					"key": "seed_masters",
					"group": _("Production demo"),
					"label": _("Seed demo data (masters)"),
				},
				{
					"key": "seed_with_tx",
					"group": _("Production demo"),
					"label": _("Seed demo data + transactions"),
				},
				{
					"key": "reset_dry",
					"group": _("Production demo"),
					"label": _("Reset transactions (dry run)"),
				},
				{
					"key": "reset_execute",
					"group": _("Production demo"),
					"label": _("Reset transactions (execute)"),
					"confirm": _("This will cancel and delete matched transactions for this company (and branch if set). Continue?"),
				},
			]
		)
		if frappe.session.user == "Administrator":
			specs.append(
				{
					"key": "wipe_all",
					"group": _("Danger Zone"),
					"label": _("Delete ALL company data (DANGER)"),
					"danger": 1,
					"prompt_confirm_text": 1,
				}
			)

	if "omnexa_construction" in apps:
		specs.append(
			{
				"key": "construction_portfolio",
				"group": _("Construction demo"),
				"label": _("Seed 5 projects (owners, IPC, subcontractors, costs)"),
				"confirm": _(
					"Creates five demo project contracts with clients, subcontractors, BOQ, IPC certificates, site diaries, and WIP. Continue?"
				),
			}
		)

	if "omnexa_fixed_assets" in apps:
		specs.append(
			{
				"key": "hotel_assets",
				"group": _("أصول الفنادق — تجريبي"),
				"label": _("إنشاء 50 أصلًا (غرف + مناطق إدارية + حركات)"),
				"confirm": _(
					"سيتم إنشاء فندقًا تجريبيًا وغرفًا وعدد 50 أصلًا مع رسملة، وتحويلات فندقية، وسجلات RFID. المتابعة؟"
				),
			}
		)

	return specs


@frappe.whitelist()
def run_demo_action(
	company: str,
	action_key: str,
	branch: str | None = None,
	activity: str | None = None,
	confirm_text: str | None = None,
	force: int | str | None = 0,
) -> dict:
	"""Execute a demo action selected on the Company form."""
	_assert_system_manager()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} not found").format(company))

	key = (action_key or "").strip()
	branch = (branch or "").strip() or None
	activity = (activity or "").strip() or None
	if not activity:
		activity = frappe.db.get_value("Company", company, "industry_sector") or "General"

	if key == "coa_generate":
		from omnexa_accounting.utils.production_readiness import generate_professional_chart_of_accounts

		return generate_professional_chart_of_accounts(company, branch=branch, activity=activity)

	if key == "ifrs_fill_gl":
		from omnexa_accounting.utils.company_financial_defaults import fill_company_financial_defaults_from_coa

		return fill_company_financial_defaults_from_coa(company, branch=branch, overwrite=0)

	if key == "coa_resync_labels":
		from omnexa_accounting.utils.production_readiness import resync_chart_of_accounts_labels

		return resync_chart_of_accounts_labels(company, branch=branch, activity=activity)

	if key == "seed_masters":
		from omnexa_accounting.utils.production_readiness import seed_activity_demo_data

		return seed_activity_demo_data(company, branch=branch, activity=activity, include_transactions=0)

	if key == "seed_with_tx":
		from omnexa_accounting.utils.production_readiness import seed_activity_demo_data

		return seed_activity_demo_data(company, branch=branch, activity=activity, include_transactions=1)

	if key == "reset_dry":
		from omnexa_accounting.utils.production_readiness import reset_transactions

		return reset_transactions(company, branch=branch, dry_run=1)

	if key == "reset_execute":
		from omnexa_accounting.utils.production_readiness import enqueue_reset_transactions

		return enqueue_reset_transactions(company, branch=branch, limit=0, batch_size=200)

	if key == "wipe_all":
		from omnexa_accounting.utils.production_readiness import wipe_company_all_data

		return wipe_company_all_data(company, branch=branch, confirm_text=confirm_text or "")

	if key == "construction_portfolio":
		from omnexa_construction.utils.demo_seed import seed_construction_portfolio_demo

		return seed_construction_portfolio_demo(company, branch=branch, force=force)

	if key == "hotel_assets":
		from omnexa_fixed_assets.api import seed_hotel_demo_assets_from_company

		return seed_hotel_demo_assets_from_company(
			company=company,
			count=50,
			with_transfer=1,
			with_rfid=1,
		)

	frappe.throw(_("Unknown demo action: {0}").format(key))
