from __future__ import annotations

import argparse
import json
import subprocess
import sys


def main(argv: list[str]) -> int:
	parser = argparse.ArgumentParser(description="Run core ERP readiness snapshot via bench execute.")
	parser.add_argument("--site", required=True, help="Frappe site name (for example: erpgenex.local.site)")
	args = parser.parse_args(argv)

	cmd = [
		"bench",
		"--site",
		args.site,
		"execute",
		"omnexa_core.core_erp_readiness.get_core_erp_readiness_snapshot",
	]
	proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
	if proc.returncode != 0:
		print(proc.stdout)
		print(proc.stderr, file=sys.stderr)
		return proc.returncode

	raw = (proc.stdout or "").strip()
	if not raw:
		print("No output returned from readiness snapshot.")
		return 1

	try:
		data = json.loads(raw)
	except json.JSONDecodeError:
		print(raw)
		return 0

	print(json.dumps(data, indent=2, ensure_ascii=False))
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

