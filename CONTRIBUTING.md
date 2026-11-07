# Contributing to github-playground

This repository is the hands-on playground for the CPU weekly session on
GitHub. Everyone is welcome to add their profile — the whole flow works
in the browser, no tools installed.

## Add your profile

1. **Fork** this repository.
2. In your fork, open the `profiles/` directory → **Add file → Create new
   file** → name it `<your-github-username>.md`.
3. Write a short intro: start with a `# Title` line, a few lines about
   yourself. Copy `profiles/_template.md` if you like a starting point.
4. In the commit dialog choose **Create a new branch for this commit** and
   name the branch `docs/add-<your-username>` — the `docs/` prefix
   matters, see below.
5. Commit, then click **Compare & pull request** back to
   `CompPsyUnion/github-playground:main`. A clear title (for example
   `feat: add <username> to profiles`) and a two-line description are
   appreciated.
6. CI checks your PR. When it passes, the robot squash-merges it within
   seconds — and the roster page rebuilds automatically.

## Update your profile later

Already merged once and want to change your intro? Same flow, one
difference — the branch prefix and the verb:

1. In your fork, create a branch named `fix/<your-username>`.
2. Edit **your own** `profiles/<your-github-username>.md`.
3. Commit, open a pull request to `main` — CI verifies you modify
   exactly one file (yours) and the robot squash-merges it.

`docs/*` = add your profile for the first time; `fix/*` = update your
own. Mixing them up fails the check with a hint pointing you to the
right prefix.

## The contract CI enforces

Pull requests from `docs/*` and `fix/*` branches are validated by
`scripts/check_profiles.py` (see the run's Summary page for the report):

- the PR changes **exactly one file**;
- the file is **`profiles/<your-github-username>.md`** — named after the
  PR author's own login, and nobody else's. The match is
  **case-sensitive**: copy your username's exact casing,
  e.g. `HarleyZHOUzzz` → `profiles/HarleyZHOUzzz.md`;
- on a `docs/*` branch the file must be **newly added**; on a `fix/*`
  branch it must be a **modification of your existing profile**;
- the content starts with a `# Title` line, for example, `# Robert He`.

Anything else fails the check with an explanation, and the robot will not
merge it.

Maintainers (maintain/admin permission) and the `PROFILE_BYPASS` list in
the workflow skip these per-PR rules; PRs from other branch prefixes are
not auto-merged and are reviewed manually.

## For maintainers

```bash
python scripts/check_profiles.py       # run the same checks locally
python scripts/build_site.py           # preview the roster page locally
```

The roster page is built by CI and deployed as a Pages artifact;
`docs/` is generated output, gitignored, and never committed.
