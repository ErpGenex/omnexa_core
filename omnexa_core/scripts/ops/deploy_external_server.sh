#!/usr/bin/env bash
# Deploy ErpGenEx bench after GitHub push (reports audit wave).
# Usage on EXTERNAL server:
#   export SITE=your.production.site
#   cd /path/to/frappe-bench
#   bash apps/omnexa_core/omnexa_core/scripts/ops/deploy_external_server.sh
#
# Optional: SKIP_PULL=1 if you already ran bench update manually.

set -euo pipefail

_find_bench_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [[ "$d" != "/" ]]; do
    if [[ -f "$d/sites/apps.txt" ]]; then
      echo "$d"
      return 0
    fi
    d="$(dirname "$d")"
  done
  return 1
}

BENCH_ROOT="$(_find_bench_root || true)"
if [[ -z "$BENCH_ROOT" ]]; then
  echo "ERROR: cannot find frappe-bench root (sites/apps.txt)"
  exit 1
fi
cd "$BENCH_ROOT"

SITE="${SITE:-}"
if [[ -z "$SITE" ]]; then
  echo "ERROR: set SITE env var, e.g. export SITE=erpgenex.yourdomain.com"
  exit 1
fi

if [[ ! -d "sites/$SITE" ]]; then
  echo "ERROR: sites/$SITE not found. Available sites:"
  ls -1 sites/ | grep -vE '^(assets|apps\.txt|apps\.json|common_site_config\.json)$' || true
  exit 1
fi

APPS_LIST="$(grep -v '^frappe$' sites/apps.txt | paste -sd,)"

echo "==> Bench: $BENCH_ROOT"
echo "==> Site:  $SITE"
echo "==> Apps:  $(echo "$APPS_LIST" | tr ',' '\n' | wc -l) omnexa/erpgenex apps"

if [[ "${SKIP_PULL:-0}" != "1" ]]; then
  echo "==> bench update (pull + build)..."
  bench update --apps "$APPS_LIST"
fi

echo "==> migrate (runs after_migrate: print, filters, workspaces)..."
bench --site "$SITE" migrate

# Optional belt-and-suspenders if omnexa_core hook failed (old build):
if [[ "${FORCE_REPORT_EXECUTE:-0}" == "1" ]]; then
  echo "==> FORCE_REPORT_EXECUTE: manual print + filters..."
  bench --site "$SITE" execute omnexa_core.omnexa_core.report_print.link_reports.link_erpgenex_report_print_assets
  bench --site "$SITE" execute omnexa_core.omnexa_core.report_print.infer_report_filters.sync_all_erpgenex_report_json_filters
fi

echo "==> clear-cache + restart..."
bench --site "$SITE" clear-cache
bench restart

AUDIT="apps/omnexa_core/omnexa_core/scripts/ops/audit_reports_print_checklist.py"
if [[ -f "$AUDIT" ]]; then
  echo "==> audit checklist (optional)..."
  python3 "$AUDIT" --merge || true
fi

echo "==> DONE. Verify: open Desk > Report > any ErpGenEx report (filters + Print)."
