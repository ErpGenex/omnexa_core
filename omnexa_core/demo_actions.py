# -*- coding: utf-8 -*-
"""
Demo Action Registrations
All demo actions register themselves with the Demo Registry.

This file contains the registration decorators for all existing demo actions.
"""

import frappe
from omnexa_core.demo_registry import (
    DemoRegistry,
    RiskLevel,
    ExecutionMode
)


def register_branch_masters_demo():
    """Register Branch Masters Demo action"""
    @DemoRegistry.register(
        key="branch_masters_demo",
        title="Seed Demo Data (Masters)",
        description="Creates master records only including items, customers, suppliers, employees, and basic setup data.",
        category="Branch",
        estimated_time="20 Seconds",
        estimated_records=1250,
        required_modules=["omnexa_core"],
        risk_level=RiskLevel.LOW,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.UPDATE_EXISTING,
            ExecutionMode.REPLACE_ALL
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-database",
        color="green",
        permissions=["System Manager", "Administrator"],
        business_impact="Creates foundational master data for branch operations",
        rollback_available=True
    )
    def branch_masters_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Branch Masters Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_seed_masters()
    
    return branch_masters_demo_handler


def register_branch_transactions_demo():
    """Register Branch Masters + Transactions Demo action"""
    @DemoRegistry.register(
        key="branch_transactions_demo",
        title="Seed Demo Data + Transactions",
        description="Creates master records plus aligned sales and purchase transaction chains with stock entries.",
        category="Branch",
        estimated_time="45 Seconds",
        estimated_records=3500,
        required_modules=["omnexa_core"],
        risk_level=RiskLevel.MEDIUM,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.UPDATE_EXISTING,
            ExecutionMode.REPLACE_ALL
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-exchange-alt",
        color="blue",
        permissions=["System Manager", "Administrator"],
        business_impact="Creates complete business simulation with transactions",
        rollback_available=True
    )
    def branch_transactions_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Branch Transactions Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_seed_with_tx()
    
    return branch_transactions_demo_handler


def register_business_simulation_6m_demo():
    """Register 6-Month Business Simulation Demo action"""
    @DemoRegistry.register(
        key="business_simulation_6m",
        title="6-Month Full Business Simulation",
        description="Generates 6 months of realistic business operations including daily transactions, stock movements, and financial entries.",
        category="Business Simulation",
        estimated_time="3 Minutes",
        estimated_records=25000,
        required_modules=["omnexa_core"],
        risk_level=RiskLevel.MEDIUM,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.REPLACE_ALL,
            ExecutionMode.RESET_ENVIRONMENT
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-chart-line",
        color="orange",
        permissions=["System Manager", "Administrator"],
        warnings=["This will create a large volume of data"],
        business_impact="Creates comprehensive 6-month business simulation",
        rollback_available=True
    )
    def business_simulation_6m_handler(execution_mode: str, context: dict) -> dict:
        """Handler for 6-Month Business Simulation"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_seed_6m()
    
    return business_simulation_6m_handler


def register_business_simulation_12m_demo():
    """Register 12-Month Business Simulation Demo action"""
    @DemoRegistry.register(
        key="business_simulation_12m",
        title="12-Month Full Business Simulation",
        description="Generates 12 months of realistic business operations with comprehensive financial reporting and analytics.",
        category="Business Simulation",
        estimated_time="6 Minutes",
        estimated_records=50000,
        required_modules=["omnexa_core"],
        risk_level=RiskLevel.HIGH,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.REPLACE_ALL,
            ExecutionMode.RESET_ENVIRONMENT
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-chart-area",
        color="red",
        permissions=["System Manager", "Administrator"],
        warnings=["This will create a very large volume of data", "Long execution time"],
        business_impact="Creates comprehensive 12-month business simulation with full year reporting",
        rollback_available=True
    )
    def business_simulation_12m_handler(execution_mode: str, context: dict) -> dict:
        """Handler for 12-Month Business Simulation"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_seed_12m()
    
    return business_simulation_12m_handler


def register_construction_portfolio_demo():
    """Register Construction Portfolio Demo action"""
    @DemoRegistry.register(
        key="construction_portfolio_demo",
        title="Construction Portfolio Demo",
        description="Creates 20 construction projects with full portfolio including budgets, progress tracking, and resource allocation.",
        category="Construction",
        estimated_time="2 Minutes",
        estimated_records=8000,
        required_modules=["omnexa_construction"],
        risk_level=RiskLevel.MEDIUM,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.REPLACE_ALL
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-hard-hat",
        color="yellow",
        permissions=["System Manager", "Administrator", "Construction Manager"],
        business_impact="Creates complete construction project portfolio",
        rollback_available=True
    )
    def construction_portfolio_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Construction Portfolio Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_construction_portfolio()
    
    return construction_portfolio_demo_handler


def register_healthcare_masters_demo():
    """Register Healthcare Masters Demo action"""
    @DemoRegistry.register(
        key="healthcare_masters_demo",
        title="Healthcare Masters Demo",
        description="Creates healthcare master data including specialties, procedures, equipment, and medical templates.",
        category="Healthcare",
        estimated_time="30 Seconds",
        estimated_records=500,
        required_modules=["omnexa_healthcare"],
        risk_level=RiskLevel.LOW,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.UPDATE_EXISTING,
            ExecutionMode.REPLACE_ALL
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-stethoscope",
        color="teal",
        permissions=["System Manager", "Administrator", "Healthcare Administrator"],
        business_impact="Creates foundational healthcare master data",
        rollback_available=True
    )
    def healthcare_masters_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Healthcare Masters Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_healthcare_masters()
    
    return healthcare_masters_demo_handler


