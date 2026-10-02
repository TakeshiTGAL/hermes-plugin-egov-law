"""e-Gov Law plugin for Hermes Agent.

Look up Japanese laws in e-Gov (the Digital Agency of Japan's official law
database): search by name or text, read one article, and check amendment
history and enforcement dates. Read-only, no credentials, network calls go to
laws.e-gov.go.jp only.
"""

from . import schemas, tools


def register(ctx):
    """Register the three read-only tools under the `egov_law` toolset."""
    for schema in schemas.ALL_SCHEMAS:
        ctx.register_tool(
            name=schema["name"],
            toolset="egov_law",
            schema=schema,
            handler=tools.HANDLERS[schema["name"]],
            emoji="⚖️",
        )
