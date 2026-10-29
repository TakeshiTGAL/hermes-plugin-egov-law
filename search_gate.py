"""Block an e-Gov title search that does not name a statute.

Process-local. Other plugins are not imported. A text-mode search is left
alone, because a phrase inside a law is not a law title. An empty query is
blocked in every mode.
"""

from __future__ import annotations

import re

# ``条`` inside 条件 is not a statute. ``令`` after 辞 or 指 is not a statute.
# 辞令 and 指令 are blocked. 第32条, 条約, 条例, 施行令, 政令, and 命令 still match.
_STATUTE = re.compile(r"法|(?<![辞指])令|条例|規則|憲法|条(?!件)")

_BLOCK = (
    "No article URL was written. The query did not name a statute, so egov_law_search was not run. "
    "A URL was not guessed. "
    "When a tool result already names a law title and an article, call egov_law_article and copy source.url."
)


def block(tool_name: str, args: dict) -> dict | None:
    if tool_name != "egov_law_search":
        return None
    query = str((args or {}).get("query") or "").strip()
    mode = str((args or {}).get("mode") or "title").strip().lower()
    if query and (mode == "text" or _STATUTE.search(query)):
        return None
    return {"action": "block", "message": _BLOCK}
