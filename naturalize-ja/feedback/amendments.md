# Amendment History

## AMD-001 — 2026-08-26
- **Pattern**: ハウススタイルのカタカナ→英語を一括置換すると、置換順序次第で英字連結 (EMBadge / 1Dialog / StatusDropdown) が発生する。
- **Evidence**: 2026-08-20 セッション (ROMS-4831 スペック全体の一括変換): 約20語の変換で複合語の事前置換 (EMバッジ→EM Badge 等) が必須と判明。事後grepで連結ゼロを確認する手順も確立。
- **Change**: references/tech-doc-house-style.md に §5「一括置換の順序規則」を追加 (複合語の事前置換→複合カタカナ語→単語の長い順、事前走査/事後検証のgrep付き)。§4 手順2から参照。
- **Files Modified**: references/tech-doc-house-style.md, SKILL.md (version)
- **Version Bump**: 1.2.0 → 1.3.0
- **Git Commit**: pending
- **Status**: applied — monitoring
---
