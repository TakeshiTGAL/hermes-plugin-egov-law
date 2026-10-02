"""Offline tests: recorded e-Gov responses, synthetic law XML trees, and an injected dead host.

No network access. Re-record fixtures with `python tests/record_fixtures.py`.
"""

from __future__ import annotations

import json
import socket
import threading
import time
from pathlib import Path

import pytest
import yaml

from conftest import PLUGIN_DIR, call

TOOLS = ["egov_law_search", "egov_law_article", "egov_law_revisions"]


# --- Registration and manifest ---------------------------------------------

def registered_tools(plugin):
    names = []

    class Ctx:
        def register_tool(self, name, toolset, schema, handler, **kwargs):
            assert toolset == "egov_law"
            assert schema["name"] == name
            assert callable(handler)
            names.append(name)

    plugin.register(Ctx())
    return names


def test_register_wires_three_tools(plugin):
    assert registered_tools(plugin) == TOOLS


def test_manifest_matches_registrations(plugin):
    manifest = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text(encoding="utf-8"))
    assert manifest["name"] == "jp-egov-law"
    assert manifest["provides_tools"] == registered_tools(plugin)
    assert manifest["provides_hooks"] == []
    assert "requires_env" not in manifest
    assert manifest["version"] == plugin.version.__version__
    assert manifest["manifest_version"] == 2 and manifest["requires_hermes"] == ">=0.21.4"
    assert "built on the e-Gov Law API" in manifest["description"]
    assert "Unofficial" not in manifest["description"] and "affiliated" not in manifest["description"]
    assert not (PLUGIN_DIR / "catalog-entry.yaml").exists()  # the catalog entry lives in the Hermes repo


def test_schemas_are_complete(plugin):
    for schema in plugin.schemas.ALL_SCHEMAS:
        assert len(schema["description"]) > 150
        for name, spec in schema["parameters"]["properties"].items():
            assert spec.get("description"), f"{schema['name']}.{name} has no description"


# --- Criterion 3 on recorded responses -------------------------------------

def test_search_labor_standards_act(replay):
    result = call(replay, "egov_law_search", query="労働基準法")
    top = result["results"][0]
    assert top["law_title"] == "労働基準法"
    assert top["law_num"] == "昭和二十二年法律第四十九号"
    assert top["match"] == "exact title"
    assert top["url"] == "https://laws.e-gov.go.jp/law/322AC0000000049"
    assert "e-Gov法令検索" in result["source"]["attribution"]


def test_article_32_by_kanji_number_and_abbreviation(replay):
    result = call(replay, "egov_law_article", law="労基法", article="三十二条")
    assert result["article"] == "第三十二条"
    assert result["caption"] == "（労働時間）"
    assert "一週間について四十時間" in result["text"]
    assert "\n２　" in result["text"]  # second paragraph numbered even though e-Gov leaves ParagraphNum empty
    assert result["resolved_by"] == "abbreviation"


def test_search_personal_information_act(replay):
    result = call(replay, "egov_law_search", query="個人情報の保護に関する法律")
    assert result["results"][0]["law_num"] == "平成十五年法律第五十七号"


def test_common_short_name_alias(replay):
    result = call(replay, "egov_law_search", query="個情法")
    assert result["results"][0]["law_num"] == "平成十五年法律第五十七号"
    assert result["results"][0]["match"] == "alias"


def test_civil_code_article_with_items(replay):
    result = call(replay, "egov_law_article", law="民法", article="第415条")
    assert result["article"] == "第四百十五条"
    assert "\n　一　債務の履行が不能であるとき。" in result["text"]


def test_branch_article_paragraph_by_law_id(replay):
    result = call(replay, "egov_law_article", law="322AC0000000049", article="32の2", paragraph=2)
    assert result["article"] == "第三十二条の二第二項"
    assert result["text"].startswith("２　")
    assert result["resolved_by"] == "law ID"


def test_revisions_show_current_and_scheduled(replay):
    result = call(replay, "egov_law_revisions", law="個情法", limit=3)
    assert result["law_num"] == "平成十五年法律第五十七号"
    assert result["in_force_now"]["status"] == "in force now"
    assert result["next_amendment"] == result["scheduled_amendments"][0]
    dates = [row["in_force_since"] for row in result["scheduled_amendments"]]
    assert dates == sorted(dates)
    assert len(result["earlier_versions"]) <= 3 and len(result["scheduled_amendments"]) <= 3


