#!/usr/bin/env bash
# Mirror local ErpGenEx bench on an external server (pull all apps + migrate + post-hooks).
#
# Run ON THE EXTERNAL SERVER (any path — finds bench root automatically):
#   SITE=erpgenex.local.kml bash apps/omnexa_core/omnexa_core/scripts/ops/deploy_external_mirror_local.sh
#
# Site names: local dev = erpgenex.local.site · external server = erpgenex.local.kml
#
# Or from bench root:
#   SITE=erpgenex.local.kml bash scripts/ops/deploy_external_mirror_local.sh
#
# Options:
#   SKIP_PULL=1     — skip bench update (already pulled)
#   SKIP_RESTART=1  — skip bench restart
#   SKIP_DOCS=1     — skip Docs/ rsync hint
#   FORCE_REPORT_EXECUTE=1 — re-run report print/filter sync

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

SITE="${SITE:-erpgenex.local.kml}"

if [[ ! -d "sites/$SITE" ]]; then
	echo "ERROR: sites/$SITE not found. Available sites:"
	ls -1 sites/ | grep -vE '^(assets|apps\.txt|apps\.json|common_site_config\.json)$' || true
	exit 1
fi

APPS_LIST="$(grep -v '^frappe$' sites/apps.txt | paste -sd,)"

echo "=============================================="
echo " ErpGenEx — mirror deploy (external = local)"
echo " Bench: $BENCH_ROOT"
echo " Site:  $SITE"
echo " Apps:  $(echo "$APPS_LIST" | tr ',' '\n' | wc -l) (excl. frappe)"
echo "=============================================="

if [[ "${SKIP_PULL:-0}" != "1" ]]; then
	echo "==> [1/6] bench update --apps (git pull + build all installed apps)..."
	# shellcheck disable=SC2086
	bench update --apps "$APPS_LIST"
else
	echo "==> [1/6] SKIP_PULL=1 — skipping bench update"
fi

echo "==> [2/6] migrate (patches, after_migrate hooks, workspaces)..."
bench --site "$SITE" migrate

echo "==> [3/6] Construction workspace + World Class 100 (if app installed)..."
if grep -qx 'omnexa_construction' sites/apps.txt 2>/dev/null; then
	bench --site "$SITE" execute omnexa_construction.workspace.construction_workspace.sync_construction_workspace_menu || true
	if bench --site "$SITE" execute omnexa_construction.patches.v2_0.ensure_world_class_score_100.execute 2>/dev/null; then
		:
	else
		bench --site "$SITE" execute omnexa_construction.world_class_certification.apply_site_certification_defaults || true
	fi
	bench build --app omnexa_construction
fi

echo "==> [4/6] Omnexa core desk / workspace sync (if available)..."
if grep -qx 'omnexa_core' sites/apps.txt 2>/dev/null; then
	bench --site "$SITE" execute omnexa_core.omnexa_core.workspace_site_sync.run_full_workspace_sync 2>/dev/null \
		|| bench --site "$SITE" execute omnexa_core.install.run_workspace_desk_sync 2>/dev/null \
		|| true
	bench --site "$SITE" execute omnexa_core.omnexa_core.session_guard.purge_corrupt_sessions_now 2>/dev/null || true
	bench build --app omnexa_core
fi

if grep -qx 'omnexa_healthcare' sites/apps.txt 2>/dev/null; then
	bench --site "$SITE" execute omnexa_healthcare.workspace.healthcare_workspace.sync_healthcare_workspace_menu 2>/dev/null || true
	bench build --app omnexa_healthcare
fi

if [[ "${FORCE_REPORT_EXECUTE:-0}" == "1" ]]; then
	echo "==> FORCE_REPORT_EXECUTE: report print + filters..."
	bench --site "$SITE" execute omnexa_core.omnexa_core.report_print.link_reports.link_erpgenex_report_print_assets || true
	bench --site "$SITE" execute omnexa_core.omnexa_core.report_print.infer_report_filters.sync_all_erpgenex_report_json_filters || true
fi

echo "==> [5/6] clear-cache..."
bench --site "$SITE" clear-cache

if [[ "${SKIP_RESTART:-0}" != "1" ]]; then
	echo "==> [6/6] bench restart..."
	bench restart
else
	echo "==> [6/6] SKIP_RESTART=1"
fi

if [[ "${SKIP_DOCS:-0}" != "1" ]] && [[ ! -d "Docs/2026-06-01_OMNEXA_CONSTRUCTION_WORLD_CLASS" ]]; then
	echo ""
	echo "NOTE: Docs/ (World Class markdown) is NOT in app git repos."
	echo "      Copy from dev machine if you need identical documentation:"
	echo "      rsync -av dev:/path/to/frappe-bench/Docs/ $BENCH_ROOT/Docs/"
fi

echo ""
echo "==> DONE. Open Desk and hard-refresh (Ctrl+F5)."
echo "    Construction: /app/construction"
if grep -qx 'omnexa_construction' sites/apps.txt 2>/dev/null; then
	bench --site "$SITE" execute omnexa_construction.world_class_compliance.get_live_compliance_score 2>/dev/null || true
fi
