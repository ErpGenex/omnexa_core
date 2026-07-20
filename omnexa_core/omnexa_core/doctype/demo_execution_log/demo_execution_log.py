# -*- coding: utf-8 -*-
"""
Demo Execution Log DocType
Tracks all demo action executions for audit and debugging purposes.
"""

import frappe
from frappe.model.document import Document
import uuid
from datetime import datetime


class DemoExecutionLog(Document):
    def before_insert(self):
        """Set execution ID and initial values before insert"""
        if not self.execution_id:
            self.execution_id = str(uuid.uuid4())
        
        if not self.user:
            self.user = frappe.session.user
        
        if not self.user_email:
            self.user_email = frappe.session.user_email
        
        if not self.user_roles:
            self.user_roles = ", ".join(frappe.get_roles(frappe.session.user))
        
        if not self.ip_address:
            self.ip_address = frappe.local.request_ip if frappe.local.request else "N/A"
        
        if not self.status:
            self.status = "Pending"
        
        if not self.start_time:
            self.start_time = datetime.now()
        
        if not self.modules_installed:
            self.modules_installed = ", ".join(frappe.get_installed_apps())
    
    def before_save(self):
        """Calculate duration before save"""
        if self.start_time and self.end_time:
            # Calculate duration in seconds as a decimal
            duration_delta = self.end_time - self.start_time
            self.duration = float(duration_delta.total_seconds())
    
    def on_update(self):
        """Handle status updates"""
        if self.status == "Completed" and not self.end_time:
            self.end_time = datetime.now()
            self.save()
    
    def mark_as_running(self):
        """Mark execution as running"""
        self.status = "Running"
        self.start_time = datetime.now()
        self.save()
    
    def mark_as_completed(self, records_created=0, records_updated=0, records_deleted=0, warnings=0, errors=0):
        """Mark execution as completed with results"""
        self.status = "Completed"
        self.end_time = datetime.now()
        self.records_created = records_created
        self.records_updated = records_updated
        self.records_deleted = records_deleted
        self.warnings = warnings
        self.errors = errors
        self.save()
    
    def mark_as_failed(self, error_message, error_details=None):
        """Mark execution as failed"""
        self.status = "Failed"
        self.end_time = datetime.now()
        self.errors = 1
        self.error_details = error_message
        if error_details:
            self.error_details += f"\n\nDetails:\n{error_details}"
        self.save()
    
    def mark_as_cancelled(self):
        """Mark execution as cancelled"""
        self.status = "Cancelled"
        self.end_time = datetime.now()
        self.save()


@frappe.whitelist()
def create_demo_execution_log(demo_action, demo_title, category, execution_mode, company, branch):
    """Create a new demo execution log"""
    log = frappe.new_doc("Demo Execution Log")
    log.demo_action = demo_action
    log.demo_title = demo_title
    log.category = category
    log.execution_mode = execution_mode
    log.company = company
    log.branch = branch
    log.insert()
    return log.name


@frappe.whitelist()
def get_demo_execution_logs(branch=None, limit=50):
    """Get demo execution logs for a branch"""
    filters = {}
    if branch:
        filters["branch"] = branch
    
    logs = frappe.get_all(
        "Demo Execution Log",
        filters=filters,
        fields=[
            "name",
            "execution_id",
            "demo_title",
            "category",
            "execution_mode",
            "status",
            "start_time",
            "end_time",
            "duration",
            "user",
            "records_created",
            "records_updated",
            "records_deleted",
            "warnings",
            "errors"
        ],
        order_by="creation desc",
        limit=limit
    )
    
    return logs


@frappe.whitelist()
def get_demo_execution_statistics(branch=None):
    """Get demo execution statistics"""
    filters = {}
    if branch:
        filters["branch"] = branch
    
    total_executions = frappe.db.count("Demo Execution Log", filters=filters)
    
    successful = frappe.db.count("Demo Execution Log", filters={**filters, "status": "Completed"
	})
    failed = frappe.db.count("Demo Execution Log", filters={**filters, "status": "Failed"
	})
    running = frappe.db.count("Demo Execution Log", filters={**filters, "status": "Running"
	})
    
    total_records_created = frappe.db.get_value(
        "Demo Execution Log",
        filters=filters,
        fieldname="SUM(records_created)"
    ) or 0
    
    total_records_updated = frappe.db.get_value(
        "Demo Execution Log",
        filters=filters,
        fieldname="SUM(records_updated)"
    ) or 0
    
    return {
        "total_executions": total_executions,
        "successful": successful,
        "failed": failed,
        "running": running,
        "success_rate": round((successful / total_executions * 100) if total_executions > 0 else 0, 2),
        "total_records_created": total_records_created,
        "total_records_updated": total_records_updated
    }
