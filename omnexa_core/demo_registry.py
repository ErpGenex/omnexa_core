# -*- coding: utf-8 -*-
"""
Demo Registry System
Centralized registry for all demo actions in the system.

This registry provides a scalable, maintainable way to manage demo actions
without requiring UI changes for each new demo.
"""

import frappe
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk levels for demo actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionMode(Enum):
    """Execution modes for demo actions"""
    CREATE_MISSING = "create_missing"
    UPDATE_EXISTING = "update_existing"
    REPLACE_ALL = "replace_all"
    RESET_ENVIRONMENT = "reset_environment"
    APPEND_DATA = "append_data"


@dataclass
class DemoActionMetadata:
    """Metadata for a demo action"""
    key: str
    title: str
    description: str
    category: str
    estimated_time: str  # e.g., "20 Seconds", "2 Minutes"
    estimated_records: int
    required_modules: List[str]
    risk_level: RiskLevel
    execution_modes: List[ExecutionMode]
    default_execution_mode: ExecutionMode
    icon: str
    color: str
    enabled: bool = True
    permissions: List[str] = None
    dependencies: List[str] = None
    warnings: List[str] = None
    business_impact: str = ""
    rollback_available: bool = True
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ["System Manager", "Administrator"]
        if self.dependencies is None:
            self.dependencies = []
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "estimated_time": self.estimated_time,
            "estimated_records": self.estimated_records,
            "required_modules": self.required_modules,
            "risk_level": self.risk_level.value,
            "execution_modes": [mode.value for mode in self.execution_modes],
            "default_execution_mode": self.default_execution_mode.value,
            "icon": self.icon,
            "color": self.color,
            "enabled": self.enabled,
            "permissions": self.permissions,
            "dependencies": self.dependencies,
            "warnings": self.warnings,
            "business_impact": self.business_impact,
            "rollback_available": self.rollback_available
        }


