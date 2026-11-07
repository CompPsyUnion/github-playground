#!/usr/bin/env python3
"""CI check for profile pull requests.

Two layers of rules:

1. Repo-wide format check (always runs): every file in profiles/ is a
   valid profile — GitHub-username filename, starting with a
   "# Title" line. Files starting with "_" are templates.

2. PR rules (when --author and --pr-files are given, i.e. on pull_request):
   a profile PR must add EXACTLY ONE new file, and it must be
   profiles/<pr-author-login>.md — named after the PR author's own
   GitHub username. Anything else is an error.

Output goes to the console, to GitHub Actions annotations (::error),
and — when running inside Actions — to the job summary page via
$GITHUB_STEP_SUMMARY.
"""

import argparse
import os
import re
import sys
from pathlib import Path

USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
ROOT = Path(__file__).resolve().parent.parent
PROFILES = ROOT / "profiles"
SUMMARY_PATH = os.environ.get("GITHUB_STEP_SUMMARY")


def note_error(message):
    print("::error::%s" % message.replace("\n", " "))


def summary(text):
    if SUMMARY_PATH:
        with open(SUMMARY_PATH, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def md_cell(text):
    return text.replace("|", "\\|").replace("\n", " ")


def check_file(path):
    name = path.stem
    errors = []
    if not USERNAME_RE.match(name):
        errors.append(
            "%s: filename must be a GitHub username — letters, digits and "
            "hyphens only, up to 39 characters (got %r)" % (path.name, name)
        )
    text = path.read_text(encoding="utf-8").strip()
    if not any(line.startswith("# ") for line in text.splitlines()):
        errors.append('%s: start the file with a "# Title" line' % path.name)
    return errors


def run_repo_check():
    """Layer 1. Returns (ok, [(filename, errors)])."""
    if not PROFILES.is_dir():
        note_error("profiles/ directory is missing")
        return False, []
    files = sorted(
        p for p in PROFILES.glob("*.md") if not p.name.startswith("_")
    )
    results = [(p.name, check_file(p)) for p in files]
    for name, errors in results:
        for message in errors:
            note_error(message)
        if not errors:
            print("OK  %s" % name)
    print("Repo check: %d profile(s) scanned" % len(results))
    return all(not e for _, e in results), results


def read_pr_rows(pr_files_path):
    rows = []
    for line in Path(pr_files_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) == 2:
            rows.append((parts[0], parts[1]))
        else:
            rows.append(("changed", parts[0]))
    return rows


def run_pr_check(author, rows, expect):
    """Layer 2. Returns (ok, info-dict).

    `expect` is "added" for docs/* branches (first-time profile) or
    "modified" for fix/* branches (update your own profile).
    """
    expected = "profiles/%s.md" % author
    errors = []
    if len(rows) != 1:
        preview = ", ".join(name for _, name in rows[:5]) or "nothing"
        errors.append(
            "a profile PR must change exactly ONE file — this one changes "
            "%d (%s). Keep the PR to your own profile only."
            % (len(rows), preview)
        )
        status = rows[0][0] if len(rows) == 1 else "multiple"
    else:
        status, filename = rows[0]
        if filename != expected:
            errors.append(
                "wrong file: %r — your profile must be %r, named after "
                "your own GitHub username (@%s)"
                % (filename, expected, author)
            )
        if status == expect:
            pass
        elif expect == "added":
            errors.append(
                "%s must be a NEW file (GitHub reports status %r) — to "
                "update your existing profile, use a fix/* branch instead"
                % (expected, status)
            )
        else:
            errors.append(
                "a fix/* PR must MODIFY your existing profile (GitHub "
                "reports status %r for %s) — if your profile does not "
                "exist yet, use a docs/* branch" % (status, expected)
            )
    for message in errors:
        note_error(message)
    if not errors:
        print("PR check: %s exactly one file, %s — matches author @%s."
              % (expect + "s", expected, author))
    return not errors, {
        "author": author,
        "expected": expected,
        "expect": expect,
        "rows": rows,
        "errors": errors,
    }


def write_summary(passed, pr_info):
    """Render the report onto the Actions job summary page."""
    summary("## Profiles check — %s" % ("PASS ✅" if passed else "FAIL ❌"))
    summary("")

    if pr_info:
        summary("### PR rules — author @%s" % pr_info["author"])
        summary("")
        summary("Expected: %s `%s`"
                % (pr_info["expect"], pr_info["expected"]))
        summary("")
        summary("| Status | File |")
        summary("| --- | --- |")
        for status, filename in pr_info["rows"]:
            summary("| %s | `%s` |" % (md_cell(status), md_cell(filename)))
        if not pr_info["rows"]:
            summary("| _none_ | _no changed files reported_ |")
        summary("")
        if pr_info["errors"]:
            for message in pr_info["errors"]:
                summary("- ❌ %s" % md_cell(message))
        else:
            summary("Exactly one file (%s), named after the PR author. ✅"
                    % pr_info["expect"])
        summary("")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--author", default=None,
        help="GitHub login of the PR author (enables PR rules)",
    )
    parser.add_argument(
        "--pr-files", default=None,
        help="TSV file of <status>\\t<path> changed in the PR",
    )
    parser.add_argument(
        "--expect", choices=["added", "modified"], default="added",
        help="docs/* branches must ADD their profile; fix/* branches "
             "must MODIFY it",
    )
    args = parser.parse_args()

    ok, repo_results = run_repo_check()

    pr_info = None
    if args.author and args.pr_files:
        pr_ok, pr_info = run_pr_check(
            args.author, read_pr_rows(args.pr_files), args.expect
        )
        ok = pr_ok and ok
    elif args.author or args.pr_files:
        note_error("--author and --pr-files must be given together")
        ok = False

    write_summary(ok, pr_info)

    print("")
    print("Profiles check: %s" % ("PASS" if ok else "FAIL"))
    if SUMMARY_PATH:
        print("Report also written to the job summary.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
