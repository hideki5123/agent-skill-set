# Feedback Log

<!-- Append new entries at the top. Do not edit previous entries. -->

## 2026-05-08T03:30Z
- **Skill Version**: 1.2.0
- **Task**: Update notion-cli to support agenix/sops-nix file-based token resolution. Added NOTION_API_KEY alias + NOTION_TOKEN_FILE (path-to-file) to the resolution chain. Mirrored logic in preflight.ts. Added section 4b to references/auth-setup.md with concrete agenix / sops-nix / 1Password / pass walkthroughs and a "why a file beats a plain env-var on Nix" rationale. Bumped to v1.2.0, installed, committed (`72547b7`), pushed, verified in fresh CLI.
- **Outcome**: success
- **Rating**: 2/5
- **Corrections**: none mid-session
- **Issues**:
  - Self-introduced bug: first write of `getToken()`'s trailing-whitespace trim contained U+0085 / U+00A0 chars inside a regex character class (`/[\r\n  ]+$/`), which deno's parser rejected as an unterminated regex. Fixed via python rewrite to `raw.trim()`. Should have type-checked the script before the smoke test, or written the simpler `.trim()` form first.
  - Latent bug surfaced: preflight.ts had been calling `Deno.env.get("HOME")` since v1.0.0, but the documented permission scope was `--allow-env=NOTION_TOKEN` (singular), which excludes `HOME`. The bare `--allow-env` (no list) form had been masking this. Caught at preflight smoke test, added `HOME,USERPROFILE` to the scope. Should have caught in v1.0.0.
  - Rough edges in description: the marketplace.json description is auto-truncated at ~250 chars by install_skill.py and ends mid-word ("list/append/delete b"). Cosmetic, but unfortunate.
- **User Note**: "2" (no elaboration provided)
---
