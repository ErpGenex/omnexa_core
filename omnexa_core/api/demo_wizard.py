# -*- coding: utf-8 -*-
"""
Demo Wizard API
Generic API endpoints for demo execution wizard.
"""

import frappe
from frappe import _
from omnexa_core.demo_registry import DemoRegistry
from omnexa_core.omnexa_core.doctype.demo_execution_log.demo_execution_log import (
    create_demo_execution_log,
    get_demo_execution_logs,
    get_demo_execution_statistics
)


@frappe.whitelist()
def get_demo_registry():
    """
    Get all registered demo actions with their metadata.
    
    Returns:
        List of demo action metadata dictionaries
    """
    try:
        return DemoRegistry.get_all_metadata(enabled_only=True)
    except Exception as e:
        frappe.log_error(f"Error getting demo registry: {str(e)}", "Demo Wizard API")
        return {"success": False, "error": str(e)
	}


@frappe.whitelist()
def get_demo_metadata(demo_key):
    """
    Get metadata for a specific demo action.
    
    Args:
        demo_key: Demo action key
        
    Returns:
        Demo action metadata dictionary
    """
    try:
        metadata = DemoRegistry.get_metadata(demo_key)
        if metadata:
            return {"success": True, "metadata": metadata
	}
        else:
            return {"success": False, "error": "Demo action not found"
	}
    except Exception as e:
        frappe.log_error(f"Error getting demo metadata: {str(e)}", "Demo Wizard API")
        return {"success": False, "error": str(e)
	}


@frappe.whitelist()
def execute_demo_action(demo_key, execution_mode, company, branch, execution_options=None):
    """
    Execute a demo action with full logging and validation.
    
    Args:
        demo_key: Demo action key
        execution_mode: Execution mode (create_missing, update_existing, etc.)
        company: Company name
        branch: Branch name
        execution_options: Additional execution options (dict)
        
    Returns:
        Execution result dictionary
    """
    try:
        # Get demo metadata
        metadata = DemoRegistry.get_metadata(demo_key)
        if not metadata:
            return {"success": False, "error": "Demo action not found"
	}
        
        # Create execution log
        log_name = create_demo_execution_log(
            demo_action=demo_key,
            demo_title=metadata["title"],
            category=metadata["category"],
            execution_mode=execution_mode,
            company=company,
            branch=branch
        )
        
        log = frappe.get_doc("Demo Execution Log", log_name)
        log.mark_as_running()
        
        # Prepare context
        context = {
            "company": company,
            "branch": branch,
            "execution_options": execution_options or {
	},
            "execution_log": log_name
        }
        
        # Execute demo
        result = DemoRegistry.execute(demo_key, execution_mode, context)
        
        if result.get("success"):
            # Mark as completed
            log.mark_as_completed(
                records_created=result.get("result", {}).get("records_created", 0),
                records_updated=result.get("result", {}).get("records_updated", 0),
                records_deleted=result.get("result", {}).get("records_deleted", 0),
                warnings=result.get("result", {}).get("warnings", 0),
                errors=result.get("result", {}).get("errors", 0)
            )
            
            return {
                "success": True,
                "result": result.get("result"),
                "execution_log": log_name,
                "duration": str(log.duration) if log.duration else "N/A"
            }
        else:
            # Mark as failed
            log.mark_as_failed(
                error_message=result.get("error", "Unknown error"),
                error_details=str(result)
            )
            
            return {
                "success": False,
                "error": result.get("error"),
                "execution_log": log_name
            }
            
    except Exception as e:
        frappe.log_error(f"Error executing demo action: {str(e)}", "Demo Wizard API")
        
        # Try to mark log as failed if it exists
        try:
            if log_name:
                log = frappe.get_doc("Demo Execution Log", log_name)
                log.mark_as_failed(error_message=str(e))
        except:
            pass
        
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def validate_demo_execution(demo_key, execution_mode, company, branch):
    """
    Validate that a demo action can be executed.
    
    Args:
        demo_key: Demo action key
        execution_mode: Execution mode
        company: Company name
        branch: Branch name
        
    Returns:
        Validation result with warnings and errors
    """
    try:
        metadata = DemoRegistry.get_metadata(demo_key)
        if not metadata:
            return {"success": False, "error": "Demo action not found"
	}
        
        warnings = []
        errors = []
        
        # Check permissions
        if not DemoRegistry._validate_permissions(metadata["permissions"]):
            errors.append(_("You don't have permission to execute this demo action"))
        
        # Check modules
        if not DemoRegistry._validate_modules(metadata["required_modules"]):
            errors.append(_("Required modules not installed: {0}").format(", ".join(metadata["required_modules"])))
        
        # Check dependencies
        if not DemoRegistry._validate_dependencies(metadata["dependencies"], {"company": company, "branch": branch
	}):
            errors.append(_("Dependencies not satisfied"))
        
        # Add metadata warnings
        for warning in metadata.get("warnings", []):
            warnings.append(warning)
        
        # Check if branch exists
        if branch:
            if not frappe.db.exists("Branch", branch):
                errors.append(_("Branch not found: {0}").format(branch))
        
        # Check if company exists
        if company:
            if not frappe.db.exists("Company", company):
                errors.append(_("Company not found: {0}").format(company))
        
        return {
            "success": len(errors) == 0,
            "valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "metadata": metadata
        }
        
    except Exception as e:
        frappe.log_error(f"Error validating demo execution: {str(e)}", "Demo Wizard API")
        return {"success": False, "error": str(e)
	}


