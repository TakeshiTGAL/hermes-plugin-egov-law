"""e-Gov Law plugin for Hermes Agent.

Look up Japanese laws in e-Gov (the Digital Agency of Japan's official law
database): search by name or text, read one article, and check amendment
history and enforcement dates. Read-only, no credentials, network calls go to
laws.e-gov.go.jp only.
"""

from pathlib import Path

from . import blueprint, schemas, tools

_SKILL = Path(__file__).resolve().parent / "skills" / "read-law" / "SKILL.md"


def register(ctx):
    """Register the three read-only tools, the quoting skill, then the blueprint."""
    ctx.register_skill(
        "read-law",
        _SKILL,
        description=(
            "Quote Japanese law only from egov_law_article, egov_law_search, or egov_law_revisions, "
            "and pass source.retrieved_at, source.url, and source.as_of with the text."
        ),
    )
    for schema in schemas.ALL_SCHEMAS:
        ctx.register_tool(
            name=schema["name"],
            toolset="egov_law",
            schema=schema,
            handler=tools.HANDLERS[schema["name"]],
            emoji="⚖️",
        )
    blueprint.register_blueprint(ctx)
