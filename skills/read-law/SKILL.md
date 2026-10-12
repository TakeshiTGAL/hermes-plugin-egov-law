---
name: read-law
description: Read one Japanese statute from e-Gov and quote it only with the tool's source fields.
---

条文や発言を伝えるときは、この欄を一緒に伝える。道具を呼んでいないときは、取得していないと言う。記憶から条文を書かない。

When you quote an article, an amendment date, or a law number, copy `source.attribution`, `source.retrieved_at`, `source.url`, and `source.as_of` (when the tool returned it) into the reply. Those fields are the time the text was fetched, the official e-Gov URL, and the date the wording is as of.

If you did not call `egov_law_article`, `egov_law_search`, or `egov_law_revisions`, say you did not fetch it. Do not write an article from memory, and do not say it came from e-Gov. 別表 and forms are `not_covered`; give the page URL from the error and do not invent the table. This plugin is read-only and does not give legal advice.
