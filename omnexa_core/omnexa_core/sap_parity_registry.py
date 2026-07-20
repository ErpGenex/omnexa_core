# Copyright (c) 2026, ErpGenEx
"""Registry of SAP parity families and checklist scoring (100% target)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

BENCH = Path(__file__).resolve().parents[4]

# app → (family, vertical_key for preview APIs)
APP_REGISTRY: dict[str, dict[str, str]] = {
	"omnexa_accounting": {"family": "fi", "vertical": ""
	},
	"omnexa_engineering_consulting": {"family": "ps_eng", "vertical": ""
	},
	"omnexa_core": {"family": "btp", "vertical": ""
	},
	"omnexa_fixed_assets": {"family": "fi_aa", "vertical": ""
	},
	"omnexa_leasing_finance": {"family": "fs", "vertical": "leasing"
	},
	"omnexa_einvoice": {"family": "einvoice", "vertical": ""
	},
	"omnexa_finance_engine": {"family": "fs_engine", "vertical": ""
	},
	"omnexa_mortgage_finance": {"family": "fs", "vertical": "mortgage"
	},
	"omnexa_vehicle_finance": {"family": "fs", "vertical": "vehicle"
	},
	"omnexa_consumer_finance": {"family": "fs", "vertical": "consumer"
	},
	"omnexa_sme_retail_finance": {"family": "fs", "vertical": "sme_retail"
	},
	"omnexa_factoring": {"family": "fs", "vertical": "factoring"
	},
	"omnexa_credit_engine": {"family": "fs", "vertical": "credit_engine"
	},
	"omnexa_credit_risk": {"family": "fs", "vertical": "credit_risk"
	},
	"omnexa_alm": {"family": "fs", "vertical": "alm"
	},
	"omnexa_operational_risk": {"family": "grc", "vertical": "operational_risk"
	},
	"omnexa_statutory_audit": {"family": "grc", "vertical": "statutory_audit"
	},
	"omnexa_reporting_compliance": {"family": "grc", "vertical": "reporting_compliance"
	},
	"erpgenex_property_mgmt": {"family": "re_fx", "vertical": ""
	},
	"erpgenex_realestate_dev": {"family": "re_dev", "vertical": ""
	},
	"erpgenex_realestate_sales": {"family": "re_sales", "vertical": ""
	},
	"erpgenex_maintenance_core": {"family": "pm", "vertical": ""
	},
	"omnexa_hr": {"family": "sector", "vertical": "hr"
	},
	"omnexa_manufacturing": {"family": "sector", "vertical": "manufacturing"
	},
	"omnexa_tourism": {"family": "sector", "vertical": "tourism"
	},
	"omnexa_trading": {"family": "sector", "vertical": "trading"
	},
	"omnexa_healthcare": {"family": "sector", "vertical": "healthcare"
	},
	"omnexa_education": {"family": "sector", "vertical": "education"
	},
	"omnexa_nursery": {"family": "sector", "vertical": "nursery"
	},
	"omnexa_restaurant": {"family": "sector", "vertical": "restaurant"
	},
	"omnexa_services": {"family": "sector", "vertical": "services"
	},
	"omnexa_construction": {"family": "sector", "vertical": "construction"
	},
	"omnexa_agriculture": {"family": "sector", "vertical": "agriculture"
	},
	"omnexa_car_rental": {"family": "sector", "vertical": "car_rental"
	},
	"omnexa_projects_pm": {"family": "sector", "vertical": "projects_pm"
	},
	"omnexa_customer_core": {"family": "sector", "vertical": "customer_core"
	},
	"omnexa_experience": {"family": "sector", "vertical": "experience"
	},
	"omnexa_eng_document_control": {"family": "infra", "vertical": "eng_document_control"
	},
	"omnexa_eng_workflow_engine": {"family": "infra", "vertical": "eng_workflow_engine"
	},
	"omnexa_eng_platform_integrations": {"family": "infra", "vertical": "eng_platform_integrations"
	},
	"omnexa_n8n_bridge": {"family": "infra", "vertical": "n8n_bridge"
	},
	"omnexa_intelligence_core": {"family": "infra", "vertical": "intelligence_core"
	},
	"omnexa_setup_intelligence": {"family": "infra", "vertical": "setup_intelligence"
	},
	"omnexa_backup": {"family": "infra", "vertical": "backup"
	},
	"omnexa_user_academy": {"family": "infra", "vertical": "user_academy"
	},
	"omnexa_theme_manager": {"family": "infra", "vertical": "theme_manager"
	},
	"erpgenex_theme_0426": {"family": "infra", "vertical": "erpgenex_theme_0426"
	},
	"omnexa_edms": {"family": "infra", "vertical": "edms"
	},
	"omnexa_sme_microfinance": {"family": "fs", "vertical": "sme_microfinance"
	},
	"omnexa_ai_employee": {"family": "infra", "vertical": "ai_employee"}
	}


def parse_checklist_score(md_text: str) -> dict[str, Any]:
	"""Parse Implemented / N/A / Planned / Partial from checklist markdown."""
	rows = re.findall(r"\|\s*\d+\s*\|[^|]+\|\s*([^|]+)\s*\|", md_text)
	if not rows:
		return {"score_pct": 0, "implemented": 0, "applicable": 0
	}
	statuses = [s.strip() for s in rows]
	applicable = [s for s in statuses if s.upper() != "N/A"]
	implemented = sum(
		1 for s in applicable if s.lower().startswith("implemented")
	)
	partial = sum(1 for s in applicable if "partial" in s.lower())
	score = round(100 * (implemented + 0.5 * partial) / len(applicable), 1) if applicable else 0
	product = min(100, score)
	return {
		"score_pct": score,
		"product_pct": product,
		"implemented": implemented,
		"partial": partial,
		"planned": sum(1 for s in applicable if "planned" in s.lower()),
		"applicable": len(applicable),
		"at_100": product >= 100,
		"at_95": product >= 95,  # legacy alias
	}


def checklist_path(app: str) -> Path | None:
	matches = list((BENCH / "apps" / app).glob("docs/SAP_PARITY_CHECKLIST.md"))
	return matches[0] if matches else None


def get_app_parity_status(app: str) -> dict[str, Any]:
	meta = APP_REGISTRY.get(app, {"family": "sector", "vertical": app.replace("omnexa_", "")})
	path = checklist_path(app)
	if not path:
		return {"app": app, "error": "no_checklist", "at_100": False, "at_95": False, **meta}
	parsed = parse_checklist_score(path.read_text(encoding="utf-8"))
	return {"app": app, **meta, **parsed}
