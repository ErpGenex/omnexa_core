#!/usr/bin/env bash
# Push every omnexa_* app under the bench to GitHub (default org: microcol).
# Run from bench root:
#   chmod +x apps/omnexa_core/omnexa_core/deploy/push_all_omnexa_apps_github.sh
#   ./apps/omnexa_core/omnexa_core/deploy/push_all_omnexa_apps_github.sh
#
# Prereq: each app is its own git repo; default branch develop.
# Auth: REMOTE_STYLE=ssh (default) or https + GITHUB_TOKEN for non-interactive https.
#
# Optional: PUSH_MAIN=1 — after pushing develop, also run: git push origin develop:main
# Optional: ALLOW_FORCE_DEVELOP_TO_MAIN=1 — if develop:main is rejected, force-with-lease (team policy).
set -euo pipefail
BENCH_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
APPS_DIR="${BENCH_ROOT}/apps"
REMOTE_STYLE="${REMOTE_STYLE:-ssh}"
GITHUB_ORG="${GITHUB_ORG:-microcol}"
PUSH_MAIN="${PUSH_MAIN:-0}"

remote_url() {
	local app_dir="$1"
	local name
	name="$(basename "$app_dir")"
	if [[ "$REMOTE_STYLE" == "ssh" ]]; then
		echo "git@github.com:${GITHUB_ORG}/${name}.git"
	else
		echo "https://github.com/${GITHUB_ORG}/${name}.git"
	fi
}

push_with_token() {
	local url="$1"
	local path="${url#https://}"
	echo "https://${GITHUB_TOKEN}@${path}"
}

ensure_origin() {
	local app_dir="$1"
	local want
	want="$(remote_url "$app_dir")"
	if [[ -n "${GITHUB_TOKEN:-}" && "$REMOTE_STYLE" != "ssh" ]]; then
		want="$(push_with_token "$want")"
	fi
	if git -C "$app_dir" remote get-url origin &>/dev/null; then
		git -C "$app_dir" remote set-url origin "$want"
	else
		git -C "$app_dir" remote add origin "$want"
	fi
}

push_one() {
	local app_dir="$1"
	local name
	local current_branch
	name="$(basename "$app_dir")"
	echo "======== ${name} ========"
	if [[ ! -d "${app_dir}/.git" ]]; then
		echo "Skip: not a git repo: ${app_dir}"
		return 0
	fi
	ensure_origin "$app_dir"
	git fetch origin 2>/dev/null || true
	current_branch="$(git -C "$app_dir" branch --show-current)"
	if [[ -z "$current_branch" ]]; then
		echo "Skip: detached HEAD in ${name}"
		return 0
	fi
	git -C "$app_dir" push -u origin "${current_branch}"
	if [[ "$PUSH_MAIN" == "1" ]] && [[ "$current_branch" == "develop" ]]; then
		if git -C "$app_dir" push origin develop:main; then
			:
		elif [[ "${ALLOW_FORCE_DEVELOP_TO_MAIN:-0}" == "1" ]]; then
			echo "WARNING: forcing origin/main to match develop (${name})"
			git -C "$app_dir" push --force-with-lease origin develop:main
		else
			echo "Note: develop -> main not updated for ${name} (set ALLOW_FORCE_DEVELOP_TO_MAIN=1 to force)."
		fi
	fi
	echo "Done ${name}"
	echo ""
}

shopt -s nullglob
mapfile -t OMNEXA_APPS < <(find "${APPS_DIR}" -maxdepth 1 -type d -name 'omnexa_*' | LC_ALL=C sort)

if [[ ${#OMNEXA_APPS[@]} -eq 0 ]]; then
	echo "No omnexa_* directories under ${APPS_DIR}"
	exit 1
fi

echo "Found ${#OMNEXA_APPS[@]} omnexa app directories."
for app_dir in "${OMNEXA_APPS[@]}"; do
	push_one "$app_dir"
done
echo "Finished pushing all omnexa apps."
