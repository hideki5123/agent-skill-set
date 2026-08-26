# ui-spec-sim — BDD spec
# WHEN TO READ: スキル自体の監査・改修時のみ。通常実行では読まない。

Feature: UIスペック+シミュレーターの設計レビューループ

  Scenario: チケットからペア成果物を初回作成する
    Given ユーザーがデザインチケット (またはURL) を指定して起動した
    When スキルがチケット・親スペック・対象アプリの実UIコードを読む
    Then 実UIに忠実なモックを持つスペックHTML (D番号決定ログ・Qカード・文言一覧) と
      遷移カバレッジ付きシミュレーターHTMLが別artifactとして公開される

  Scenario: レビュー指摘を1ラウンドとして反映する
    Given 公開済みのスペックとシミュレーターがある
    When ユーザーが設計への指摘を送る
    Then 指摘は新しいD番号 (または D改) になり、スペック・シミュレーター・文言一覧が
      同時に更新され、headless検証と敵対的整合チェックを通ってから同じURLで再公開される

  Scenario: 「ボタンが効かない」報告が再現しない
    Given ユーザーがシミュレーターの不具合を報告した
    When headless再現でJSエラーなく該当フローが成功する
    Then バグではなく操作上の罠 (状態リセット・分かりにくい挙動) を特定し、
      罠自体を設計変更 (D) として潰す

  Scenario: 外部同期はチーム向け最小限に留める
    Given 設計が確定しユーザーが外部反映を求めた
    When Ticket/Confluence/Figmaへ同期する
    Then Ticketには蒸留テキストと製品状態スクショのみ (シミュレーター専用の絵・
      録画・リンクは含めない)、ConfluenceはliteralアンカーでSurgical edit、
      Figmaはfigma-shot-boardに委譲する

  Scenario: 未決事項が残ったまま確定を求められる
    Given Qカードに未回答の案A/Bが残っている
    When ユーザーが「まとめて」と言う
    Then 推奨案を明示した上で未決として残し、勝手に確定させない