def test_text_search_returns_snippets_without_markup(replay):
    result = call(replay, "egov_law_search", query="年次有給休暇", mode="text", limit=3)
    assert result["results"][0]["law_title"] == "労働基準法"
    for law in result["results"]:
        for snippet in law["snippets"]:
            assert "<span" not in snippet


# --- Criterion 4 on recorded responses -------------------------------------

def test_unknown_law_is_zero_results_not_error(replay):
    result = call(replay, "egov_law_search", query="架空法令テスト")
    assert result["total_matches"] == 0 and result["results"] == []
    assert result["message"].startswith("0 laws found")
    assert "mode='text'" in result["next_step"]


def test_unknown_phrase_in_text_mode(replay):
    result = call(replay, "egov_law_search", query="架空法令テスト", mode="text")
    assert result["returned_laws"] == 0
    assert result["message"].startswith("0 laws found")


def asof_requests(urls):
    return [url for url in urls if "/law_data/" in url and "asof=" in url]


def test_missing_article_is_explained(replay):
    result = call(replay, "egov_law_article", law="労働基準法", article="第九九九九条")
    assert result["error_type"] == "article_not_found"
    assert "第九千九百九十九条" in result["error"]
    assert "next_step" in result
    assert "existed_on" not in result and "moved or deleted" not in result["error"]
    # one look at the version before the current one (労基法: in force since 2026-07-17), no more
    assert asof_requests(replay["_transport"].urls) == [
        "https://laws.e-gov.go.jp/api/2/law_data/322AC0000000049?elm=MainProvision-Article_9999"
        "&json_format=full&asof=2026-07-16&omit_amendment_suppl_provision=true"]


def test_article_renumbered_by_the_current_amendment(replay):
    """パワハラ防止法 第三十条の二 is gone from the version in force since 2026-10-01 (recorded 2026-10-02)."""
    result = call(replay, "egov_law_article", law="パワハラ防止法", article="30の2")
    assert result["error_type"] == "article_not_found"
    assert "第三十条の二 existed in the version in force on 2026-09-30" in result["error"]
    assert "the amendment that took effect on 2026-10-01" in result["error"]
    assert "（令和七年法律第六十三号）) moved or deleted it." in result["error"]
    assert result["previous_caption"] == "（雇用管理上の措置等）"
    assert (result["existed_on"], result["changed_on"]) == ("2026-09-30", "2026-10-01")
    assert result["url"] == "https://laws.e-gov.go.jp/law/341AC0000000132"
    step = result["next_step"]
    assert "mode='text'" in step and "query='雇用管理上の措置等'" in step
    assert "https://laws.e-gov.go.jp/law/341AC0000000132" in step
    assert "Do not guess the new number" in step and "第" not in step  # no new number is offered
    assert len(asof_requests(replay["_transport"].urls)) == 1


def synthetic_law(missing_today=True, caption="（旧い見出し）"):
    """A transport for one law whose 第五条 is missing today and present on 2026-09-30."""
    urls = []

    def transport(url, timeout):
        urls.append(url)
        if "/law_revisions/" in url:
            return 200, json.dumps({"law_info": {"law_id": "341AC0000000132"}, "revisions": [
                {"amendment_enforcement_date": "2026-10-01", "current_revision_status": "CurrentEnforced",
                 "amendment_law_title": "改正法", "amendment_law_num": "令和七年法律第六十三号"},
                {"amendment_enforcement_date": "2026-04-01", "current_revision_status": "PreviousEnforced"},
            ]}, ensure_ascii=False).encode()
        if "asof=" not in url and missing_today or "asof=2026-07-01" in url:
            return 400, b'{"code":"400021","message":"elm"}'
        children = [node("ArticleTitle", "第五条"),
                    node("Paragraph", node("ParagraphNum"), node("ParagraphSentence", node("Sentence", "旧い文。")))]
        if caption:
            children.insert(0, node("ArticleCaption", caption))
        return 200, json.dumps({"law_info": {"law_id": "341AC0000000132", "law_num": "n"},
                                "revision_info": {"law_title": "テスト法"},
                                "law_full_text": node("Article", *children)}, ensure_ascii=False).encode()

    return transport, urls


