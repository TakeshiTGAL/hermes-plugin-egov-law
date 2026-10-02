"""Re-record tests/fixtures/amending_titles.json: for each law in LAWS, its titles across versions and
the title, number and type of every amending law, straight from the e-Gov revisions API.

    python tests/record_amending_titles.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import FIXTURES, load_plugin  # noqa: E402

LAWS = {
    "322AC0000000049": "労働基準法",
    "331AC0000000120": "下請法（改題後の題名）",
    "415AC0000000120": "次世代育成支援対策推進法",
    "420AC0000000056": "保険法",
    "349AC0000000116": "雇用保険法",
    "211AC0000000070": "健康保険法",
    "333AC0000000192": "国民健康保険法",
    "356AC0000000059": "銀行法",
    "409AC0000000089": "日本銀行法",
    "129AC0000000089": "民法",
    "334AC0000000141": "国民年金法",
    "329AC0000000115": "厚生年金保険法",
    "347AC0000000057": "労働安全衛生法",
    "419AC0000000128": "労働契約法",
    "334AC0000000137": "最低賃金法",
    "403AC0000000076": "育児・介護休業法",
    "360AC0000000088": "労働者派遣法",
    "322AC0000000050": "労働者災害補償保険法",
    "347AC0000000113": "男女雇用機会均等法",
    "405AC0000000076": "パートタイム・有期雇用労働法",
    "346AC0000000068": "高年齢者雇用安定法",
    "341AC0000000132": "労働施策総合推進法",
}


def main() -> None:
    plugin = load_plugin()
    client = plugin.client.EgovClient()
    out = {}
    for law_id in LAWS:
        revisions = client.get(f"law_revisions/{law_id}").get("revisions") or []
        out[law_id] = {
            "titles": sorted({r.get("law_title") for r in revisions if r.get("law_title")}),
            "amendments": [
                {"num": r.get("amendment_law_num"), "title": r.get("amendment_law_title"),
                 "type": r.get("amendment_type")}
                for r in revisions
            ],
        }
        print(law_id, LAWS[law_id], len(revisions))
    (FIXTURES / "amending_titles.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
