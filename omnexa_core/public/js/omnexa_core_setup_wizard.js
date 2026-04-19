frappe.setup.on("before_load", function () {
	if (
		frappe.boot.setup_wizard_completed_apps?.length &&
		frappe.boot.setup_wizard_completed_apps.includes("omnexa_core")
	) {
		return;
	}

	const existing = frappe.setup.slides_settings.find((s) => s.name === "omnexa_core_foundation");
	if (existing) {
		return;
	}

	frappe.setup.slides_settings.push({
		name: "omnexa_core_foundation",
		title: __("Core Foundation"),
		icon: "fa fa-building",
		fields: [
			{
				fieldname: "omnexa_company_name",
				label: __("Company Legal Name"),
				fieldtype: "Data",
				reqd: 1,
			},
			{
				fieldname: "omnexa_company_abbr",
				label: __("Company Abbreviation"),
				fieldtype: "Data",
				reqd: 1,
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "omnexa_tax_id",
				label: __("Tax ID"),
				fieldtype: "Data",
			},
			{
				fieldtype: "Section Break",
			},
			{
				fieldname: "omnexa_main_branch_name",
				label: __("Main Branch Name"),
				fieldtype: "Data",
				reqd: 1,
				default: __("Head Office"),
			},
			{
				fieldname: "omnexa_main_branch_code",
				label: __("Main Branch Code"),
				fieldtype: "Data",
				reqd: 1,
				default: "MAIN",
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "omnexa_default_vat_rate",
				label: __("Default VAT Rate (%)"),
				fieldtype: "Float",
				default: 15,
			},
			{
				fieldname: "omnexa_enable_starter_coa",
				label: __("Create starter Chart of Accounts"),
				fieldtype: "Check",
				default: 1,
			},
		],
	});
});
