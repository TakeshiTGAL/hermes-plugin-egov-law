"""A title search that does not name a statute is blocked before HTTP."""


def _gate(plugin):
    return __import__(plugin.__name__ + ".search_gate", fromlist=["block"])


def test_empty_query_is_blocked(plugin):
    blocked = _gate(plugin).block("egov_law_search", {"query": ""})
    assert blocked["action"] == "block"
    assert "No article URL" in blocked["message"]
    assert "not guessed" in blocked["message"]
    assert "egov_law_article" in blocked["message"]


def test_company_name_is_blocked(plugin):
    blocked = _gate(plugin).block(
        "egov_law_search", {"query": "トヨタ自動車", "company_name": "トヨタ自動車"},
    )
    assert blocked["action"] == "block"


def test_jouken_is_blocked(plugin):
    gate = _gate(plugin)
    for query in ("条件", "必要条件"):
        blocked = gate.block("egov_law_search", {"query": query})
        assert blocked["action"] == "block"
        assert "did not name a statute" in blocked["message"]
    assert gate.block("egov_law_search", {"query": "第32条"}) is None
    assert gate.block("egov_law_search", {"query": "条約"}) is None
    assert gate.block("egov_law_search", {"query": "労働基準法施行令"}) is None
    assert gate.block("egov_law_search", {"query": "条例"}) is None
    blocked = gate.block("egov_law_search", {"query": "辞令"})
    assert blocked["action"] == "block"
    blocked = gate.block("egov_law_search", {"query": "指令"})
    assert blocked["action"] == "block"
    assert "did not name a statute" in blocked["message"]
    assert gate.block("egov_law_search", {"query": "施行令"}) is None
    assert gate.block("egov_law_search", {"query": "政令"}) is None
    assert gate.block("egov_law_search", {"query": "命令"}) is None


def test_statute_title_and_text_mode_and_article_are_not_blocked(plugin):
    gate = _gate(plugin)
    assert gate.block("egov_law_search", {"query": "労働基準法"}) is None
    assert gate.block(
        "egov_law_search", {"query": "時間外労働", "mode": "text"},
    ) is None
    assert gate.block(
        "egov_law_article", {"law": "労働基準法", "article": "32"},
    ) is None
