# Copyright (c) 2026, ErpGenEx
"""SSOT — vertical apps workcenter rollout registry."""

from __future__ import annotations

# status: complete | partial | planned | finance_group
VERTICAL_WORKCENTER_REGISTRY: list[dict] = [
	{"app": "omnexa_education", "slug": "education", "title_en": "EduSphere", "title_ar": "EduSphere — التعليم", "workcenter": "education-workcenter", "status": "complete", "tier": 1, "reference": True},
	{"app": "omnexa_healthcare", "slug": "healthcare", "title_en": "Healthcare", "title_ar": "الرعاية الصحية", "workcenter": "healthcare-workcenter", "status": "complete", "tier": 1, "reference": True},
	{"app": "omnexa_core", "slug": "finance", "title_en": "Finance Group", "title_ar": "المجموعة المالية", "workcenter": "finance-workcenter", "status": "complete", "tier": 1, "reference": True},
	{"app": "omnexa_tourism", "slug": "tourism", "title_en": "Tourism", "title_ar": "السياحة", "workcenter": "tourism-workcenter", "status": "partial", "tier": 1},
	{"app": "omnexa_construction", "slug": "construction", "title_en": "Construction", "title_ar": "المقاولات", "workcenter": "construction-workcenter", "status": "partial", "tier": 1},
	{"app": "omnexa_manufacturing", "slug": "manufacturing", "title_en": "Manufacturing", "title_ar": "التصنيع", "workcenter": "manufacturing-workcenter", "status": "partial", "tier": 1},
	{"app": "omnexa_trading", "slug": "trading", "title_en": "Trading", "title_ar": "التجارة", "workcenter": "trading-workcenter", "status": "partial", "tier": 1},
	{"app": "omnexa_agriculture", "slug": "agriculture", "title_en": "Agriculture", "title_ar": "الزراعة", "workcenter": "agriculture-workcenter", "status": "partial", "tier": 1},
	{"app": "omnexa_hr", "slug": "hr", "title_en": "Human Resources", "title_ar": "الموارد البشرية", "workcenter": "hr-workcenter", "status": "partial", "tier": 1},
	{"app": "omnexa_restaurant", "slug": "restaurant", "title_en": "Restaurant", "title_ar": "المطاعم", "workcenter": "restaurant-workcenter", "status": "planned", "tier": 2},
	{"app": "omnexa_services", "slug": "services", "title_en": "Services", "title_ar": "الخدمات", "workcenter": "services-workcenter", "status": "planned", "tier": 2},
	{"app": "omnexa_car_rental", "slug": "car-rental", "title_en": "Car Rental", "title_ar": "تأجير السيارات", "workcenter": "car-rental-workcenter", "status": "planned", "tier": 2},
	{"app": "omnexa_nursery", "slug": "nursery", "title_en": "Nursery", "title_ar": "الحضانة", "workcenter": "nursery-workcenter", "status": "planned", "tier": 2},
	{"app": "omnexa_fixed_assets", "slug": "fixed-assets", "title_en": "Fixed Assets", "title_ar": "الأصول الثابتة", "workcenter": "fixed-assets-workcenter", "status": "planned", "tier": 2},
	{"app": "omnexa_engineering_consulting", "slug": "engineering-consulting", "title_en": "Engineering Consulting", "title_ar": "الاستشارات الهندسية", "workcenter": "engineering-consulting-workcenter", "status": "planned", "tier": 2},
	{"app": "omnexa_projects_pm", "slug": "projects-pm", "title_en": "Projects PM", "title_ar": "إدارة المشاريع", "workcenter": "projects-pm-workcenter", "status": "planned", "tier": 2},
	{"app": "omnexa_statutory_audit", "slug": "statutory-audit", "title_en": "Statutory Audit", "title_ar": "المراجعة القانونية", "workcenter": "statutory-audit-workcenter", "status": "planned", "tier": 2},
	{"app": "erpgenex_property_mgmt", "slug": "property-mgmt", "title_en": "Property Management", "title_ar": "إدارة العقارات", "workcenter": "property-mgmt-workcenter", "status": "planned", "tier": 2},
	{"app": "erpgenex_realestate_dev", "slug": "realestate-dev", "title_en": "RE Development", "title_ar": "التطوير العقاري", "workcenter": "realestate-dev-workcenter", "status": "planned", "tier": 2},
	{"app": "erpgenex_realestate_sales", "slug": "realestate-sales", "title_en": "RE Marketing", "title_ar": "التسويق العقاري", "workcenter": "realestate-sales-workcenter", "status": "planned", "tier": 2},
	{"app": "erpgenex_maintenance_core", "slug": "maintenance-core", "title_en": "Maintenance", "title_ar": "الصيانة", "workcenter": "maintenance-core-workcenter", "status": "planned", "tier": 2},
	{"app": "omnexa_finance_engine", "slug": "finance-engine", "title_en": "Finance Engine", "title_ar": "محرك التمويل", "workcenter": "finance-workcenter", "status": "finance_group", "tier": 3},
	{"app": "omnexa_accounting", "slug": "accounting", "title_en": "Accounting", "title_ar": "المحاسبة", "workcenter": "finance-workcenter", "status": "finance_group", "tier": 3},
]


def get_registry_entry(app: str) -> dict | None:
	for row in VERTICAL_WORKCENTER_REGISTRY:
		if row["app"] == app:
			return row
	return None


def list_by_tier(tier: int) -> list[dict]:
	return [r for r in VERTICAL_WORKCENTER_REGISTRY if r.get("tier") == tier]
