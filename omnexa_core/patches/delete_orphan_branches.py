# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Delete all branches that reference companies that no longer exist."""

from __future__ import annotations

import frappe


def execute():
    """Delete all branches that reference companies that no longer exist."""
    
    # Get all valid companies
    valid_companies = frappe.db.get_all('Company', pluck='name')
    
    # Get all branches that reference invalid companies
    orphan_branches = frappe.db.get_all(
        'Branch',
        filters={'company': ['not in', valid_companies]},
        pluck='name'
    )
    
    if not orphan_branches:
        print("No orphan branches found.")
        return
    
    total_branches = len(orphan_branches)
    print(f"Found {total_branches} orphan branches to delete.")
    
    # Delete branches
    deleted_count = 0
    failed_count = 0
    
    for branch_name in orphan_branches:
        try:
            frappe.delete_doc('Branch', branch_name, force=1, ignore_permissions=True)
            
            deleted_count += 1
            
            if deleted_count % 100 == 0:
                print(f"Deleted {deleted_count}/{total_branches} branches...")
                
        except Exception as e:
            failed_count += 1
            print(f"Failed to delete {branch_name}: {str(e)}")
            frappe.log_error(frappe.get_traceback(), f"Delete Branch Error: {branch_name}")
    
    print(f"\nDeletion complete:")
    print(f"  - Successfully deleted: {deleted_count} branches")
    print(f"  - Failed: {failed_count} branches")
    
    # Clear cache
    frappe.clear_cache()
    print("Cache cleared.")
