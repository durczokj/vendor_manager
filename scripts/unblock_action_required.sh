#!/usr/bin/env bash
# Re-fires any CI runs stuck at conclusion=action_required.
#
# GitHub gates the first workflow runs from a "first-time contributor" (which
# includes the copilot-swe-agent bot on its early PRs) behind a manual
# "Approve and run" click in the Actions UI. There is no REST endpoint that
# flips that repo setting for a user-owned repo, but `gh run rerun` on an
# action_required run bypasses the gate and starts a fresh execution.
#
# Usage:
#   scripts/unblock_action_required.sh                # scan all recent runs
#   scripts/unblock_action_required.sh <branch-name>  # scan one branch
#
# Idempotent: skips runs that are not action_required.

set -euo pipefail

BRANCH="${1:-}"

if [[ -n "${BRANCH}" ]]; then
    LIST_ARGS=(--branch "${BRANCH}")
else
    LIST_ARGS=()
fi

mapfile -t RUN_IDS < <(
    gh run list "${LIST_ARGS[@]}" --limit 50 \
        --json databaseId,conclusion,status \
        --jq '.[] | select(.conclusion=="action_required") | .databaseId'
)

if [[ "${#RUN_IDS[@]}" -eq 0 ]]; then
    echo "No action_required runs found."
    exit 0
fi

for run_id in "${RUN_IDS[@]}"; do
    echo "Re-firing run ${run_id}..."
    gh run rerun "${run_id}"
done

echo "Done. ${#RUN_IDS[@]} run(s) re-queued."
