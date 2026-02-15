# PR Guide

## Detecting the Repo's PR Template

Check for PR templates in order:

1. `.github/PULL_REQUEST_TEMPLATE/` directory (multiple templates)
2. `.github/pull_request_template.md` (single template)
3. `PULL_REQUEST_TEMPLATE.md` at repo root

If multiple templates exist (e.g. `other.md`, `robot_client.md`), pick the one that matches the change. For most changes, use `other.md`.

## Reading and Filling the Template

1. Read the template file
2. Fill in each section based on the actual changes made
3. For checklist items: mark with `[x]` if applicable, leave `[ ]` if not

## Creating the PR

```bash
gh pr create \
  --base <base-branch> \
  --title "<short title under 70 chars>" \
  --body "$(cat <<'EOF'
<filled template content>
EOF
)"
```

### Title Conventions

- Keep under 70 chars
- Be descriptive but concise
- No prefix needed (the PR template provides structure)

### Body

- Use the repo's PR template as the structure
- Fill in Motivation, Existing Behavior, New Behavior
- Complete the checklist honestly
- Keep descriptions concise - reviewers will read the diff
