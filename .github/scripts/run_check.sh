#!/usr/bin/env bash
# Run one verification command, copy its output into the GitHub step summary
# inside a fenced block, and exit with the command's own status.
#
#   run_check.sh "Heading" python .github/scripts/check_links.py
#
# Outside Actions, GITHUB_STEP_SUMMARY is unset and the summary goes nowhere;
# the command still runs and its exit status is still what you get back.
set -uo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <heading> <command> [args...]" >&2
  exit 2
fi

heading=$1
shift
summary=${GITHUB_STEP_SUMMARY:-/dev/null}

{ printf '### %s\n\n' "$heading"; printf '```text\n'; } >> "$summary"
"$@" 2>&1 | tee -a "$summary"
status=${PIPESTATUS[0]}
printf '```\n\n' >> "$summary"

if [ "$status" -ne 0 ]; then
  printf '**This check FAILED.** The job log has the full output.\n\n' >> "$summary"
fi

exit "$status"