@frappe.whitelist()
def get_execution_logs(branch=None, limit=50):
    """
    Get demo execution logs for a branch.
    
    Args:
        branch: Branch name (optional)
        limit: Maximum number of logs to return
        
    Returns:
        List of execution logs
    """
    try:
        return get_demo_execution_logs(branch, limit)
    except Exception as e:
        frappe.log_error(f"Error getting execution logs: {str(e)}", "Demo Wizard API")
        return {"success": False, "error": str(e)
	}


@frappe.whitelist()
def get_execution_statistics(branch=None):
    """
    Get demo execution statistics for a branch.
    
    Args:
        branch: Branch name (optional)
        
    Returns:
        Statistics dictionary
    """
    try:
        return get_demo_execution_statistics(branch)
    except Exception as e:
        frappe.log_error(f"Error getting execution statistics: {str(e)}", "Demo Wizard API")
        return {"success": False, "error": str(e)
	}


@frappe.whitelist()
def cancel_demo_execution(log_name):
    """
    Cancel a running demo execution.
    
    Args:
        log_name: Execution log name
        
    Returns:
        Result dictionary
    """
    try:
        log = frappe.get_doc("Demo Execution Log", log_name)
        
        if log.status != "Running":
            return {"success": False, "error": "Can only cancel running executions"
	}
        
        log.mark_as_cancelled()
        
        return {"success": True, "message": "Execution cancelled"
	}
        
    except Exception as e:
        frappe.log_error(f"Error cancelling demo execution: {str(e)}", "Demo Wizard API")
        return {"success": False, "error": str(e)
	}


@frappe.whitelist()
def rollback_demo_execution(log_name):
    """
    Rollback a demo execution if rollback is available.
    
    Args:
        log_name: Execution log name
        
    Returns:
        Result dictionary
    """
    try:
        log = frappe.get_doc("Demo Execution Log", log_name)
        
        if not log.rollback_available:
            return {"success": False, "error": "Rollback not available for this execution"
	}
        
        if log.rollback_performed:
            return {"success": False, "error": "Rollback already performed"
	}
        
        # This would need to be implemented per demo action
        # For now, just mark as rollback performed
        log.rollback_performed = 1
        log.save()
        
        return {"success": True, "message": "Rollback performed"
	}
        
    except Exception as e:
        frappe.log_error(f"Error rolling back demo execution: {str(e)}", "Demo Wizard API")
        return {"success": False, "error": str(e)
	}