def register_healthcare_procedures_consumables_demo():
    """Register Healthcare Procedures & Consumables Demo action"""
    @DemoRegistry.register(
        key="healthcare_procedures_consumables_demo",
        title="Healthcare Procedures & Consumables Demo",
        description="Creates medical procedures with associated consumables, pricing, and inventory templates.",
        category="Healthcare",
        estimated_time="25 Seconds",
        estimated_records=350,
        required_modules=["omnexa_healthcare"],
        risk_level=RiskLevel.LOW,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.UPDATE_EXISTING,
            ExecutionMode.REPLACE_ALL
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-notes-medical",
        color="cyan",
        permissions=["System Manager", "Administrator", "Healthcare Administrator"],
        business_impact="Creates procedures and consumables for medical operations",
        rollback_available=True
    )
    def healthcare_procedures_consumables_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Healthcare Procedures & Consumables Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_healthcare_procedures_consumables()
    
    return healthcare_procedures_consumables_demo_handler


def register_healthcare_hospital_demo():
    """Register Healthcare Hospital Demo action"""
    @DemoRegistry.register(
        key="healthcare_hospital_demo",
        title="Healthcare Hospital Demo",
        description="Creates comprehensive hospital simulation with 20 patients, appointments, medical records, and web bookings.",
        category="Healthcare",
        estimated_time="2 Minutes",
        estimated_records=3000,
        required_modules=["omnexa_healthcare"],
        risk_level=RiskLevel.MEDIUM,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.REPLACE_ALL,
            ExecutionMode.RESET_ENVIRONMENT
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-hospital",
        color="purple",
        permissions=["System Manager", "Administrator", "Healthcare Administrator"],
        warnings=["Creates patient medical records with sensitive data"],
        business_impact="Creates complete hospital operations simulation",
        rollback_available=True
    )
    def healthcare_hospital_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Healthcare Hospital Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_healthcare_hospital()
    
    return healthcare_hospital_demo_handler


def register_finance_group_demo():
    """Register Finance Group Demo action"""
    @DemoRegistry.register(
        key="finance_group_demo",
        title="Finance Group Demo",
        description="Creates 50 finance clients across all installed finance applications with complete loan portfolios.",
        category="Finance",
        estimated_time="3 Minutes",
        estimated_records=10000,
        required_modules=["omnexa_finance_engine", "omnexa_sme_retail_finance"],
        risk_level=RiskLevel.HIGH,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.REPLACE_ALL,
            ExecutionMode.RESET_ENVIRONMENT
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-university",
        color="indigo",
        permissions=["System Manager", "Administrator", "Finance Manager"],
        warnings=["Requires multiple finance modules", "Creates sensitive financial data"],
        business_impact="Creates comprehensive finance group simulation",
        rollback_available=True
    )
    def finance_group_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Finance Group Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_finance_group()
    
    return finance_group_demo_handler


def register_education_demo():
    """Register Education Demo action"""
    @DemoRegistry.register(
        key="education_demo",
        title="EduSphere Education Demo",
        description="Creates 5 types of educational institutions with 8 role portal accounts and complete academic setup.",
        category="Education",
        estimated_time="2 Minutes",
        estimated_records=5000,
        required_modules=["omnexa_education"],
        risk_level=RiskLevel.MEDIUM,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.REPLACE_ALL,
            ExecutionMode.RESET_ENVIRONMENT
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-graduation-cap",
        color="pink",
        permissions=["System Manager", "Administrator", "Education Administrator"],
        warnings=["Creates user accounts for 8 different roles"],
        business_impact="Creates complete education institution simulation",
        rollback_available=True
    )
    def education_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Education Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_education()
    
    return education_demo_handler


def register_hotel_assets_demo():
    """Register Hotel Assets Demo action"""
    @DemoRegistry.register(
        key="hotel_assets_demo",
        title="Hotel Assets Demo",
        description="Creates 50 hotel assets including rooms, administrative areas, and asset movements.",
        category="Hotel",
        estimated_time="1 Minute",
        estimated_records=2000,
        required_modules=["omnexa_tourism"],
        risk_level=RiskLevel.LOW,
        execution_modes=[
            ExecutionMode.CREATE_MISSING,
            ExecutionMode.REPLACE_ALL
        ],
        default_execution_mode=ExecutionMode.CREATE_MISSING,
        icon="fa-hotel",
        color="amber",
        permissions=["System Manager", "Administrator", "Hotel Manager"],
        business_impact="Creates hotel asset management simulation",
        rollback_available=True
    )
    def hotel_assets_demo_handler(execution_mode: str, context: dict) -> dict:
        """Handler for Hotel Assets Demo"""
        import frappe
        from omnexa_core.omnexa_core.doctype.branch.branch import Branch
        branch = frappe.get_doc("Branch", context.get("branch"))
        return branch.branch_demo_action_hotel_assets()
    
    return hotel_assets_demo_handler


# Register all demo actions on module load
register_branch_masters_demo()
register_branch_transactions_demo()
register_business_simulation_6m_demo()
register_business_simulation_12m_demo()
register_construction_portfolio_demo()
register_healthcare_masters_demo()
register_healthcare_procedures_consumables_demo()
register_healthcare_hospital_demo()
register_finance_group_demo()
register_education_demo()
register_hotel_assets_demo()
