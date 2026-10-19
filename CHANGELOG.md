# Changelog

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
