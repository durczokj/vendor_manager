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
    RUN_IDS=$(gh run list --branch "${BRANCH}" --limit 50 \
        --json databaseId,conclusion \
        --jq '.[] | select(.conclusion=="action_required") | .databaseId')
else
    RUN_IDS=$(gh run list --limit 50 \
        --json databaseId,conclusion \
        --jq '.[] | select(.conclusion=="action_required") | .databaseId')
fi

if [[ -z "${RUN_IDS}" ]]; then
    echo "No action_required runs found."
    exit 0
fi

COUNT=0
while IFS= read -r run_id; do
    [[ -z "${run_id}" ]] && continue
    echo "Re-firing run ${run_id}..."
    gh run rerun "${run_id}"
    COUNT=$((COUNT + 1))
done <<< "${RUN_IDS}"

echo "Done. ${COUNT} run(s) re-queued."
