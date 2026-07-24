import marivo.semantic as ms

ms.domain(
    name="mobility",
    owner="Marivo Yellow Taxi Demo",
    default=True,
    ai_context=ms.ai_context(
        business_definition=(
            "NYC Yellow Taxi trip demand, passenger fares, route geography, and "
            "published record quality for calendar year 2025."
        ),
        guardrails=[
            "Treat all timestamps as America/New_York local time.",
            "Do not infer unique passengers or drivers; the public data has no stable identities.",
            "Do not describe before/after differences or correlations as causal effects.",
            "Credit-card tips are recorded automatically; cash tips are generally not recorded.",
        ],
    ),
)
