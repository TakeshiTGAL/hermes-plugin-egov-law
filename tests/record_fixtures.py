"""Re-record the e-Gov responses the offline tests replay.

    python tests/record_fixtures.py            # tool-call fixtures (about 35 requests, 1 per second)
    python tests/record_fixtures.py --aliases  # titles behind the built-in short names (about 25 requests)
    python tests/record_fixtures.py --missing  # only fetch URLs that have no recorded response yet

Runs the same tool calls as tests/test_offline.py against the live API and
stores every response under tests/fixtures/<sha1(url)>.json. Article fixtures
are small (one article each), so the directory stays well under 1 MB.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import FIXTURES, fixture_name, load_plugin  # noqa: E402

# (tool, args) pairs; keep in sync with test_offline.py.
CALLS = [
    ("egov_law_search", {"query": "労働基準法"}),
    ("egov_law_search", {"query": "個人情報の保護に関する法律"}),
    ("egov_law_search", {"query": "架空法令テスト"}),
    ("egov_law_search", {"query": "個情法"}),
    ("egov_law_search", {"query": "年次有給休暇", "mode": "text", "limit": 3}),
    ("egov_law_search", {"query": "架空法令テスト", "mode": "text"}),
    ("egov_law_article", {"law": "労基法", "article": "三十二条"}),
    ("egov_law_article", {"law": "労働基準法", "article": "第九九九九条"}),
    ("egov_law_article", {"law": "民法", "article": "第415条"}),
    ("egov_law_article", {"law": "322AC0000000049", "article": "32の2", "paragraph": 2}),
    ("egov_law_revisions", {"law": "個情法", "limit": 3}),
    ("egov_law_article", {"law": "労基法", "article": "附則第143条"}),
    ("egov_law_article", {"law": "労基法", "article": "別表第一"}),
    ("egov_law_article", {"law": "パワハラ防止法", "article": "30の2"}),  # renumbered on 2026-10-01
    ("egov_law_revisions", {"law": "415AC0000000058"}),  # repealed on 2022-04-01
    ("egov_law_article", {"law": "415AC0000000058", "article": "1"}),
]


def main() -> None:
    plugin = load_plugin()
    FIXTURES.mkdir(exist_ok=True)

    seen = []

    missing_only = "--missing" in sys.argv

    def recording_transport(url, timeout):
        path = FIXTURES / fixture_name(url)
        if missing_only and path.is_file():
            record = json.loads(path.read_text(encoding="utf-8"))
            return record["status"], json.dumps(record["body"], ensure_ascii=False).encode("utf-8")
        seen.append(url)
        print("fetch", url)
        status, body = plugin.client.urllib_transport(url, timeout)
        record = {"url": url, "status": status, "body": json.loads(body.decode("utf-8"))}
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return status, body

    client = plugin.client.EgovClient(transport=recording_transport, min_interval=1.0)
    handlers = plugin.tools.make_handlers(client)
    if "--aliases" in sys.argv:
        record_aliases(plugin, client)
        print("requests:", len(seen))
        return
    for name, args in CALLS:
        result = json.loads(handlers[name](args))
        print(name, json.dumps(args, ensure_ascii=False), "->", "error" if "error" in result else "ok")
    print("requests:", len(seen))


def record_aliases(plugin, client) -> None:
    titles = {}
    for alias, law_id in plugin.laws.ALIASES.items():
        laws = client.get("laws", {"law_id": law_id, "limit": 1}).get("laws") or []
        titles[alias] = (laws[0].get("revision_info") or {}).get("law_title") if laws else None
    (FIXTURES / "alias_titles.json").write_text(json.dumps(titles, ensure_ascii=False, indent=1) + "\n",
                                                encoding="utf-8")


if __name__ == "__main__":
    main()
