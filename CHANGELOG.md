# Changelog

## 0.1.11

What was understood: company talk treated two katakana characters followed by kanji as a registry name, so フィボナッチ数列 and グラタン皿 received the statute paragraph. A company name with no statute word also received it. Pytest before this change, on 0.1.10: 130 passed, 2 skipped. The live fixture made 31 e-Gov requests.

What changed: `pre_llm_call` adds the statute paragraph only on a statute question, or when an e-Gov tool was called in the previous turn. 条件 does not match. A company name does not add it. The decision is `turn_scope.domains`, copied into this plugin and not imported from another. Pytest on this commit: 129 passed, 6 skipped. The live fixture made 31 e-Gov requests.

## 0.1.10

What was understood: `pre_llm_call` added the statute paragraph on every turn, including a settings question. Pytest before this change, on 0.1.9: 129 passed, 2 skipped. The live fixture made 31 e-Gov requests.

What changed: that paragraph is added only on company talk or a statute question. 条 inside 条件 does not count. Other turns get no extra context. The paragraph text is unchanged. Pytest on this commit: 130 passed, 2 skipped. The live fixture made 31 e-Gov requests.

## 0.1.9

What was understood: `令` was a statute marker except immediately after `辞`. `指令` was not blocked. Pytest before this change, on 0.1.8: 129 passed, 2 skipped. The live fixture made 31 e-Gov requests.

What changed: `令` after `指` is not a statute marker. `指令` is blocked. `施行令`, `政令`, and `命令` are not. Pytest on this commit: 129 passed, 2 skipped. The live fixture made 31 e-Gov requests.

## 0.1.8

What was understood: the title gate matched `令`, so `辞令` was not blocked. `条件` and `必要条件` were already blocked. `第32条`, `条約`, `条例`, and `施行令` were already allowed. Pytest before this change, on 0.1.7: 129 passed, 2 skipped.

What changed: `令` immediately after `辞` is not a statute marker. `辞令` is blocked. `施行令`, `政令`, and `命令` are not. A text-mode search and `egov_law_article` stay unblocked. Pytest on this commit: 129 passed, 2 skipped. The live fixture made 31 e-Gov requests.

## 0.1.7

What was understood: a title search was blocked when the query did not contain 法, 令, 条例, 規則, 憲法, or 条. `条件` contains 条, so it was not blocked. An empty query and a company name were already blocked. `mode=text` and `egov_law_article` were not blocked. Pytest on this commit: 129 passed, 2 skipped. The live e-Gov fixture made 31 requests.

What changed: 条 inside 条件 is not treated as a statute. `条件` and `必要条件` are blocked. `第32条`, `条約`, `条例`, and `労働基準法施行令` are not. The block text is unchanged.

## 0.1.6

What was understood: `egov_law_article` already returns `source.url`. The first section said this version does not change that tool. On a small model `egov_law_search` was called with an empty query, the tool rejected it, and the reply had no article URL and did not say a URL was guessed. Pytest on this commit: 124 passed, 6 skipped. The live e-Gov fixture made 31 requests.

What changed: `pre_tool_call` blocks `egov_law_search` before HTTP when `query` is empty, or when `mode` is title and the query does not contain 法, 令, 条例, 規則, 憲法, or 条. A text-mode search is not blocked. `egov_law_article` is not blocked. The block says no article URL was written and a URL was not guessed, and to call `egov_law_article` when a tool result already names a law and an article. The first section leads with that gate.

## 0.1.5

What was understood: `egov_law_article` already returns the article and `source.url`. e-Gov 法令検索 already returns that URL. This version does not change the tool. A written line that presented "open the article URL" as this version's increment described the existing tool. On a small model the skill body was not opened, `egov_law_article` was not called, and the reply had no article URL.

What changed: the skill and `pre_llm_call` say to copy `source.url` only when a tool result already has `law_title` and `article`. When `article` is null, do not guess and do not write an e-Gov URL. The first section says opening an article URL is the existing tool, not this version's increment.

## 0.1.4

What was understood: `egov_law_article` already returns one article and `source.url`. A subsidy guideline that names a statute was not part of the skill, so the model was not told to open only the article the guideline names.

What changed: the `read-law` skill tells the model to call `egov_law_article` when `subsidies_detail` returns a `law_title` and an `article`, and to copy `source.url`. When the article number is absent, the model is told not to guess one and not to say the corporation is eligible.

## 0.1.3

The first sentence Tool Search shows now uses the words a person would ask with. A sentence that starts by describing the mechanism is not found, and the model falls through to the built-in web_search.

The `read-law` skill no longer sets requires_toolsets. With Tool Search left at its default, this plugin's tools are hidden, and the skill now stays in the model's skill list. Its description tells the model to find the e-Gov tools with tool_search before web_search.

The aliases law_id, law_name, q, number, and article_number, and date separators, are accepted. fulltext, a date that is too early, and an `egov_law_search` limit outside 1 to 50 are refused with a fix and an example, and the caller's value is not copied into the message. That search limit used to be clamped. `egov_law_revisions` still clamps its limit to 1 to 50.

Tool descriptions now name laws a person asks about (the Civil Code on a sale or a lease, the childcare leave act, the National Public Service Act for civil servants) and say that an article number is passed as digits (the example is 32). The schemas no longer mark `query`, `law`, or `article` as required and no longer list `mode` as an enum; an empty query or an unknown mode is refused by the tool with `bad_argument`.

## 0.1.0

Read search, article text, and revision history from the e-Gov law API v2. Read-only. The text is not stored.

## 0.1.1

An empty body, or a response with no article for that date, is not treated as a changed article. A failure on the comparison date is returned as an error.

## 0.1.2

Tool descriptions say what each call returns, when to use it, and that it is read-only. `bad_argument` adds `field`, `problem`, `expected`, and `allowed_fields`, and does not repeat the caller's value. A paragraph that cannot be read is `field=paragraph`. `egov_law_article` returns `source.retrieved_at`, `source.url`, and `source.as_of` (the date the wording is as of). `egov_law_search` and `egov_law_revisions` return `source.retrieved_at` and `source.url`, and do not return `source.as_of`. On a search, `source.url` is the e-Gov top page; each result has its own `url`. The `read-law` skill asks the model to copy the fields the tool returned and not to write an article from memory when the tool was not called. The skill is registered with `metadata.hermes.requires_toolsets: [egov_law]`.

A later run of five models, 40 sessions (39 answered) and 158 turns, counted: `bypass` 22 (a built-in tool such as web_search, read_file, or terminal was used instead of this plugin), `missing_tool` 6 (the reply did not call the plugin tool that turn required), `unsourced_claim` 1 (the reply said the text had been fetched without a plugin call), `wrong_tool` 15 (a plugin tool the turn did not need), `omitted_attribution` 2 (the plugin result succeeded, and the reply had neither 出典 nor laws.e-gov.go.jp).
