"""e-Gov Law plugin for Hermes Agent.

Look up Japanese laws in e-Gov (the Digital Agency of Japan's official law
database): search by name or text, read one article, and check amendment
history and enforcement dates. Read-only, no credentials, network calls go to
laws.e-gov.go.jp only.
"""

import logging
from pathlib import Path

from . import blueprint, schemas, tools

logger = logging.getLogger(__name__)

_SKILL = Path(__file__).resolve().parent / "skills" / "read-law" / "SKILL.md"
_SKILL_DESCRIPTION = (
    "Source fields for a Japanese statute fetched from e-Gov: "
    "source.retrieved_at, source.url, and source.as_of when egov_law_article returned it."
)
# Passed to register_skill. Hermes filters <available_skills> from this argument,
# not from the SKILL.md file. A host that does not pass toolset info still lists it.
_SKILL_FRONTMATTER = {"metadata": {"hermes": {"requires_toolsets": ["egov_law"]}}}


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
    try:
        ctx.register_skill(
            "read-law",
            _SKILL,
            description=_SKILL_DESCRIPTION,
            frontmatter=_SKILL_FRONTMATTER,
        )
    except Exception:
        logger.warning("jp-egov-law skill was not registered", exc_info=True)
    blueprint.register_blueprint(ctx)
