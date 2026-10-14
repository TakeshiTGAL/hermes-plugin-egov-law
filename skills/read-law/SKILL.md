---
name: read-law
description: "Source fields for a Japanese statute fetched from e-Gov: source.retrieved_at, source.url, and source.as_of when egov_law_article returned it."
metadata:
  hermes:
    requires_toolsets:
      - egov_law
---

When you quote an article, an amendment date, or a law number, copy `source.attribution`, `source.retrieved_at`, and `source.url` into the reply. Copy `source.as_of` only when the tool returned it. That key is the date the wording is as of, and only `egov_law_article` returns it. `egov_law_search` and `egov_law_revisions` do not. On a search, `source.url` is the e-Gov top page (`https://laws.e-gov.go.jp/`); each result's `url` is that law's page.

If you did not call `egov_law_article`, `egov_law_search`, or `egov_law_revisions`, say you did not fetch it. Do not write an article from memory, and do not say it came from e-Gov. 別表 and forms are `not_covered`; give the page URL from the error and do not invent the table. This plugin is read-only and does not give legal advice.

条文や改正日や法令番号を伝えるときは、道具が返した `source.attribution`、`source.retrieved_at`、`source.url` を一緒に書く。`source.as_of` は返ったときだけ書く。それは文言の時点で、`egov_law_article` だけが返す。検索の `source.url` は e-Gov のトップ頁で、各結果の `url` がその法令の頁である。道具を呼んでいないときは、取得していないと言う。記憶から条文を書かない。
