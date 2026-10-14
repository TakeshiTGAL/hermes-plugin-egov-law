# Changelog

## 0.1.0

e-Gov 法令 API v2 から、法令の検索・条文・改正履歴を読む。読み取りだけで、本文は保存しない。

## 0.1.1

空の本文や、日付で条文が無い応答を、条文が変わった結果と取り違えない。比較日の障害はエラーとして返す。

## 0.1.2

Tool descriptions say what each call returns, when to use it, and that it is read-only. `bad_argument` adds `field`, `problem`, `expected`, and `allowed_fields`, and does not repeat the caller's value. A paragraph that cannot be read is `field=paragraph`. `egov_law_article` returns `source.retrieved_at`, `source.url`, and `source.as_of` (the date the wording is as of). `egov_law_search` and `egov_law_revisions` return `source.retrieved_at` and `source.url`, and do not return `source.as_of`. On a search, `source.url` is the e-Gov top page; each result has its own `url`. The `read-law` skill asks the model to copy the fields the tool returned and not to write an article from memory when the tool was not called. The skill is registered with `metadata.hermes.requires_toolsets: [egov_law]`.

A later run of five models, 40 sessions (39 answered) and 158 turns, counted: bypass 22/158 (13.9%), omitted attribution 2/158 (1.3%), unsourced claim 1/158 (0.6%), wrong tool 15/158 (9.5%). A recount that said 142 turns and 42 bypasses is not in the saved summary, so it is not listed here.

道具の説明に、何を返すか・いつ使うか・読み取りだけかを書いた。`bad_argument` には `field`・`problem`・`expected`・`allowed_fields` を足し、入力の値は載せない。項が読めないときは `field=paragraph`。条文は `source.retrieved_at`・`source.url`・文言の時点 `source.as_of` を返す。検索と改正履歴は取得時刻と URL を返し、`source.as_of` は返さない。検索の `source.url` は e-Gov のトップ頁で、各結果の `url` がその法令の頁である。`read-law` の skill は、返った欄を写すことと、呼んでいないときに記憶から条文を書かないことをモデルに求める。skill は `metadata.hermes.requires_toolsets: [egov_law]` で登録する。

同じあとからの記録は、5 モデル・40 セッション（答えたもの 39）・ターン 158。迂回 22/158（13.9%）、出典落ち 2/158（1.3%）、呼んでいない取得の名乗り 1/158（0.6%）、要らない道具 15/158（9.5%）。ターン 142・迂回 42 という数え直しは、残っている集計には無いので書かない。
