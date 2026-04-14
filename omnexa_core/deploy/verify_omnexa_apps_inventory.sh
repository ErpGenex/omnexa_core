#!/usr/bin/env bash
# Compare omnexa_* folders under apps/ with sites/apps.txt (and optionally list repos without origin).
# Run from bench root:
#   ./apps/omnexa_core/omnexa_core/deploy/verify_omnexa_apps_inventory.sh
set -euo pipefail
BENCH_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
APPS_DIR="${BENCH_ROOT}/apps"
APPS_TXT="${BENCH_ROOT}/sites/apps.txt"

tmp1=$(mktemp)
tmp2=$(mktemp)
trap 'rm -f "$tmp1" "$tmp2"' EXIT

find "${APPS_DIR}" -maxdepth 1 -type d -name 'omnexa_*' -printf '%f\n' | LC_ALL=C sort >"$tmp1"
if [[ -f "$APPS_TXT" ]]; then
	grep '^omnexa_' "$APPS_TXT" | LC_ALL=C sort >"$tmp2"
	echo "=== Diff: folder apps/ vs sites/apps.txt (omnexa_* only) ==="
	if ! diff -u "$tmp2" "$tmp1"; then
		echo "MISMATCH: fix sites/apps.txt or add/remove app under apps/"
		exit 1
	fi
	echo "OK: apps/ omnexa_* matches sites/apps.txt ($(wc -l <"$tmp1") apps)."
else
	echo "WARN: no ${APPS_TXT}; listing apps/ only ($(wc -l <"$tmp1") dirs)."
fi

echo ""
echo "=== Git remotes (expect origin -> github.com/microcol/<name>.git) ==="
while IFS= read -r name; do
	[[ -z "$name" ]] && continue
	dir="${APPS_DIR}/${name}"
	if [[ ! -d "${dir}/.git" ]]; then
		echo "${name}: NO .git"
		continue
	fi
	url=$(git -C "$dir" remote get-url origin 2>/dev/null || echo "(no origin)")
	echo "${name}: ${url}"
done <"$tmp1"
