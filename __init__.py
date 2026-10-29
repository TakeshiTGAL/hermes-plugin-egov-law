"""e-Gov Law plugin for Hermes Agent.

Look up Japanese laws in e-Gov (the Digital Agency of Japan's official law
database): search by name or text, read one article, and check amendment
history and enforcement dates. Read-only, no credentials, network calls go to
laws.e-gov.go.jp only.
"""

import logging
from pathlib import Path

from . import blueprint, schemas, tools, turn_scope

logger = logging.getLogger(__name__)

_SKILL = Path(__file__).resolve().parent / "skills" / "read-law" / "SKILL.md"
_SKILL_DESCRIPTION = (
    "Before web_search, use tool_search to find the e-Gov law tools and tool_call to read an official Japanese statute. "
    "pre_tool_call blocks egov_law_search when the query is empty or, in title mode, does not name a statute. "
    "The block says no article URL was written and a URL was not guessed. "
    "Copy source.retrieved_at, source.url, and source.as_of when egov_law_article returned it."
)


def _law_turn(user_message, conversation_history=None) -> bool:
    """A statute question, or an e-Gov tool called in the previous turn. 条件 does not match."""
    return turn_scope.owns(user_message, conversation_history, "statute")


def _nudge_law(user_message="", conversation_history=None, **_kwargs):
    if not _law_turn(user_message, conversation_history):
        return None
    return {"context": (
        "Do not call egov_law_search with an empty query or with a company name. "
        "pre_tool_call blocks that search before HTTP. No article URL is written and a URL is not guessed. "
        "Call egov_law_article when the user named a law and an article, or when a tool result already names "
        "law_title and article, and copy source.url. If article is null, do not guess. "
        "Do not call tool_describe. Do not write 取得しました or 確認できます."
    )}


def _block_unnamed_search(tool_name="", args=None, **_kwargs):
    from . import search_gate
    return search_gate.block(tool_name or "", args if isinstance(args, dict) else {})


def register(ctx):
    """Register the three read-only tools, then the quoting skill, then the blueprint."""
    for schema in schemas.ALL_SCHEMAS:
        ctx.register_tool(
            name=schema["name"],
            toolset="egov_law",
            schema=schema,
            handler=tools.HANDLERS[schema["name"]],
            emoji="⚖️",
        )
    for hook_name, callback in (
        ("pre_llm_call", _nudge_law),
        ("pre_tool_call", _block_unnamed_search),
    ):
        try:
            ctx.register_hook(hook_name, callback)
        except Exception:
            logger.warning("jp-egov-law %s hook unavailable", hook_name, exc_info=True)
    try:
        ctx.register_skill(
            "read-law",
            _SKILL,
            description=_SKILL_DESCRIPTION,
        )
    except Exception:
        logger.warning("jp-egov-law skill was not registered", exc_info=True)
    blueprint.register_blueprint(ctx)
