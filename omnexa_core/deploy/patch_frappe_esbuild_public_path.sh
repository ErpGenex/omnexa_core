#!/usr/bin/env bash
# Fix bench get-app build failure:
#   TypeError paths[0] must be string, Received undefined
# when an app is passed to esbuild before it appears in sites/apps.txt.
#
# Root fix for ErpGenEx apps: ensure each app has omnexa_*/patches.txt (bench is_frappe_app).
# This script is a belt-and-suspenders patch for frappe/esbuild/utils.js.
#
# Usage (from bench root):
#   chmod +x apps/omnexa_core/omnexa_core/deploy/patch_frappe_esbuild_public_path.sh
#   ./apps/omnexa_core/omnexa_core/deploy/patch_frappe_esbuild_public_path.sh
set -euo pipefail

BENCH_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
UTILS="${BENCH_ROOT}/apps/frappe/esbuild/utils.js"
export BENCH_ROOT

if [[ ! -f "$UTILS" ]]; then
	echo "ERROR: $UTILS not found"
	exit 1
fi

if grep -q 'return path.resolve(apps_path, app, app, "public")' "$UTILS"; then
	echo "esbuild utils.js already patched."
	exit 0
fi

cp -a "$UTILS" "${UTILS}.bak-$(date +%Y%m%d%H%M%S)"

python3 - <<'PY'
from pathlib import Path
import os

path = Path(os.environ["BENCH_ROOT"]) / "apps/frappe/esbuild/utils.js"
text = path.read_text(encoding="utf-8")
old = 'const get_public_path = (app) => public_paths[app];'
new = '''const get_public_path = (app) => {
\tif (public_paths[app]) {
\t\treturn public_paths[app];
\t}
\treturn path.resolve(apps_path, app, app, "public");
};'''
if old not in text and 'return path.resolve(apps_path, app, app, "public")' not in text:
	raise SystemExit("ERROR: unexpected utils.js format — patch manually")
if old in text:
	path.write_text(text.replace(old, new), encoding="utf-8")
	print("Patched get_public_path in", path)
else:
	print("Already patched:", path)
PY

echo "Done. Re-run: bench build --app <app>"
