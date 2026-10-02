"""Live tests against https://laws.e-gov.go.jp/api/2 (the real service).

Run only the offline suite with:  pytest -m "not live"
"""

from __future__ import annotations

import json

import pytest

from conftest import call

pytestmark = pytest.mark.live


def test_search_labor_standards_act(live):
    result = call(live, "egov_law_search", query="労働基準法")
    assert result["results"][0]["law_num"] == "昭和二十二年法律第四十九号"


def test_labor_standards_act_article_32(live):
    result = call(live, "egov_law_article", law="労働基準法", article="第三十二条")
    assert "一週間について四十時間" in result["text"]
    assert result["law_num"] == "昭和二十二年法律第四十九号"
    assert result["url"] == "https://laws.e-gov.go.jp/law/322AC0000000049"


@pytest.mark.parametrize("article", ["第32条", "32条", "32", "三十二条", "第三十二条"])
def test_article_number_spellings(live, article):
    result = call(live, "egov_law_article", law="労基法", article=article)
    assert result["article"] == "第三十二条"


def test_search_personal_information_act(live):
    result = call(live, "egov_law_search", query="個人情報の保護に関する法律")
    assert result["results"][0]["law_num"] == "平成十五年法律第五十七号"


def test_unknown_law_name_is_zero_results(live):
    result = call(live, "egov_law_search", query="架空法令テスト")
    assert result["total_matches"] == 0 and result["message"].startswith("0 laws found")


def test_unknown_article(live):
    result = call(live, "egov_law_article", law="労働基準法", article="第九九九九条")
    assert result["error_type"] == "article_not_found"


def test_unreachable_host_is_an_error_not_an_exception(plugin):
    client = plugin.client.EgovClient(base_url="https://egov-law-test.invalid/api/2", timeout=3)
    result = json.loads(plugin.tools.make_handlers(client)["egov_law_article"]({"law": "労基法", "article": "32"}))
    assert result["error_type"] in ("network", "timeout")
    assert "egov-law-test.invalid" in result["error"]


def test_as_of_before_and_after_an_amendment(live):
    past = call(live, "egov_law_article", law="労基法", article="32", as_of="2018-01-01")
    assert past["law_version"]["in_force_since"] <= "2018-01-01"
    assert "一週間について四十時間" in past["text"]


def test_paragraph_out_of_range_says_how_many(live):
    result = call(live, "egov_law_article", law="322AC0000000049", article="36", paragraph=99)
    assert result["error_type"] == "paragraph_not_found"
    assert result["error"].startswith("労働基準法 第三十六条 has ")
    assert "paragraph between 1 and" in result["next_step"]


def test_not_covered_gives_the_page(live):
    result = call(live, "egov_law_article", law="労基法", article="別表第一")
    assert result["error_type"] == "not_covered"
    assert "https://laws.e-gov.go.jp/law/322AC0000000049" in result["next_step"]


def test_revisions_point_to_compare_with(live):
    result = call(live, "egov_law_revisions", law="労基法")
    assert "compare_with=" in result["next_step"]
    rows = result["scheduled_amendments"] + result["earlier_versions"]
    assert all("kind" not in row for row in rows)
    assert any(row.get("title_names_this_law") is True for row in rows)


def test_revisions(live):
    result = call(live, "egov_law_revisions", law="労基法")
    assert result["law_num"] == "昭和二十二年法律第四十九号"
    assert result["in_force_now"]["status"] == "in force now"
    assert result["total_versions"] >= len(result["earlier_versions"]) > 0


def test_some_aliases_live(live):
    for alias, title in {"個情法": "個人情報の保護に関する法律", "下請法": "製造委託等に係る中小受託事業者に対する代金の支払の遅延等の防止に関する法律",
                         "パワハラ防止法": "労働施策の総合的な推進並びに労働者の雇用の安定及び職業生活の充実等に関する法律"}.items():
        assert call(live, "egov_law_search", query=alias, limit=1)["results"][0]["law_title"] == title, alias


def test_compare_with_same_wording(live):
    result = call(live, "egov_law_article", law="労基法", article="32", compare_with="2018-01-01")
    assert result["comparison"]["changed"] is False


def test_original_supplementary_provision_on_wage_claims(live):
    result = call(live, "egov_law_article", law="労基法", article="附則第百四十三条", paragraph=3)
    assert "三年間" in result["text"]
