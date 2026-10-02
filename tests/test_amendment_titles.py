"""Regression table for title_names_this_law / follow_up_of, on real e-Gov data.

Each row: (law ID, amending law number, does the amending law's title name this law as a word of its
own, the law named before 「の施行に伴う」 or None). Expected values were written by hand from the
titles, not computed by the code under test. The offline test uses the titles recorded in
tests/fixtures/amending_titles.json (re-record with tests/record_amending_titles.py); the live test
checks the same table against e-Gov now.
"""

from __future__ import annotations

import json

import pytest

from conftest import FIXTURES, call

EXPECTED = [
    # 労働基準法: a reform bundle named after another law, 働き方改革関連法, follow-ups, its own amendment
    ("322AC0000000049", "令和八年法律第六十号", False, None),
    ("322AC0000000049", "平成三十年法律第七十一号", False, None),
    ("322AC0000000049", "令和八年法律第四十六号", False, "民法等の一部を改正する法律"),
    ("322AC0000000049", "令和二年法律第十三号", True, None),
    ("322AC0000000049", "平成二十七年法律第三十一号", False, None),       # 国民健康保険法等…
    # 下請法: amended under its former title (下請代金支払遅延等防止法)
    ("331AC0000000120", "令和七年法律第四十一号", True, None),
    # 次世代育成支援対策推進法: named second, after 及び
    ("415AC0000000120", "令和六年法律第四十二号", True, None),
    ("415AC0000000120", "令和四年法律第七十六号", False, "こども家庭庁設置法"),
    ("415AC0000000120", "令和四年法律第十二号", False, None),           # 雇用保険法等…
    # 保険法 / 雇用保険法: 保険法 is inside 雇用保険法
    ("420AC0000000056", "平成二十九年法律第四十五号", False, "民法の一部を改正する法律"),
    ("349AC0000000116", "令和六年法律第二十六号", True, None),
    ("349AC0000000116", "令和三年法律第五十八号", True, None),          # 育児…及び雇用保険法の一部…
    ("349AC0000000116", "令和二年法律第五十四号", True, None),          # …ための雇用保険法の臨時特例等…
    # 健康保険法 / 国民健康保険法
    ("211AC0000000070", "令和八年法律第三十一号", True, None),
    ("211AC0000000070", "令和五年法律第三十一号", True, None),          # …構築するための健康保険法等…
    ("211AC0000000070", "令和七年法律第七十四号", False, None),
    ("333AC0000000192", "令和八年法律第三十一号", False, None),         # 健康保険法等… does not name 国保法
    ("333AC0000000192", "平成二十七年法律第三十一号", True, None),
    # 銀行法 / 日本銀行法
    ("356AC0000000059", "令和三年法律第四十六号", True, None),
    ("356AC0000000059", "平成二十九年法律第四十九号", True, None),
    ("356AC0000000059", "令和元年法律第七十一号", False, "会社法の一部を改正する法律"),
    ("409AC0000000089", "令和四年法律第六十八号", False, "刑法等の一部を改正する法律"),
    ("409AC0000000089", "平成二十三年法律第七十四号", False, None),
    # 民法: 成年後見 (…ための民法及び…), its own amendments, a follow-up of another law
    ("129AC0000000089", "平成二十八年法律第二十七号", True, None),
    ("129AC0000000089", "令和八年法律第四十五号", True, None),
    ("129AC0000000089", "令和七年法律第五十七号", False, "譲渡担保契約及び所有権留保契約に関する法律"),
    ("129AC0000000089", "令和三年法律第六十一号", False, None),         # 国家公務員法等…
    # 国民年金法 / 厚生年金保険法: the 2025 pension reform names only 国民年金法
    ("334AC0000000141", "令和七年法律第七十四号", True, None),
    ("334AC0000000141", "令和二年法律第四十号", True, None),
    ("329AC0000000115", "令和七年法律第七十四号", False, None),
    ("329AC0000000115", "平成二十八年法律第六十六号", False, None),     # 確定拠出年金法等…
    # More labour and social-insurance laws
    ("347AC0000000057", "令和七年法律第三十三号", True, None),
    ("347AC0000000057", "平成三十年法律第七十八号", False, None),
    ("419AC0000000128", "平成三十年法律第七十一号", False, None),
    ("334AC0000000137", "令和四年法律第六十八号", False, "刑法等の一部を改正する法律"),
    ("403AC0000000076", "令和六年法律第四十二号", True, None),
    ("403AC0000000076", "令和七年法律第六十三号", False, None),
    ("360AC0000000088", "令和七年法律第三十三号", False, None),
    ("322AC0000000050", "令和八年法律第六十号", True, None),
    ("322AC0000000050", "平成二十六年法律第六十九号", False, "行政不服審査法"),
    ("347AC0000000113", "令和元年法律第二十四号", False, None),
    ("405AC0000000076", "平成三十年法律第七十一号", False, None),
    ("346AC0000000068", "令和四年法律第十二号", False, None),
    ("341AC0000000132", "令和七年法律第六十三号", True, None),
    ("341AC0000000132", "令和五年法律第五十六号", False, None),
]


def check(plugin, data, only=None):
    failures = []
    for law_id, num, names, follow in EXPECTED:
        if only is not None and law_id not in only:
            continue
        law = data[law_id]
        rows = [a for a in law["amendments"] if a["num"] == num]
        assert rows, f"{law_id}: no amendment {num} in the data"
        title = rows[0]["title"]
        got = (plugin.laws.title_names_this_law(title, law["titles"]), plugin.laws.follow_up_of(title))
        if got != (names, follow):
            failures.append(f"{law_id} {num} {title}: expected {(names, follow)}, got {got}")
    assert not failures, "\n".join(failures)


def test_recorded_titles(plugin):
    check(plugin, json.loads((FIXTURES / "amending_titles.json").read_text(encoding="utf-8")))


def test_table_covers_twenty_laws():
    assert len({law_id for law_id, *_ in EXPECTED}) >= 20


@pytest.mark.parametrize("amending,titles,expected", [
    ("雇用保険法等の一部を改正する法律", ["保険法"], False),
    ("国民健康保険法の一部を改正する法律", ["健康保険法"], False),
    ("日本銀行法の一部を改正する法律", ["銀行法"], False),
    ("健康保険法等の一部を改正する法律", ["健康保険法"], True),
    ("社会経済の変化を踏まえた年金制度の機能強化のための国民年金法等の一部を改正する等の法律", ["国民年金法"], True),
    ("子ども・子育て支援法等の一部を改正する法律", ["子育て支援法"], False),
])
def test_word_boundary(plugin, amending, titles, expected):
    assert plugin.laws.title_names_this_law(amending, titles) is expected


@pytest.mark.live
def test_live_titles(plugin, live):
    from conftest import LIVE_REQUESTS

    def counted(url, timeout):
        LIVE_REQUESTS.append(url)
        return plugin.client.urllib_transport(url, timeout)

    client = plugin.client.EgovClient(transport=counted, min_interval=1.0)
    data = {}
    sample = ["322AC0000000049", "331AC0000000120", "334AC0000000141", "333AC0000000192"]  # keep the live load small
    for law_id in sample:
        revisions = client.get(f"law_revisions/{law_id}").get("revisions") or []
        data[law_id] = {
            "titles": sorted({r.get("law_title") for r in revisions if r.get("law_title")}),
            "amendments": [{"num": r.get("amendment_law_num"), "title": r.get("amendment_law_title")}
                           for r in revisions],
        }
    check(plugin, data, only=set(sample))
