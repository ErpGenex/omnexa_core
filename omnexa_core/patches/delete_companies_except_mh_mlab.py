# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Delete all companies except MH (Microhard) and MLAB (Microlab Information Systems)."""

from __future__ import annotations

import frappe


def execute():
    """Delete all companies except MH and MLAB."""
    
    # Companies to keep
    companies_to_keep = ['MH', 'MLAB']
    
    # Get all companies except the ones to keep
    companies_to_delete = frappe.db.get_all(
        'Company',
        filters={'name': ['not in', companies_to_keep]},
        pluck='name'
    )
    
    if not companies_to_delete:
        print("No companies to delete found.")
        return
    
    total_companies = len(companies_to_delete)
    print(f"Found {total_companies} companies to delete.")
    
    # Delete companies
    deleted_count = 0
    failed_count = 0
    
    for company_name in companies_to_delete:
        try:
            # Delete the company (this will cascade delete branches and related data)
            frappe.delete_doc('Company', company_name, force=1, ignore_permissions=True)
            
            deleted_count += 1
            
            if deleted_count % 100 == 0:
                print(f"Deleted {deleted_count}/{total_companies} companies...")
                
        except Exception as e:
            failed_count += 1
            print(f"Failed to delete {company_name}: {str(e)}")
            frappe.log_error(frappe.get_traceback(), f"Delete Company Error: {company_name}")
    
    print(f"\nDeletion complete:")
    print(f"  - Successfully deleted: {deleted_count} companies")
    print(f"  - Failed: {failed_count} companies")
    
    # Clear cache
    frappe.clear_cache()
    print("Cache cleared.")