def test_previous_version_is_checked_once_and_only_without_as_of(plugin):
    transport, urls = synthetic_law()
    handlers = plugin.tools.make_handlers(plugin.client.EgovClient(transport=transport))
    result = json.loads(handlers["egov_law_article"]({"law": "341AC0000000132", "article": "5", "paragraph": 2}))
    assert result["error_type"] == "article_not_found" and result["previous_caption"] == "（旧い見出し）"
    assert "第五条 existed in the version in force on 2026-09-30" in result["error"]
    assert "改正法（令和七年法律第六十三号）" in result["error"]
    assert sum("/law_revisions/" in url for url in urls) == 1 and len(asof_requests(urls)) == 1
    assert "Paragraph" not in asof_requests(urls)[0]  # the whole article, for its caption

    urls.clear()
    result = json.loads(handlers["egov_law_article"]({"law": "341AC0000000132", "article": "5",
                                                      "as_of": "2026-07-01"}))
    assert result["error_type"] == "article_not_found" and "previous_caption" not in result
    assert not any("/law_revisions/" in url for url in urls)


def test_previous_version_without_a_caption_points_to_its_wording(plugin):
    transport, _ = synthetic_law(caption="")
    handlers = plugin.tools.make_handlers(plugin.client.EgovClient(transport=transport))
    result = json.loads(handlers["egov_law_article"]({"law": "341AC0000000132", "article": "5"}))
    assert "previous_caption" not in result
    assert "as_of='2026-09-30'" in result["next_step"] and "mode='text'" in result["next_step"]


# --- Network failure: a host that accepts and never answers ----------------

@pytest.fixture
def silent_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(5)
    stop = threading.Event()
    held = []

    def accept():
        server.settimeout(0.2)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
                held.append(conn)  # hold the connection open, never reply
            except OSError:
                continue

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.getsockname()[1]}/api/2"
    stop.set()
    thread.join(timeout=2)
    for conn in held:
        conn.close()
    server.close()


def test_silent_host_times_out_with_a_message(plugin, silent_server):
    client = plugin.client.EgovClient(base_url=silent_server, timeout=0.5)
    handlers = plugin.tools.make_handlers(client)
    for name, args in [("egov_law_search", {"query": "労働基準法"}),
                       ("egov_law_article", {"law": "労基法", "article": "32"}),
                       ("egov_law_revisions", {"law": "322AC0000000049"})]:
        started = time.monotonic()
        result = json.loads(handlers[name](args))
        assert time.monotonic() - started < 5
        assert result["error_type"] == "timeout", result
        assert "did not answer within 0.5 seconds" in result["error"]
        assert "Wait a minute" in result["next_step"]


def test_refused_connection_is_a_network_error(plugin):
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()  # nothing listens on this port now
    client = plugin.client.EgovClient(base_url=f"http://127.0.0.1:{port}/api/2", timeout=2)
    result = json.loads(plugin.tools.make_handlers(client)["egov_law_search"]({"query": "民法"}))
    assert result["error_type"] == "network"
    assert "laws.e-gov.go.jp" in result["next_step"]


