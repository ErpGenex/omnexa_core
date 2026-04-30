frappe.setup.on("before_load", function () {
	const omnexaSlides = [
		{
			name: "omnexa_core_company_profile",
			title: __("Company Profile"),
			icon: "fa fa-building",
			fields: [
				{ fieldname: "omnexa_company_name", label: __("Company Legal Name"), fieldtype: "Data", reqd: 1 },
				{ fieldname: "omnexa_company_abbr", label: __("Company Abbreviation"), fieldtype: "Data", reqd: 1 },
				{ fieldname: "omnexa_country", label: __("Country"), fieldtype: "Data", reqd: 1, default: "Egypt" },
				{ fieldtype: "Column Break" },
				{ fieldname: "omnexa_tax_id", label: __("Tax ID"), fieldtype: "Data" },
				{
					fieldname: "omnexa_business_activity",
					label: __("Business Activity"),
					fieldtype: "Select",
					options:
						"\nGeneral\nBakeries (مخابز)\nConstruction\nEngineering Consulting\nHealthcare\nEducation\nManufacturing\nAgriculture\nTourism\nTrading\nServices\nFinancial Services\nStatutory Audit",
				},
				{
					fieldname: "omnexa_industry_sector",
					label: __("Industry Sector"),
					fieldtype: "Select",
					options:
						"\nGeneral\nBakeries (مخابز)\nConstruction\nEngineering Consulting\nHealthcare\nEducation\nManufacturing\nAgriculture\nTourism\nTrading\nServices\nFinancial Services\nStatutory Audit",
				},
			],
		},
		{
			name: "omnexa_core_branch_profile",
			title: __("Main Branch"),
			icon: "fa fa-code-fork",
			fields: [
				{
					fieldname: "omnexa_main_branch_name",
					label: __("Main Branch Name"),
					fieldtype: "Data",
					reqd: 1,
					default: __("Head Office"),
				},
				{ fieldname: "omnexa_main_branch_code", label: __("Main Branch Code"), fieldtype: "Data", reqd: 1, default: "HO" },
				{ fieldtype: "Column Break" },
				{ fieldname: "omnexa_branch_tax_id", label: __("Branch Tax ID"), fieldtype: "Data" },
			],
		},
		{
			name: "omnexa_core_accounting_bootstrap",
			title: __("Chart of Accounts"),
			icon: "fa fa-sitemap",
			fields: [
				{ fieldname: "omnexa_default_vat_rate", label: __("Default VAT Rate (%)"), fieldtype: "Float", default: 15 },
				{
					fieldname: "omnexa_account_numbering_mode",
					label: __("Account Numbering Mode"),
					fieldtype: "Select",
					options: "Standard\nAdvanced (Company-Branch-Type-Subtype-Main-Child)",
					default: "Advanced (Company-Branch-Type-Subtype-Main-Child)",
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "omnexa_enable_starter_coa",
					label: __("Create starter Chart of Accounts"),
					fieldtype: "Check",
					default: 1,
				},
				{
					fieldname: "omnexa_seed_demo_data",
					label: __("Create demo data for training"),
					fieldtype: "Check",
					default: 0,
				},
			],
		},
	];

	omnexaSlides.forEach((slide) => {
		const inSettings = (frappe.setup.slides_settings || []).some((s) => s.name === slide.name);
		if (!inSettings) {
			frappe.setup.slides_settings.push(slide);
		}

		// Frappe may skip default `slides_settings -> slides` copy when frappe setup is considered completed.
		// Push directly to runtime slides to guarantee visibility of Omnexa setup steps.
		const inRuntime = (frappe.setup.slides || []).some((s) => s.name === slide.name);
		if (!inRuntime) {
			frappe.setup.add_slide(slide);
		}
	});
});
