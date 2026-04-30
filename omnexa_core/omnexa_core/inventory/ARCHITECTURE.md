## Inventory / Warehouse Module (Enterprise)

This implementation builds on existing Omnexa accounting inventory doctypes and adds enterprise controls without breaking current flows.

### Core Lifecycle

Item Master -> Stock Entry -> Purchase Receipt -> Delivery Note -> Valuation/GL -> Reports

Added enterprise flow:

Stock Transfer Request -> Execute -> Stock Entry (Material Transfer)

### Key Enterprise Additions

- **Stock Transfer Request** (`Stock Transfer Request`, `Stock Transfer Request Item`)
- **Stock Adjustment Reason** master
- **Warehouse Transfer Report**
- **Inventory API** for:
  - transfer execution
  - reorder suggestions
- **Submit-time compliance controls** on `Stock Entry`:
  - negative stock prevention
  - batch/serial traceability requirement for tracked items
  - adjustment reason + manager approval gate for adjustment/opening entries

### IFRS / IAS posture

- **IAS 2**: traceable stock movements, controlled adjustments, valuation method field on Item.
- **IAS 21**: currency controls rely on existing global conversion checks.
- **Auditability**: all inventory adjustments now have explicit reason metadata and submit-time governance.

### Feature Flags

- `global_inventory_controls` (default: true)
- `global_inventory_prevent_negative_stock` (default: true)
- `global_inventory_adjustment_approval` (default: true)

### Safe-by-default strategy

- No destructive schema rewrites.
- Existing doctypes remain valid.
- Enhancements are custom-field based and submit-time policies only.

