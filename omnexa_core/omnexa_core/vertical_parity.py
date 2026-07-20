# Copyright (c) 2026, ErpGenEx
"""Wave C — sector KPI previews vs SAP (no document mutation)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from frappe.utils import flt

VERTICALS = frozenset(
	{
		"hr",
		"manufacturing",
		"tourism",
		"trading",
		"healthcare",
		"education",
		"nursery",
		"restaurant",
		"services",
		"construction",
		"agriculture",
		"car_rental",
		"projects_pm",
		"customer_core",
		"experience",
		"accounting",
		"engineering_consulting",
		"fixed_assets",
		"statutory_audit",
		"property_mgmt",
		"realestate_dev",
		"realestate_sales",
		"maintenance_core",
		"operational_risk",
		"einvoice",
	}
)


def preview_for_vertical(vertical: str, scenario: str | None = None, **params: Any) -> dict[str, Any]:
	vertical = (vertical or "").strip().lower()
	if vertical not in VERTICALS:
		return {"vertical": vertical, "error": "unknown_vertical"
	}
	scenario = (scenario or "default").strip().lower()
	handler = _HANDLERS.get(vertical, _default_handler)
	return {"vertical": vertical, "scenario": scenario, **handler(scenario, params)}


def _default_handler(scenario: str, params: dict) -> dict:
	return {"kpi": {
	}, "note": "default_preview"
	}


def _hr(scenario: str, params: dict) -> dict:
	gross = flt(params.get("gross_pay") or 0)
	deductions = flt(params.get("deductions") or 0)
	net = gross - deductions
	if scenario == "leave_accrual":
		days = flt(params.get("leave_days") or 0)
		daily = gross / 30.0 if gross else 0
		accrual = flt(daily * days, 2)
		return {
			"kpi": {"leave_days": days, "accrual_amount": accrual, "daily_rate": flt(daily, 2)},
			"sap_module": "PA/PT"
	}
	if scenario == "payroll_run":
		return {
			"kpi": {
				"gross_pay": gross,
				"deductions": deductions,
				"net_pay": net,
				"employer_cost": flt(gross * 0.11, 2)},
			"sap_module": "PA/PY"
	}
	return {
		"kpi": {
			"gross_pay": gross,
			"deductions": deductions,
			"net_pay": net,
			"deduction_ratio": round(deductions / gross, 4) if gross else 0},
		"sap_module": "PA/PY"
	}


def _manufacturing(scenario: str, params: dict) -> dict:
	labor = flt(params.get("labor_cost") or 0)
	material = flt(params.get("material_cost") or 0)
	overhead = flt(params.get("overhead") or 0)
	total = labor + material + overhead
	return {
		"kpi": {"labor": labor, "material": material, "overhead": overhead, "work_order_cost": total
	},
		"sap_module": "PP"
	}


def _tourism(scenario: str, params: dict) -> dict:
	rooms = int(params.get("rooms_available") or 0)
	occupied = int(params.get("rooms_occupied") or 0)
	occ = round(occupied / rooms, 4) if rooms else 0
	adr = flt(params.get("average_daily_rate") or 0)
	revpar = round(adr * occ, 2)
	return {
		"kpi": {
			"occupancy_rate": occ,
			"rooms_available": rooms,
			"rooms_occupied": occupied,
			"revpar": revpar
	},
		"sap_module": "Hospitality"
	}


def _trading(scenario: str, params: dict) -> dict:
	lines = params.get("lines") or []
	if isinstance(lines, str):
		import json

		lines = json.loads(lines)
	total = sum(flt(r.get("amount")) for r in lines if isinstance(r, dict))
	return {"kpi": {"route_sales_total": total, "line_count": len(lines)
	}, "sap_module": "SD"
	}


def _healthcare(scenario: str, params: dict) -> dict:
	fees = flt(params.get("procedure_fees") or 0)
	copay = flt(params.get("patient_copay") or 0)
	return {"kpi": {"billable": fees, "copay": copay, "net_receivable": fees - copay
	}, "sap_module": "IS-H"
	}


def _education(scenario: str, params: dict) -> dict:
	students = int(params.get("student_count") or 0)
	fee = flt(params.get("fee_per_student") or 0)
	return {"kpi": {"total_fees": students * fee, "students": students
	}, "sap_module": "IS-HER"
	}


def _nursery(scenario: str, params: dict) -> dict:
	out = _education(scenario, params)
	out["sap_module"] = "Education/Nursery"
	return out


def _restaurant(scenario: str, params: dict) -> dict:
	revenue = flt(params.get("revenue") or 0)
	cogs = flt(params.get("cogs") or 0)
	margin = revenue - cogs
	return {
		"kpi": {"revenue": revenue, "cogs": cogs, "gross_margin": margin, "margin_pct": round(margin / revenue, 4) if revenue else 0},
		"sap_module": "Retail"
	}


def _services(scenario: str, params: dict) -> dict:
	target = flt(params.get("sla_hours") or 24)
	elapsed = flt(params.get("elapsed_hours") or 0)
	return {
		"kpi": {"sla_hours": target, "elapsed_hours": elapsed, "breached": elapsed > target
	},
		"sap_module": "CS"
	}


def _construction(scenario: str, params: dict) -> dict:
	pct = flt(params.get("completed_percent") or 0) / 100.0
	contract = flt(params.get("contract_value") or 0)
	ipc = round(contract * pct, 2)
	return {"kpi": {"ipc_amount": ipc, "completed_percent": pct * 100
	}, "sap_module": "PS/E&C"
	}


def _agriculture(scenario: str, params: dict) -> dict:
	estimated = flt(params.get("estimated_yield") or 0)
	actual = flt(params.get("actual_yield") or 0)
	variance = actual - estimated
	return {"kpi": {"estimated": estimated, "actual": actual, "variance": variance
	}, "sap_module": "LO-AGR"
	}


def _car_rental(scenario: str, params: dict) -> dict:
	fleet = int(params.get("fleet_size") or 0)
	rented = int(params.get("rented_units") or 0)
	util = round(rented / fleet, 4) if fleet else 0
	return {"kpi": {"fleet_size": fleet, "rented": rented, "utilization": util
	}, "sap_module": "TM"
	}


def _projects_pm(scenario: str, params: dict) -> dict:
	pv = flt(params.get("planned_value") or 0)
	ev = flt(params.get("earned_value") or 0)
	ac = flt(params.get("actual_cost") or 1) or 1
	spi = round(ev / pv, 4) if pv else 0
	cpi = round(ev / ac, 4)
	return {"kpi": {"spi": spi, "cpi": cpi, "pv": pv, "ev": ev, "ac": ac
	}, "sap_module": "PS"
	}


def _customer_core(scenario: str, params: dict) -> dict:
	stages = params.get("stages") or []
	if isinstance(stages, str):
		import json

		stages = json.loads(stages)
	weighted = sum(flt(s.get("amount")) * flt(s.get("probability", 1)) for s in stages if isinstance(s, dict))
	return {"kpi": {"weighted_pipeline": weighted, "stage_count": len(stages)
	}, "sap_module": "CRM"
	}


def _experience(scenario: str, params: dict) -> dict:
	items = params.get("items") or []
	if isinstance(items, str):
		import json

		items = json.loads(items)
	total = sum(flt(i.get("amount")) for i in items if isinstance(i, dict))
	return {"kpi": {"checkout_total": total, "item_count": len(items)
	}, "sap_module": "CX"
	}


def _accounting(scenario: str, params: dict) -> dict:
	debit = flt(params.get("debit_total") or 0)
	credit = flt(params.get("credit_total") or 0)
	balanced = abs(debit - credit) < 0.01
	return {
		"kpi": {"debit_total": debit, "credit_total": credit, "balanced": balanced
	},
		"sap_module": "FI"
	}


def _engineering_consulting(scenario: str, params: dict) -> dict:
	out = _projects_pm(scenario, params)
	out["sap_module"] = "PS/ENG"
	return out


def _fixed_assets(scenario: str, params: dict) -> dict:
	cost = flt(params.get("asset_cost") or 0)
	nbv = flt(params.get("net_book_value") or cost)
	dep = flt(params.get("annual_depreciation") or 0)
	return {
		"kpi": {"asset_cost": cost, "net_book_value": nbv, "annual_depreciation": dep
	},
		"sap_module": "FI-AA"
	}


def _statutory_audit(scenario: str, params: dict) -> dict:
	findings = int(params.get("open_findings") or 0)
	evidence = int(params.get("evidence_count") or 0)
	return {
		"kpi": {"open_findings": findings, "evidence_count": evidence, "coverage_pct": 1.0 if evidence else 0
	},
		"sap_module": "GRC/Audit"
	}


_HANDLERS = {
	"hr": _hr,
	"manufacturing": _manufacturing,
	"tourism": _tourism,
	"trading": _trading,
	"healthcare": _healthcare,
	"education": _education,
	"nursery": _nursery,
	"restaurant": _restaurant,
	"services": _services,
	"construction": _construction,
	"agriculture": _agriculture,
	"car_rental": _car_rental,
	"projects_pm": _projects_pm,
	"customer_core": _customer_core,
	"experience": _experience,
	"accounting": _accounting,
	"engineering_consulting": _engineering_consulting,
	"fixed_assets": _fixed_assets,
	"statutory_audit": _statutory_audit
	}