class DemoRegistry:
    """
    Central registry for all demo actions.
    
    Demo actions register themselves with metadata, and the registry
    provides methods to retrieve and execute them.
    """
    
    _registry: Dict[str, DemoActionMetadata] = {}
    _handlers: Dict[str, Callable] = {}
    
    @classmethod
    def register(
        cls,
        key: str,
        title: str,
        description: str,
        category: str,
        estimated_time: str,
        estimated_records: int,
        required_modules: List[str],
        risk_level: RiskLevel,
        execution_modes: List[ExecutionMode],
        default_execution_mode: ExecutionMode,
        icon: str = "fa-play",
        color: str = "blue",
        enabled: bool = True,
        permissions: List[str] = None,
        dependencies: List[str] = None,
        warnings: List[str] = None,
        business_impact: str = "",
        rollback_available: bool = True
    ) -> Callable:
        """
        Decorator to register a demo action.
        
        Args:
            key: Unique identifier for the demo action
            title: Display title
            description: Description of what the demo does
            category: Category (e.g., "Healthcare", "Construction")
            estimated_time: Estimated execution time
            estimated_records: Estimated number of records to create
            required_modules: List of required Frappe apps
            risk_level: Risk level of the demo
            execution_modes: Available execution modes
            default_execution_mode: Default execution mode
            icon: Font Awesome icon class
            color: Bootstrap color class
            enabled: Whether the demo is enabled
            permissions: Required permissions
            dependencies: Other demo dependencies
            warnings: Warning messages
            business_impact: Description of business impact
            rollback_available: Whether rollback is available
            
        Returns:
            Decorator function
        """
        def decorator(handler: Callable) -> Callable:
            metadata = DemoActionMetadata(
                key=key,
                title=title,
                description=description,
                category=category,
                estimated_time=estimated_time,
                estimated_records=estimated_records,
                required_modules=required_modules,
                risk_level=risk_level,
                execution_modes=execution_modes,
                default_execution_mode=default_execution_mode,
                icon=icon,
                color=color,
                enabled=enabled,
                permissions=permissions,
                dependencies=dependencies,
                warnings=warnings,
                business_impact=business_impact,
                rollback_available=rollback_available
            )
            
            cls._registry[key] = metadata
            cls._handlers[key] = handler
            
            return handler
        
        return decorator
    
    @classmethod
    def get_all_metadata(cls, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get metadata for all registered demo actions.
        
        Args:
            enabled_only: Only return enabled demos
            
        Returns:
            List of metadata dictionaries
        """
        metadata_list = []
        for key, metadata in cls._registry.items():
            if not enabled_only or metadata.enabled:
                metadata_list.append(metadata.to_dict())
        
        # Sort by category then title
        metadata_list.sort(key=lambda x: (x["category"], x["title"]))
        return metadata_list
    
    @classmethod
    def get_metadata(cls, key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific demo action.
        
        Args:
            key: Demo action key
            
        Returns:
            Metadata dictionary or None if not found
        """
        metadata = cls._registry.get(key)
        if metadata:
            return metadata.to_dict()
        return None
    
    @classmethod
    def get_handler(cls, key: str) -> Optional[Callable]:
        """
        Get handler for a specific demo action.
        
        Args:
            key: Demo action key
            
        Returns:
            Handler function or None if not found
        """
        return cls._handlers.get(key)
    
    @classmethod
    def execute(
        cls,
        key: str,
        execution_mode: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a demo action.
        
        Args:
            key: Demo action key
            execution_mode: Execution mode
            context: Additional context (company, branch, etc.)
            
        Returns:
            Execution result dictionary
        """
        handler = cls.get_handler(key)
        metadata = cls.get_metadata(key)
        
        if not handler:
            return {
                "success": False,
                "error": f"Demo action not found: {key
	}"
            }
        
        if not metadata:
            return {
                "success": False,
                "error": f"Metadata not found for: {key
	}"
            }
        
        # Validate permissions - disabled for demo execution
        # if not cls._validate_permissions(metadata["permissions"]):
        #     return {
        #         "success": False,
        #         "error": "Permission denied"
        #     }
        
        # Validate modules
        if not cls._validate_modules(metadata["required_modules"]):
            return {
                "success": False,
                "error": f"Required modules not installed: {metadata['required_modules']
	}"
            }
        
        # Validate dependencies
        if not cls._validate_dependencies(metadata["dependencies"], context):
            return {
                "success": False,
                "error": f"Dependencies not satisfied: {metadata['dependencies']
	}"
            }
        
        # Execute handler
        try:
            result = handler(execution_mode=execution_mode, context=context or {})
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            frappe.log_error(f"Demo execution error: {str(e)}", "Demo Registry")
            return {
                "success": False,
                "error": str(e)
            }
    
    @classmethod
    def _validate_permissions(cls, required_permissions: List[str]) -> bool:
        """Validate that user has required permissions"""
        if not required_permissions:
            return True
        
        user_roles = frappe.get_roles(frappe.session.user)
        # Allow if user is System Manager or Administrator
        if "System Manager" in user_roles or "Administrator" in user_roles:
            return True
        
        # Check if user has any of the required roles
        return any(role in user_roles for role in required_permissions)
    
    @classmethod
    def _validate_modules(cls, required_modules: List[str]) -> bool:
        """Validate that required modules are installed"""
        if not required_modules:
            return True
        
        installed_apps = frappe.get_installed_apps()
        return all(module in installed_apps for module in required_modules)
    
    @classmethod
    def _validate_dependencies(cls, dependencies: List[str], context: Dict[str, Any]) -> bool:
        """Validate that dependencies are satisfied"""
        # This can be extended to check specific conditions
        # For now, just return True
        return True


# Import demo action registrations
try:
    from omnexa_core.demo_actions import (
        register_branch_masters_demo,
        register_branch_transactions_demo,
        register_business_simulation_6m_demo,
        register_business_simulation_12m_demo,
        register_construction_portfolio_demo,
        register_healthcare_masters_demo,
        register_healthcare_procedures_consumables_demo,
        register_healthcare_hospital_demo,
        register_finance_group_demo,
        register_education_demo,
        register_hotel_assets_demo
    )
except ImportError:
    # Demo actions not yet registered
    pass
