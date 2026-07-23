# Sidebar Sector Grouping — Safety Backup (2026-07-21)

Restore these files to roll back the sector sidebar grouping change:

```bash
BACKUP=apps/omnexa_core/omnexa_core/backups/sidebar_sector_20260721
cp "$BACKUP/business_categories.py" apps/omnexa_core/omnexa_core/business_categories.py
cp "$BACKUP/finance_desktop_sidebar.py" apps/omnexa_core/omnexa_core/omnexa_core/finance_desktop_sidebar.py
cp "$BACKUP/finance_group_sidebar.py" apps/omnexa_core/omnexa_core/omnexa_core/finance_demo/finance_group_sidebar.py
cp "$BACKUP/sidebar_categories.js" apps/omnexa_core/omnexa_core/public/js/sidebar_categories.js
cp "$BACKUP/sidebar_categories.css" apps/omnexa_core/omnexa_core/public/css/sidebar_categories.css
```

Then remove (if rolling back fully):
- `omnexa_core/omnexa_core/sector_registry.py`
- `omnexa_core/omnexa_core/sector_sidebar_sync.py`
- `patches/sync_sector_sidebar.py`

Run: `bench --site <site> migrate` and `bench build --app omnexa_core`
