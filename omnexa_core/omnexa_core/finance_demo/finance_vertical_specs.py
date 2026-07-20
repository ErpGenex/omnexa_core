# Copyright (c) 2026, ErpGenEx
"""Finance vertical BPE specs — workflow, roles, seed per app."""

from __future__ import annotations

VERTICAL_BPE_SPECS: dict[str, dict] = {
	"omnexa_finance_engine": {
		"brand": "FinanceCore",
		"case_doctype": "Finance Contract Account",
		"workflow_name": "FinanceCore Contract Lending",
		"prefix": "FE",
		"desk_role": "Finance Group Executive",
		"module": "Omnexa Finance Engine",
		"seed_label_field": "customer_name",
		"seed_prefix": "Demo FE",
		"lifecycle_field": "status",
		"lifecycle_disbursed": "ACTIVE",
		"lifecycle_closed": "CLOSED"
	},
	"omnexa_credit_engine": {
		"brand": "CreditPulse",
		"case_doctype": "Credit Decision Case",
		"workflow_name": "CreditPulse Decision Flow",
		"prefix": "CE",
		"desk_role": "Finance Credit Officer",
		"module": "Omnexa Credit Engine",
		"seed_label_field": "customer_name",
		"seed_prefix": "Demo CE",
		"lifecycle_field": "decision_status",
		"lifecycle_disbursed": "APPROVED",
		"lifecycle_closed": "APPROVED"
	},
	"omnexa_credit_risk": {
		"brand": "RiskGuard",
		"case_doctype": "Credit Risk Portfolio Stress Run",
		"workflow_name": "RiskGuard Stress Run",
		"prefix": "RK",
		"desk_role": "Finance Risk Analyst",
		"module": "Omnexa Credit Risk",
		"seed_label_field": "run_name",
		"seed_prefix": "Demo RK Stress"
	},
	"omnexa_alm": {
		"brand": "TreasuryALM",
		"case_doctype": "ALM Daily Run",
		"workflow_name": "TreasuryALM Daily Run",
		"prefix": "AL",
		"desk_role": "Finance Treasury Officer",
		"module": "Omnexa ALM",
		"seed_label_field": "run_reference",
		"seed_prefix": "DEMO-ALM",
		"lifecycle_field": "run_status",
		"lifecycle_disbursed": "SUCCESS",
		"lifecycle_closed": "SUCCESS"
	},
	"omnexa_consumer_finance": {
		"brand": "RetailLend",
		"case_doctype": "Consumer Finance Case",
		"workflow_name": "RetailLend Consumer Lending",
		"prefix": "CF",
		"desk_role": "Finance Consumer Officer",
		"module": "Omnexa Consumer Finance",
		"seed_label_field": "customer_name",
		"seed_prefix": "Demo CF",
		"lifecycle_field": "lifecycle_stage",
		"lifecycle_disbursed": "SERVICING",
		"lifecycle_closed": "SERVICING"
	},
	"omnexa_vehicle_finance": {
		"brand": "AutoLend",
		"case_doctype": "Vehicle Finance Case",
		"workflow_name": "AutoLend Vehicle Lending",
		"prefix": "VF",
		"desk_role": "Finance Auto Officer",
		"module": "Omnexa Vehicle Finance",
		"seed_label_field": "customer_name",
		"seed_prefix": "Demo VF",
		"lifecycle_field": "lifecycle_stage",
		"lifecycle_disbursed": "SERVICING",
		"lifecycle_closed": "SERVICING"
	},
	"omnexa_mortgage_finance": {
		"brand": "HomeLend",
		"case_doctype": "Mortgage Finance Case",
		"workflow_name": "HomeLend Mortgage Lending",
		"prefix": "MG",
		"desk_role": "Finance Mortgage Officer",
		"module": "Omnexa Mortgage Finance",
		"seed_label_field": "customer_name",
		"seed_prefix": "Demo MG",
		"lifecycle_field": "lifecycle_stage",
		"lifecycle_disbursed": "SERVICING",
		"lifecycle_closed": "SERVICING"
	},
	"omnexa_factoring": {
		"brand": "FactorFlow",
		"case_doctype": "Factoring Case",
		"workflow_name": "FactorFlow Invoice Lending",
		"prefix": "FC",
		"desk_role": "Finance Factoring Officer",
		"module": "Omnexa Factoring",
		"seed_label_field": "customer_name",
		"seed_prefix": "Demo FC",
		"lifecycle_field": "lifecycle_stage",
		"lifecycle_disbursed": "SERVICING",
		"lifecycle_closed": "SERVICING"
	},
	"omnexa_sme_retail_finance": {
		"brand": "SMECapital",
		"case_doctype": "SME Retail Finance Case",
		"workflow_name": "SMECapital SME Lending",
		"prefix": "SR",
		"desk_role": "Finance SME Officer",
		"module": "Omnexa SME Retail Finance",
		"seed_label_field": "customer_name",
		"seed_prefix": "Demo SR",
		"lifecycle_field": "lifecycle_stage",
		"lifecycle_disbursed": "SERVICING",
		"lifecycle_closed": "SERVICING"
	},
	"omnexa_leasing_finance": {
		"brand": "LeaseMaster",
		"case_doctype": "Leasing Finance Contract",
		"workflow_name": "LeaseMaster Contract Flow",
		"prefix": "LF",
		"desk_role": "Finance Leasing Officer",
		"module": "Omnexa Leasing Finance",
		"seed_label_field": "customer_name",
		"seed_prefix": "Demo LF",
		"lifecycle_field": "lifecycle_stage",
		"lifecycle_disbursed": "SERVICING",
		"lifecycle_closed": "SERVICING"
	},
	"omnexa_sme_microfinance": {
		"brand": "MicroCapital",
		"case_doctype": "Microfinance Case",
		"workflow_name": "MicroCapital Group Lending",
		"prefix": "MF",
		"desk_role": "Finance Microfinance Officer",
		"module": "Omnexa SME Microfinance",
		"seed_label_field": "group_name",
		"seed_prefix": "Demo Group",
		"lifecycle_field": "lifecycle_stage",
		"lifecycle_disbursed": "Disbursement",
		"lifecycle_closed": "Closed",
		"delegate_seed": "omnexa_sme_microfinance.mf_demo_seed.seed_microfinance_demo"
	},
	"omnexa_operational_risk": {
		"brand": "OpRisk",
		"case_doctype": "Operational Risk Incident",
		"workflow_name": "OpRisk Incident GRC",
		"prefix": "OR",
		"desk_role": "Finance GRC Officer",
		"module": "Omnexa Operational Risk",
		"seed_label_field": "incident_title",
		"seed_prefix": "Demo OR Incident",
		"lifecycle_field": "status",
		"lifecycle_disbursed": "ACTION_APPROVED",
		"lifecycle_closed": "CLOSED"
	},
	"omnexa_accounting": {
		"brand": "FinTruth",
		"case_doctype": "Journal Entry",
		"workflow_name": "FinTruth Stage Gate GL",
		"prefix": "AC",
		"desk_role": "Finance Accounting Controller",
		"module": "Omnexa Accounting",
		"seed_label_field": "title",
		"seed_prefix": "Demo FinTruth JE",
		"skip_seed": True,
		"standard_doctype": True}
	}

VERTICAL_BPE_APPS: list[str] = list(VERTICAL_BPE_SPECS.keys())

VERTICAL_BPE_DOCTYPES: list[str] = list({s["case_doctype"] for s in VERTICAL_BPE_SPECS.values()})


def get_spec(app: str) -> dict | None:
	return VERTICAL_BPE_SPECS.get(app)
