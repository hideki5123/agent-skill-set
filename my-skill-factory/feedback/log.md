# Feedback Log

<!-- Append new entries at the top. Do not edit previous entries. -->

## 2026-05-04T14:52:59Z
- **Skill Version**: (factory v current)
- **Task**: Create new skill scoping gdrive-cli to user's private Google Drive
- **Outcome**: partial-success
- **Rating**: 2/5
- **Corrections**:
  - User asked to rename `gdrive-private` → `my-gdrive` after install (skill name was decided unilaterally; should have confirmed naming before file creation given a name like "private" was a judgment call about the public-facing label).
  - User asked for concrete rclone authentication steps for the personal account, given that an existing remote (`tx-gdrive:`) is the user's *company* account. The first version had a generic setup walkthrough without addressing the specific pain point: the browser will auto-pick the already-signed-in company Gmail unless you actively force a different account.
- **Issues**:
  - Naming chosen without confirmation — auto-mode interpreted "minimize interruptions" too broadly for a user-visible label.
  - Auth section was generic Drive-config guidance copy-shaped from gdrive-cli; missed the actual concrete pain (forcing OAuth to a *different* Gmail when one is already authorized to rclone).
- **User Note**: "please change name for my-gdrive. Also give me how authenticate rclone for my private google drive since current auth is only for my company, I suppose."
---
