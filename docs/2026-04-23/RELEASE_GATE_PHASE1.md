# Release Gate (Phase 1)

This gate is intentionally simple and focused on two immediate stability rules:

1. **Minimum test floor** per app repo.
2. **No tracked cache artifacts** (`__pycache__`, `.pyc`) in git.

## Run

From bench root:

```bash
python apps/omnexa_core/tools/release_gate_check.py --bench-root .
```

Optional stricter mode:

```bash
python apps/omnexa_core/tools/release_gate_check.py --bench-root . --min-tests-default 2 --min-tests-utility 2
```

## Exit code

- `0`: gate passed
- `1`: gate failed (one or more repos below floor or with tracked cache files)

## Utility app set (current)

- `omnexa_theme_manager`
- `omnexa_setup_intelligence`
- `omnexa_user_academy`
- `omnexa_intelligence_core`
- `omnexa_backup`

