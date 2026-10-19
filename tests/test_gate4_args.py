"""Argument shapes from the 2026-10-12 e-Gov sessions."""
import json

import pytest


class _KeywordMiss:
    def __init__(self, error_type):
        self._error_type = error_type

    def get(self, path, params=None):
        raise self._error_type("not_found", "none", api_code="404001")


def test_law_id_and_number_reach_the_article_call(plugin, monkeypatch):
    # article_abbrev_en sent law_id and number; Hermes never called the tool
    seen = {}

    def fake(client, law, article, **kwargs):
        seen["law"] = law
        seen["article"] = article
        return {"folded": True}

    monkeypatch.setattr(plugin.laws, "get_article", fake)
    out = json.loads(plugin.tools.HANDLERS["egov_law_article"]({
        "law_id": "322AC0000000049",
        "number": "32",
    }))
    assert out["folded"] is True
    assert seen == {"law": "322AC0000000049", "article": "32"}


def test_slash_date_before_2017_is_refused_without_the_input(plugin):
    # article_bad_date_en sent as_of 2000-01-01; slashes are the same day
    out = json.loads(plugin.tools.HANDLERS["egov_law_article"]({
        "law": "労基法",
        "article": "32",
        "as_of": "2000/01/01",
    }))
    text = json.dumps(out, ensure_ascii=False)
    assert out["ok"] is False
    assert out["error_type"] == "bad_argument"
    assert "2017-04-01" in out["error"]
    assert "2000" not in text
    assert "2000/01/01" not in text


def test_dotted_date_is_a_real_date(plugin):
    assert plugin.laws._check_date("2018.01.01", "as_of") == "2018-01-01"
    assert plugin.laws._check_date("２０１８/０１/０１", "as_of") == "2018-01-01"


def test_fulltext_mode_says_which_mode_to_use(plugin):
    # search_bad_mode_ja sent mode fulltext. Body search is mode text, not a silent rewrite.
    with pytest.raises(plugin.client.EgovError) as caught:
        plugin.laws.search_laws(_KeywordMiss(plugin.client.EgovError), "時間外労働", mode="fulltext")
    assert "title or text" in caught.value.message
    assert "fulltext" not in caught.value.message
    assert "mode='text'" in caught.value.hint


def test_unknown_mode_and_limit_zero_name_the_fix(plugin):
    with pytest.raises(plugin.client.EgovError) as mode_error:
        plugin.laws.search_laws(_KeywordMiss(plugin.client.EgovError), "民法", mode="SIDEWAYS")
    assert "title or text" in mode_error.value.message
    assert "SIDEWAYS" not in mode_error.value.message
    with pytest.raises(plugin.client.EgovError) as limit_error:
        plugin.laws.search_laws(_KeywordMiss(plugin.client.EgovError), "民法", limit=0)
    assert limit_error.value.message == (
        "limit is not accepted (out_of_range). Expected: an integer from 1 to 50, for example 10."
    )
    assert "10" in limit_error.value.hint
    wrapped = json.loads(plugin.tools.HANDLERS["egov_law_search"]({"query": "民法", "limit": 0}))
    assert wrapped["ok"] is False
    assert wrapped["error_type"] == "bad_argument"
    assert wrapped["error"] == limit_error.value.message
    assert "for example 10" in wrapped["next_step"]
