#!/usr/bin/env python3
"""Generate GitHub issue payloads from docs/IMPLEMENTATION_PLAN.md.

Usage:
    scripts/plan_tasks_to_issues.py               # print all tasks to stdout
    scripts/plan_tasks_to_issues.py --phase 1     # only Phase 1
    scripts/plan_tasks_to_issues.py --task P3.T2  # only one task
    scripts/plan_tasks_to_issues.py --gh-create   # actually create issues via
                                                  # `gh issue create` (requires
                                                  # the GitHub CLI to be
                                                  # authenticated).

The generated issue title is: "Task P<phase>.T<task>: <first line of context>".
The body contains the task's `Satisfies` / `Do` / `Acceptance` sections copied
verbatim, plus a link back to the plan.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PLAN_PATH = Path(__file__).resolve().parent.parent / "docs" / "IMPLEMENTATION_PLAN.md"
PLAN_URL_TMPL = "https://github.com/durczokj/vendor_manager/blob/main/docs/IMPLEMENTATION_PLAN.md"

TASK_HEADER = re.compile(r"^### (P\d+\.T\d+)\s+—\s+(.+?)\s*(\[.*\])?\s*$", re.MULTILINE)
PHASE_HEADER = re.compile(r"^## Phase (\d+)\b", re.MULTILINE)


@dataclass
class Task:
    """A single plan task extracted from ``docs/IMPLEMENTATION_PLAN.md``."""

    task_id: str  # e.g. "P3.T2"
    phase: int  # e.g. 3
    title: str  # e.g. "Contracts/orders viewsets"
    body: str  # the raw markdown between the `###` and the next `###`/`##`


def _anchor(task_id: str) -> str:
    return task_id.replace(".", "").lower()


def parse_plan(text: str) -> list[Task]:
    """Extract every ### Px.Ty task block."""
    tasks: list[Task] = []
    headers = list(TASK_HEADER.finditer(text))
    for i, m in enumerate(headers):
        task_id = m.group(1)
        title = m.group(2).strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else _next_h2(text, start)
        body = text[start:end].strip()
        phase = int(task_id.split(".")[0][1:])
        tasks.append(Task(task_id=task_id, phase=phase, title=title, body=body))
    return tasks


def _next_h2(text: str, from_pos: int) -> int:
    m = re.search(r"^## ", text[from_pos:], re.MULTILINE)
    return from_pos + m.start() if m else len(text)


def render_issue_body(task: Task) -> str:
    """Render the GitHub issue body for a task, including the plan link."""
    link = f"{PLAN_URL_TMPL}#{_anchor(task.task_id)}"
    return (
        f"> Executes task **{task.task_id}** from the implementation plan.\n"
        f"> Plan section: [{task.task_id} — {task.title}]({link})\n\n"
        f"---\n\n"
        f"{task.body.strip()}\n\n"
        f"---\n\n"
        f"### Working agreement\n\n"
        f"- Read `.github/copilot-instructions.md` before starting.\n"
        f"- Follow the plan's `Do` bullets verbatim. Anything outside scope goes into a follow-up issue.\n"
        f"- Every bullet under `Acceptance` must be verifiable in the PR (screenshots, logs, or CI evidence).\n"
        f"- Reference `{task.task_id}` in the PR title. Reference every FR-/NFR- ID in the commit body.\n"
        f"- The PR must be self-contained and leave CI green.\n"
    )


def render_issue_title(task: Task) -> str:
    """Render the GitHub issue title as ``<task_id>: <title>``."""
    return f"{task.task_id}: {task.title}"


def main() -> int:
    """Parse CLI args, filter tasks, and print or create issues."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase", type=int, help="Only tasks in this phase.")
    p.add_argument("--task", help="Only this task ID, e.g. P3.T2.")
    p.add_argument(
        "--gh-create",
        action="store_true",
        help="Actually create the issues via `gh issue create`. Otherwise dry-run to stdout.",
    )
    p.add_argument(
        "--label",
        default="plan-task",
        help="Label to attach when --gh-create is set (default: plan-task).",
    )
    args = p.parse_args()

    text = PLAN_PATH.read_text(encoding="utf-8")
    tasks = parse_plan(text)
    if args.phase is not None:
        tasks = [t for t in tasks if t.phase == args.phase]
    if args.task:
        tasks = [t for t in tasks if t.task_id == args.task]

    if not tasks:
        print("No tasks matched.", file=sys.stderr)
        return 1

    for t in tasks:
        title = render_issue_title(t)
        body = render_issue_body(t)
        if args.gh_create:
            result = subprocess.run(
                ["gh", "issue", "create", "--title", title, "--body", body, "--label", args.label],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                print(f"FAILED: {title}\n{result.stderr}", file=sys.stderr)
                continue
            print(f"created: {title} — {result.stdout.strip()}")
        else:
            print("=" * 80)
            print(f"TITLE: {title}")
            print("-" * 80)
            print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
