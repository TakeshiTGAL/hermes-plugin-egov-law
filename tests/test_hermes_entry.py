"""Refusals and source fields through Hermes's own tool entry.

``model_tools.handle_function_call`` is what a session actually runs. The
plugin root is named ``tools.py``, so it is taken off ``sys.path`` before
Hermes's ``tools`` package is imported.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _hermes():
    root = str(ROOT.resolve())
    sys.path[:] = [p for p in sys.path if p not in ("", root) and _resolved(p) != root]
    shadowed = sys.modules.get("tools")
    if shadowed is not None and str(getattr(shadowed, "__file__", "")).endswith("/tools.py"):
        del sys.modules["tools"]
    model_tools = pytest.importorskip("model_tools")
    registry_mod = pytest.importorskip("tools.registry")
    return model_tools, registry_mod


def _resolved(path: str) -> str:
    try:
        return str(Path(path).resolve())
    except OSError:
        return path


def _install(registry_mod, plugin, handlers):
    for schema in plugin.schemas.ALL_SCHEMAS:
        registry_mod.registry.register(
            name=schema["name"],
            toolset="egov_law",
            schema=schema,
            handler=handlers[schema["name"]],
            override=True,
        )


def _call(model_tools, name, args):
    raw = model_tools.handle_function_call(name, args)
    assert isinstance(raw, str)
    payload = json.loads(raw)
    assert payload.get("error_type") != "tool_result_contract"
    return raw, payload


def _props(plugin, tool):
    return list(plugin.schemas.BY_NAME[tool]["parameters"]["properties"])


def test_entry_refuses_a_bad_paragraph_as_paragraph(replay, plugin):
    model_tools, registry_mod = _hermes()
    _install(registry_mod, plugin, replay)
    raw, bad = _call(model_tools, "egov_law_article", {"law": "労基法", "article": "32", "paragraph": "abc"})
    assert bad["error_type"] == "bad_argument"
    assert bad["field"] == "paragraph"
    assert bad["problem"] == "unparsed"
    assert bad["expected"] == "a paragraph number such as 2 or 第2項"
    assert bad["allowed_fields"] == _props(plugin, "egov_law_article")
    assert "abc" not in raw


def test_entry_refuses_other_bad_arguments_with_the_tool_fields(replay, plugin):
    model_tools, registry_mod = _hermes()
    _install(registry_mod, plugin, replay)
    _, article = _call(model_tools, "egov_law_article", {"law": "労基法", "article": "three"})
    assert article["field"] == "article"
    assert article["allowed_fields"] == _props(plugin, "egov_law_article")
    _, search = _call(model_tools, "egov_law_search", {"query": ""})
    assert search["field"] == "query"
    assert search["allowed_fields"] == _props(plugin, "egov_law_search")
    _, revisions = _call(model_tools, "egov_law_revisions", {"law": ""})
    assert revisions["field"] == "law"
    assert revisions["allowed_fields"] == _props(plugin, "egov_law_revisions")


def test_entry_article_returns_wording_date_and_history_does_not(replay, plugin):
    model_tools, registry_mod = _hermes()
    _install(registry_mod, plugin, replay)
    _, article = _call(model_tools, "egov_law_article", {"law": "労基法", "article": "32"})
    assert article["source"]["as_of"] == article["as_of"]
    assert article["source"]["url"] == article["url"]
    assert article["source"]["retrieved_at"].endswith("Z")
    _, history = _call(model_tools, "egov_law_revisions", {"law": "個情法", "limit": 3})
    assert "as_of" not in history["source"]
    assert "PDL1.0" in article["source"]["note"]
    assert history["source"]["url"] == history["url"]
    assert history["source"]["retrieved_at"].endswith("Z")
    assert history["in_force_now"]["in_force_since"]
    _, found = _call(model_tools, "egov_law_search", {"query": "労働基準法"})
    assert "as_of" not in found["source"]
    assert found["source"]["url"] == "https://laws.e-gov.go.jp/"
    assert found["results"][0]["url"] == "https://laws.e-gov.go.jp/law/322AC0000000049"


def test_skill_stays_hidden_when_the_toolset_is_off(plugin):
    _hermes()
    from agent.prompt_builder import _skill_should_show
    from agent.skill_utils import extract_skill_conditions

    seen = {}

    class Ctx:
        def register_tool(self, name, toolset, schema, handler, **kwargs):
            return None

        def register_skill(self, name, path, description="", frontmatter=None):
            seen["frontmatter"] = frontmatter

    _hermes()
    plugin.register(Ctx())
    conditions = extract_skill_conditions(seen["frontmatter"])
    assert _skill_should_show(conditions, set(), set()) is False
    assert _skill_should_show(conditions, set(), {"egov_law"}) is True
    assert _skill_should_show(conditions, None, None) is True