@pytest.mark.parametrize("location", ["https://example.invalid/api/2/laws", "http://laws.e-gov.go.jp/api/2/laws"])
def test_redirects_away_from_e_gov_are_refused(plugin, location):
    """A redirect to another host, or to plain HTTP, is refused before any connection to it."""
    import http.server

    class Redirect(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", location)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Redirect)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = plugin.client.EgovClient(base_url=f"http://127.0.0.1:{server.server_port}/api/2", timeout=3)
        result = json.loads(plugin.tools.make_handlers(client)["egov_law_search"]({"query": "民法"}))
    finally:
        server.shutdown()
        server.server_close()
    assert result["error_type"] == "network"
    assert "refused a redirect" in result["error"] and "https://laws.e-gov.go.jp" in result["error"]


def test_handler_never_raises_on_bad_arguments(replay):
    assert call(replay, "egov_law_article", law="", article="32")["error_type"] == "bad_argument"
    assert call(replay, "egov_law_article", law="労基法", article="")["error_type"] == "bad_argument"
    assert call(replay, "egov_law_article", law="労基法", article="three")["error_type"] == "bad_argument"
    assert call(replay, "egov_law_article", law="労基法", article="32", as_of="2000-01-01")["error_type"] == "bad_argument"
    assert call(replay, "egov_law_article", law="労基法", article="32", as_of="yesterday")["error_type"] == "bad_argument"
    assert call(replay, "egov_law_search", query="")["error_type"] == "bad_argument"
    assert call(replay, "egov_law_search", query="民法", mode="fulltext")["error_type"] == "bad_argument"
    assert replay["egov_law_search"](None)  # None args still produce a JSON string
    assert replay["_transport"].urls == []  # none of these reached the network


def test_ambiguous_name_lists_candidates(plugin):
    laws = [
        {"law_info": {"law_id": f"3{i:02d}AC0000000001", "law_num": f"n{i}", "law_type": "Act"},
         "revision_info": {"law_title": title, "abbrev": None}}
        for i, title in enumerate(["労働基準法", "労働組合法", "労働契約法"])
    ]

    def transport(url, timeout):
        return 200, json.dumps({"total_count": 3, "count": 3, "laws": laws}).encode()

    handlers = plugin.tools.make_handlers(plugin.client.EgovClient(transport=transport))
    result = json.loads(handlers["egov_law_article"]({"law": "労働", "article": "1"}))
    assert result["error_type"] == "ambiguous_law"
    assert "労働基準法 [300AC0000000001]" in result["next_step"]


def test_upstream_500_and_non_json_are_errors(plugin):
    def broken(url, timeout):
        return 500, b'{"code":"500001","message":"internal"}'

    def html(url, timeout):
        return 200, b"<html>maintenance</html>"

    for transport, kind in [(broken, "upstream"), (html, "bad_response")]:
        handlers = plugin.tools.make_handlers(plugin.client.EgovClient(transport=transport))
        result = json.loads(handlers["egov_law_revisions"]({"law": "322AC0000000049"}))
        assert result["error_type"] == kind


# --- Number parsing ----------------------------------------------------------

@pytest.mark.parametrize("text,numbers,paragraph", [
    ("第32条", [32], None), ("32条", [32], None), ("32", [32], None), ("三十二条", [32], None),
    ("第三十二条", [32], None), ("第三十二条の二", [32, 2], None), ("32の2", [32, 2], None),
    ("32-2", [32, 2], None), ("第32条第2項", [32], 2), ("32条2項", [32], 2), ("第３２条", [32], None),
    ("第三十二条の二第一項", [32, 2], 1),
    ("Article 32", [32], None), ("第四百十五条", [415], None), ("第百条", [100], None),
    ("第三百九十八条の二十二", [398, 22], None), ("第九九九九条", [9999], None), (32, [32], None),
])
def test_parse_article(plugin, text, numbers, paragraph):
    ref = plugin.numbers_ja.parse_article(text)
    assert ref.numbers == numbers and ref.paragraph == paragraph


@pytest.mark.parametrize("bad", ["", "abc", "第条", "0", "第32項"])
def test_parse_article_rejects(plugin, bad):
    with pytest.raises(ValueError):
        plugin.numbers_ja.parse_article(bad)


def test_law_number_normalization(plugin):
    as_law_num = plugin.numbers_ja.as_law_num
    assert as_law_num("昭和22年法律第49号") == "昭和二十二年法律第四十九号"
    assert as_law_num("平成十五年法律第五十七号") == "平成十五年法律第五十七号"
    assert as_law_num("令和1年法律第1号") == "令和元年法律第一号"
    assert as_law_num("労働基準法") is None


def test_labels_round_trip(plugin):
    assert plugin.numbers_ja.parse_article("32の2第1項").label == "第三十二条の二第一項"
    assert plugin.numbers_ja.int_to_kanji(110) == "百十"


# --- Rendering law XML trees -------------------------------------------------

def node(tag, *children, **attr):
    return {"tag": tag, "attr": attr, "children": list(children)}


def test_render_items_ruby_columns_and_tables(plugin):
    article = node(
        "Article",
        node("ArticleCaption", "（定義）"),
        node("ArticleTitle", "第二条"),
        node("Paragraph",
             node("ParagraphNum"),
             node("ParagraphSentence", node("Sentence", "次の", node("Ruby", "各", node("Rt", "かく")), "号に定める。")),
             node("Item",
                  node("ItemTitle", "一"),
                  node("ItemSentence", node("Column", node("Sentence", "事業者")),
                       node("Column", node("Sentence", "事業を行う者"))),
                  node("Subitem1", node("Subitem1Title", "イ"), node("Subitem1Sentence", node("Sentence", "法人"))))),
        node("Paragraph", node("ParagraphNum"), node("ParagraphSentence", node("Sentence", "前項の…")), Num="2"),
        node("Paragraph", node("ParagraphNum", "３"), node("ParagraphSentence", node("Sentence", "表のとおり。")),
             node("TableStruct", node("Table", node("TableRow", node("TableColumn", "区分"), node("TableColumn", "額"))))),
    )
    rendered = plugin.laws.render_article(article)
    assert rendered["paragraphs"] == 3
    assert rendered["text"].splitlines() == [
        "（定義）",
        "第二条　次の各号に定める。",
        "　一　事業者　事業を行う者",
        "　　イ　法人",
        "２　前項の…",
        "３　表のとおり。",
        "　区分｜額",
    ]


def test_long_text_is_trimmed_at_a_line(plugin):
    text, truncated = plugin.laws._trim("あ" * 200 + "\n" + "い" * 200, 300)
    assert truncated and text == "あ" * 200
    for size in (300, 301, 302):
        assert len(plugin.laws._trim("う" * 1000, size)[0]) <= size


def test_original_supplementary_provision(replay):
    result = call(replay, "egov_law_article", law="労基法", article="附則第143条")
    assert result["article"] == "附則第百四十三条"
    assert "「三年間」とする" in result["text"]
    assert result["provision"].startswith("附則")


def test_appended_tables_are_refused_with_the_page(replay):
    result = call(replay, "egov_law_article", law="労基法", article="別表第一")
    assert result["error_type"] == "not_covered"
    assert "Do not retry" in result["next_step"]
    assert "https://laws.e-gov.go.jp/law/322AC0000000049" in result["next_step"]


def test_split_supplementary_reference(plugin):
    split = plugin.laws._split_suppl
    assert split("附則第143条") == (True, "第143条")
    assert split("附則") == (True, "")
    assert split("第32条") == (False, "第32条")


def test_compare_diff_obeys_max_chars(plugin):
    def article(sentence):
        return {"law_info": {"law_id": "322AC0000000049", "law_num": "n"}, "revision_info": {"law_title": "x"},
                "law_full_text": node("Article", node("ArticleTitle", "第一条"),
                                      *[node("Paragraph", node("ParagraphNum"),
                                             node("ParagraphSentence", node("Sentence", sentence + str(i))), Num=str(i))
                                        for i in range(1, 30)])}

    def transport(url, timeout):
        return 200, json.dumps(article("新" * 50 if "asof=2027" in url else "旧" * 50), ensure_ascii=False).encode()

    handlers = plugin.tools.make_handlers(plugin.client.EgovClient(transport=transport))
    result = json.loads(handlers["egov_law_article"]({"law": "322AC0000000049", "article": "1",
                                                       "compare_with": "2027-04-01", "max_chars": 500}))
    comparison = result["comparison"]
    assert sum(len(line) for line in comparison["diff"]) <= 500
    assert len(comparison["text"]) <= 500 and comparison["truncated"] is True


# --- Revision status when e-Gov's label lags --------------------------------

def test_in_force_falls_back_to_dates_when_no_version_is_marked_current(plugin):
    revisions = [
        {"amendment_enforcement_date": "2027-01-17", "current_revision_status": "UnEnforced"},
        {"amendment_enforcement_date": "2026-10-01", "current_revision_status": "PreviousEnforced"},
        {"amendment_enforcement_date": "2026-07-17", "current_revision_status": "PreviousEnforced"},
    ]
    assert plugin.laws._pick_in_force(revisions, "2026-10-02") == 1
    revisions[2]["current_revision_status"] = "CurrentEnforced"
    assert plugin.laws._pick_in_force(revisions, "2026-10-02") == 2


def test_aliases_are_law_ids(plugin):
    for alias, law_id in plugin.laws.ALIASES.items():
        assert plugin.numbers_ja.LAW_ID_RE.match(law_id), alias


def test_compare_with_reports_a_line_diff(plugin):
    def article(sentence):
        return {"law_info": {"law_id": "322AC0000000049", "law_num": "n"},
                "revision_info": {"law_title": "労働基準法"},
                "law_full_text": node("Article", node("ArticleTitle", "第一条"),
                                      node("Paragraph", node("ParagraphNum"),
                                           node("ParagraphSentence", node("Sentence", sentence))))}

    def transport(url, timeout):
        new = "asof=2027-04-01" in url
        return 200, json.dumps(article("新しい文。" if new else "古い文。"), ensure_ascii=False).encode()

    handlers = plugin.tools.make_handlers(plugin.client.EgovClient(transport=transport))
    result = json.loads(handlers["egov_law_article"]({"law": "322AC0000000049", "article": "1",
                                                       "compare_with": "2027-04-01"}))
    comparison = result["comparison"]
    assert comparison["changed"] is True
    assert comparison["diff"] == ["-第一条　古い文。", "+第一条　新しい文。"]
    assert comparison["text"] == "第一条　新しい文。"
    bad = json.loads(handlers["egov_law_article"]({"law": "322AC0000000049", "article": "1",
                                                   "compare_with": "2010-01-01"}))
    assert bad["error_type"] == "bad_argument" and "compare_with" in bad["error"]


EXPECTED_ALIAS_TITLES = {
    "個情法": "個人情報の保護に関する法律",
    "特商法": "特定商取引に関する法律",
    "下請法": "製造委託等に係る中小受託事業者に対する代金の支払の遅延等の防止に関する法律",
    "雇保法": "雇用保険法",
    "育介法": "育児休業、介護休業等育児又は家族介護を行う労働者の福祉に関する法律",
    "育児休業法": "育児休業、介護休業等育児又は家族介護を行う労働者の福祉に関する法律",
    "パート法": "短時間労働者及び有期雇用労働者の雇用管理の改善等に関する法律",
    "パート有期法": "短時間労働者及び有期雇用労働者の雇用管理の改善等に関する法律",
    "パートタイム・有期雇用労働法": "短時間労働者及び有期雇用労働者の雇用管理の改善等に関する法律",
    "フリーランス法": "特定受託事業者に係る取引の適正化等に関する法律",
    "フリーランス新法": "特定受託事業者に係る取引の適正化等に関する法律",
    "派遣法": "労働者派遣事業の適正な運営の確保及び派遣労働者の保護等に関する法律",
    "均等法": "雇用の分野における男女の均等な機会及び待遇の確保等に関する法律",
    "憲法": "日本国憲法",
    "健保法": "健康保険法",
    "厚年法": "厚生年金保険法",
    "パワハラ防止法": "労働施策の総合的な推進並びに労働者の雇用の安定及び職業生活の充実等に関する法律",
    "高年法": "高年齢者等の雇用の安定等に関する法律",
    "労基則": "労働基準法施行規則",
    "労規則": "労働基準法施行規則",
    "雇保則": "雇用保険法施行規則",
    "電帳法": "電子計算機を使用して作成する国税関係帳簿書類の保存方法等の特例に関する法律",
}


def test_every_alias_points_at_the_intended_law(plugin):
    recorded = json.loads((Path(__file__).parent / "fixtures" / "alias_titles.json").read_text(encoding="utf-8"))
    assert set(plugin.laws.ALIASES) == set(EXPECTED_ALIAS_TITLES)
    for alias, title in EXPECTED_ALIAS_TITLES.items():
        assert recorded[alias] == title, alias


def test_sub_paragraph_suffixes_are_dropped(plugin):
    drop = plugin.laws._drop_sub_paragraph
    assert drop("第32条第1項第2号") == ("第32条第1項", "第2号")
    assert drop("32条ただし書") == ("32条", "ただし書")
    assert drop("32条1項本文") == ("32条1項", "本文")
    assert drop("第32条") == ("第32条", None)


def test_check_dates(plugin):
    assert plugin.laws._check_dates("2027-04-01") == {"as_of": "2027-03-31", "compare_with": "2027-04-01"}
    assert plugin.laws._check_dates("2017-04-01") is None


def test_change_types(plugin):
    change = plugin.laws._change_type
    assert change({"repeal_status": "Repeal", "amendment_type": "8"}) == plugin.laws.CHANGE_REPEAL
    assert change({"amendment_type": "1"}) == plugin.laws.CHANGE_OWN
    assert change({"amendment_type": "3", "amendment_law_id": "000000000000000"}) == plugin.laws.CHANGE_OWN
    assert change({"amendment_type": "3", "amendment_law_id": "508AC0000000060",
                   "amendment_law_title": "労働者災害補償保険法等の一部を改正する法律"}) == "amendment"


def test_transitional_supplementary_reading_is_noted(plugin, replay):
    client = plugin.client.EgovClient(transport=replay["_transport"])
    assert plugin.laws._suppl_readings(client, "322AC0000000049", None, "第百十五条") == ["附則第百四十三条"]
    assert plugin.laws._suppl_readings(client, "322AC0000000049", None, "第三十二条") == []


def test_repealed_law_is_not_in_force(plugin, replay):
    """行政機関個人情報保護法 (415AC0000000058) was repealed on 2022-04-01 (recorded 2026-10-02)."""
    result = call(replay, "egov_law_revisions", law="415AC0000000058")
    assert result["in_force_now"] is None
    assert result["repealed_on"] == "2022-04-01"
    assert result["message"] == ("This law was repealed on 2022-04-01 by デジタル社会の形成を図るための関係法律の整備に"
                                 "関する法律（令和三年法律第三十七号）; it is not in force.")
    assert "as_of='2022-03-31'" in result["next_step"]
    rows = result["earlier_versions"]
    assert rows[0]["change"] == plugin.laws.CHANGE_REPEAL and rows[0]["status"] == "repealed"
    assert rows[0]["check"] == {"as_of": "2022-03-31"}
    assert not any(row.get("status") == "in force now" for row in rows)

    article = call(replay, "egov_law_article", law="415AC0000000058", article="1")
    assert article["law_version"]["status"] == "repealed"
    assert "This law was repealed on 2022-04-01" in article["text_notes"]


def test_scheduled_repeal_as_next_change(plugin):
    def transport(url, timeout):
        return 200, json.dumps({"law_info": {"law_id": "341AC0000000132"}, "revisions": [
            {"amendment_enforcement_date": "2099-04-01", "current_revision_status": "UnEnforced",
             "repeal_status": "Repeal", "amendment_type": "8", "amendment_law_title": "廃止法",
             "amendment_law_num": "令和九十九年法律第一号"},
            {"amendment_enforcement_date": "2026-04-01", "current_revision_status": "CurrentEnforced"},
        ]}, ensure_ascii=False).encode()

    handlers = plugin.tools.make_handlers(plugin.client.EgovClient(transport=transport))
    result = json.loads(handlers["egov_law_revisions"]({"law": "341AC0000000132"}))
    assert result["scheduled_repeal"]["in_force_since"] == "2099-04-01"
    assert result["scheduled_repeal"]["check"] == {"as_of": "2099-03-31"}
    assert result["in_force_now"]["in_force_since"] == "2026-04-01" and "repealed_on" not in result
    assert "compare_with=<its in_force_since>" in result["next_step"]


def test_repeal_rows_are_never_the_version_in_force(plugin):
    pick = plugin.laws._pick_in_force
    repeal = {"amendment_enforcement_date": "2022-04-01", "current_revision_status": "Repeal",
              "repeal_status": "Repeal", "amendment_type": "8"}
    older = {"amendment_enforcement_date": "2021-05-19", "current_revision_status": "PreviousEnforced"}
    assert pick([repeal, older], "2026-10-02") is None
    assert pick([dict(repeal, amendment_enforcement_date="2027-04-01", current_revision_status="UnEnforced"),
                 older], "2026-10-02") == 1  # a repeal still to come leaves the current version in force
    not_yet = [{"amendment_enforcement_date": "2027-04-01", "current_revision_status": "UnEnforced",
                "amendment_type": "1"}]
    assert pick(not_yet, "2026-10-02") is None


def test_version_status_uses_the_versions_own_date(plugin):
    status = plugin.laws._version_status
    assert status({"amendment_enforcement_date": "2026-07-17"}, "2099-01-01").startswith("in force now")
    assert status({"amendment_enforcement_date": "2099-01-01"}, "2099-06-01").startswith("not yet in force")
    assert status({"amendment_enforcement_date": "2018-01-01"}, "2018-06-01") == "version in force on 2018-06-01"
