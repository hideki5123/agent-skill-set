# Amendment History

## AMD-001 — 2026-08-26
- **Pattern**: Attachments needed on Jira issues; neither jira-cli nor Atlassian MCP supports upload/delete, causing ad-hoc rediscovery of the REST path.
- **Evidence**: 2026-08-26 session (ROMS-4830): attached 12 screenshots + later deleted a video via raw REST after both toolchains lacked the capability.
- **Change**: Added "Attachments via REST" workflow (upload with X-Atlassian-Token: no-check, list, delete), comparison-table row, and quick-reference row.
- **Files Modified**: SKILL.md (When to Use CLI vs. MCP table, Quick Reference, Common Agent Workflows)
- **Version Bump**: (none) → 1.1.0
- **Git Commit**: 418302a
- **Status**: applied — monitoring
---
