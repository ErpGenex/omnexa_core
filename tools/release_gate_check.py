from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GateFailure:
	repo: str
	reason: str


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
	return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _is_git_repo(path: Path) -> bool:
	return (path / ".git").exists()


def _count_test_files(repo_path: Path) -> int:
	matches = list(repo_path.glob("**/tests/test_*.py"))
	return len(matches)


def _tracked_pyc(repo_path: Path) -> int:
	proc = _run(["git", "ls-files"], cwd=repo_path)
	if proc.returncode != 0:
		return 0
	count = 0
	for line in proc.stdout.splitlines():
		p = line.strip()
		if "__pycache__/" in p or p.endswith(".pyc"):
			count += 1
	return count


def evaluate_apps(bench_root: Path, min_tests_default: int, min_tests_utility: int) -> tuple[list[GateFailure], list[str]]:
	failures: list[GateFailure] = []
	passed: list[str] = []

	utility_apps = {
		"omnexa_theme_manager",
		"omnexa_setup_intelligence",
		"omnexa_user_academy",
		"omnexa_intelligence_core",
		"omnexa_backup",
	}

	apps_dir = bench_root / "apps"
	for app_dir in sorted(apps_dir.iterdir()):
		if not app_dir.is_dir():
			continue
		name = app_dir.name
		if not name.startswith("omnexa_"):
			continue
		if not _is_git_repo(app_dir):
			continue

		min_tests = min_tests_utility if name in utility_apps else min_tests_default
		tests_count = _count_test_files(app_dir)
		pyc_count = _tracked_pyc(app_dir)

		if tests_count < min_tests:
			failures.append(GateFailure(repo=name, reason=f"tests below floor ({tests_count} < {min_tests})"))
			continue
		if pyc_count > 0:
			failures.append(GateFailure(repo=name, reason=f"tracked pyc/cache files found ({pyc_count})"))
			continue
		passed.append(name)

	return failures, passed


def main(argv: list[str]) -> int:
	parser = argparse.ArgumentParser(description="Simple release gate for omnexa apps.")
	parser.add_argument("--bench-root", default=".", help="Path to frappe-bench root.")
	parser.add_argument("--min-tests-default", type=int, default=1, help="Minimum tests for normal apps.")
	parser.add_argument("--min-tests-utility", type=int, default=1, help="Minimum tests for utility apps.")
	args = parser.parse_args(argv)

	bench_root = Path(args.bench_root).resolve()
	failures, passed = evaluate_apps(
		bench_root=bench_root,
		min_tests_default=max(0, int(args.min_tests_default)),
		min_tests_utility=max(0, int(args.min_tests_utility)),
	)

	print("Release Gate Check")
	print("==================")
	print(f"Passed repos: {len(passed)}")
	print(f"Failed repos: {len(failures)}")
	if failures:
		print("\nFailures:")
		for item in failures:
			print(f"- {item.repo}: {item.reason}")
		return 1

	print("\nAll gate checks passed.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

