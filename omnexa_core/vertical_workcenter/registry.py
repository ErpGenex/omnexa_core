# Copyright (c) 2026, ErpGenEx
"""SSOT — vertical apps workcenter rollout registry."""

from __future__ import annotations

# status: complete | partial | planned | finance_group
VERTICAL_WORKCENTER_REGISTRY: list[dict] = [
	{"app": "omnexa_education", "slug": "education", "title_en": "EduSphere", "title_ar": "EduSphere — التعليم", "workcenter": "education-workcenter", "status": "complete", "tier": 1, "reference": True
	},
	{"app": "omnexa_healthcare", "slug": "healthcare", "title_en": "Healthcare", "title_ar": "الرعاية الصحية", "workcenter": "healthcare-workcenter", "status": "complete", "tier": 1, "reference": True
	},
	{"app": "omnexa_core", "slug": "finance", "title_en": "Finance Group", "title_ar": "المجموعة المالية", "workcenter": "finance-workcenter", "status": "complete", "tier": 1, "reference": True
	},
	{"app": "omnexa_tourism", "slug": "tourism", "title_en": "Tourism", "title_ar": "السياحة", "workcenter": "tourism-workcenter", "status": "partial", "tier": 1, "portals": "default"
	},
	{"app": "omnexa_construction", "slug": "construction", "title_en": "Construction", "title_ar": "المقاولات", "workcenter": "construction-workcenter", "status": "partial", "tier": 1, "portals": "default"
	},
	{"app": "omnexa_manufacturing", "slug": "manufacturing", "title_en": "Manufacturing", "title_ar": "التصنيع", "workcenter": "manufacturing-workcenter", "status": "partial", "tier": 1, "portals": "default"
	},
	{"app": "omnexa_trading", "slug": "trading", "title_en": "Trading", "title_ar": "التجارة", "workcenter": "trading-workcenter", "status": "complete", "tier": 1, "portals": "pharma", "reference": True
	},
	{"app": "omnexa_agriculture", "slug": "agriculture", "title_en": "Agriculture", "title_ar": "الزراعة", "workcenter": "agriculture-workcenter", "status": "partial", "tier": 1, "portals": "default"
	},
	{"app": "omnexa_hr", "slug": "hr", "title_en": "Human Resources", "title_ar": "الموارد البشرية", "workcenter": "hr-workcenter", "status": "partial", "tier": 1, "portals": "default"
	},
	{"app": "omnexa_restaurant", "slug": "restaurant", "title_en": "Restaurant", "title_ar": "المطاعم", "workcenter": "restaurant-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "omnexa_services", "slug": "services", "title_en": "Services", "title_ar": "الخدمات", "workcenter": "services-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "omnexa_car_rental", "slug": "car-rental", "title_en": "Car Rental", "title_ar": "تأجير السيارات", "workcenter": "car-rental-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "omnexa_nursery", "slug": "nursery", "title_en": "Nursery", "title_ar": "الحضانة", "workcenter": "nursery-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "omnexa_fixed_assets", "slug": "fixed-assets", "title_en": "Fixed Assets", "title_ar": "الأصول الثابتة", "workcenter": "fixed-assets-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "omnexa_engineering_consulting", "slug": "engineering-consulting", "title_en": "Engineering Consulting", "title_ar": "الاستشارات الهندسية", "workcenter": "engineering-consulting-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "omnexa_projects_pm", "slug": "projects-pm", "title_en": "Projects PM", "title_ar": "إدارة المشاريع", "workcenter": "projects-pm-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "omnexa_statutory_audit", "slug": "statutory-audit", "title_en": "Statutory Audit", "title_ar": "المراجعة القانونية", "workcenter": "statutory-audit-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "erpgenex_property_mgmt", "slug": "property-mgmt", "title_en": "Property Management", "title_ar": "إدارة العقارات", "workcenter": "property-mgmt-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "erpgenex_realestate_dev", "slug": "realestate-dev", "title_en": "RE Development", "title_ar": "التطوير العقاري", "workcenter": "realestate-dev-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "erpgenex_realestate_sales", "slug": "realestate-sales", "title_en": "RE Marketing", "title_ar": "التسويق العقاري", "workcenter": "realestate-sales-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "erpgenex_maintenance_core", "slug": "maintenance-core", "title_en": "Maintenance", "title_ar": "الصيانة", "workcenter": "maintenance-core-workcenter", "status": "partial", "tier": 2, "portals": "default"
	},
	{"app": "erpgenex_legal", "slug": "legal", "title_en": "Legal", "title_ar": "القانون", "workcenter": "legal-workcenter", "status": "complete", "tier": 2, "portals": "legal", "reference": True
	},
	{"app": "omnexa_finance_engine", "slug": "finance-engine", "title_en": "Finance Engine", "title_ar": "محرك التمويل", "workcenter": "finance-workcenter", "status": "finance_group", "tier": 3
	},
	{"app": "omnexa_accounting", "slug": "accounting", "title_en": "Accounting", "title_ar": "المحاسبة", "workcenter": "finance-workcenter", "status": "finance_group", "tier": 3
	},
]

# Platform / finance / infrastructure apps — not full vertical workcenters but registered for audit.
INFRASTRUCTURE_APP_REGISTRY: list[dict] = [
	{"app": "erpgenex_theme_0426", "category": "theme", "status": "infrastructure"},
	{"app": "omnexa_backup", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_customer_core", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_einvoice", "category": "compliance", "status": "infrastructure"},
	{"app": "omnexa_experience", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_setup_intelligence", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_intelligence_core", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_eng_document_control", "category": "engineering", "status": "infrastructure"},
	{"app": "omnexa_eng_platform_integrations", "category": "engineering", "status": "infrastructure"},
	{"app": "omnexa_eng_workflow_engine", "category": "engineering", "status": "infrastructure"},
	{"app": "omnexa_reporting_compliance", "category": "compliance", "status": "infrastructure"},
	{"app": "omnexa_theme_manager", "category": "theme", "status": "infrastructure"},
	{"app": "omnexa_user_academy", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_n8n_bridge", "category": "integration", "status": "infrastructure"},
	{"app": "erpgenex_saas", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_ai_employee", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_alm", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_consumer_finance", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_credit_engine", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_credit_risk", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_edms", "category": "platform", "status": "infrastructure"},
	{"app": "omnexa_factoring", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_leasing_finance", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_mortgage_finance", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_operational_risk", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_sme_microfinance", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_sme_retail_finance", "category": "finance", "status": "finance_group"},
	{"app": "omnexa_vehicle_finance", "category": "finance", "status": "finance_group"},
	{"app": "erpgenex_demo_studio", "category": "platform", "status": "infrastructure"},
]


def get_registry_entry(app: str) -> dict | None:
	for row in VERTICAL_WORKCENTER_REGISTRY:
		if row["app"] == app:
			return row
	return None


def get_infrastructure_entry(app: str) -> dict | None:
	for row in INFRASTRUCTURE_APP_REGISTRY:
		if row["app"] == app:
			return row
	return None


def get_any_registry_entry(app: str) -> dict | None:
	return get_registry_entry(app) or get_infrastructure_entry(app)


def list_by_tier(tier: int) -> list[dict]:
	return [r for r in VERTICAL_WORKCENTER_REGISTRY if r.get("tier") == tier]
