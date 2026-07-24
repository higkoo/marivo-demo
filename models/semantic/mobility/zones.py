import marivo.datasource as md
import marivo.semantic as ms

ZONE_GUARDRAILS = [
    "Treat Unknown and N/A as published lookup categories, not inferred geography.",
]

pickup_zones = ms.entity(
    name="pickup_zones",
    datasource=ms.ref.datasource("warehouse"),
    source=md.table("pickup_zones"),
    primary_key=["location_id"],
    ai_context=ms.ai_context(
        business_definition="One row per official TLC Taxi Zone in its pickup role.",
        guardrails=ZONE_GUARDRAILS,
    ),
)
pickup_location_id = ms.dimension_column(
    name="location_id",
    entity=pickup_zones,
    column="location_id",
    ai_context=ms.ai_context(
        business_definition="Official TLC Taxi Zone identifier.",
        guardrails=["Use the named borough or zone dimension for presentation."],
    ),
)
pickup_borough = ms.dimension_column(
    name="borough",
    entity=pickup_zones,
    column="borough",
    ai_context=ms.ai_context(
        business_definition="Borough containing the pickup zone.",
        guardrails=ZONE_GUARDRAILS,
    ),
)
pickup_zone = ms.dimension_column(
    name="zone",
    entity=pickup_zones,
    column="zone",
    ai_context=ms.ai_context(
        business_definition="Official pickup Taxi Zone name.",
        guardrails=ZONE_GUARDRAILS,
    ),
)
pickup_service_zone = ms.dimension_column(
    name="service_zone",
    entity=pickup_zones,
    column="service_zone",
    ai_context=ms.ai_context(
        business_definition="TLC service-zone classification for pickup.",
        guardrails=ZONE_GUARDRAILS,
    ),
)

dropoff_zones = ms.entity(
    name="dropoff_zones",
    datasource=ms.ref.datasource("warehouse"),
    source=md.table("dropoff_zones"),
    primary_key=["location_id"],
    ai_context=ms.ai_context(
        business_definition="One row per official TLC Taxi Zone in its drop-off role.",
        guardrails=ZONE_GUARDRAILS,
    ),
)
dropoff_location_id = ms.dimension_column(
    name="location_id",
    entity=dropoff_zones,
    column="location_id",
    ai_context=ms.ai_context(
        business_definition="Official TLC Taxi Zone identifier.",
        guardrails=["Use the named borough or zone dimension for presentation."],
    ),
)
dropoff_borough = ms.dimension_column(
    name="borough",
    entity=dropoff_zones,
    column="borough",
    ai_context=ms.ai_context(
        business_definition="Borough containing the drop-off zone.",
        guardrails=ZONE_GUARDRAILS,
    ),
)
dropoff_zone = ms.dimension_column(
    name="zone",
    entity=dropoff_zones,
    column="zone",
    ai_context=ms.ai_context(
        business_definition="Official drop-off Taxi Zone name.",
        guardrails=ZONE_GUARDRAILS,
    ),
)
dropoff_service_zone = ms.dimension_column(
    name="service_zone",
    entity=dropoff_zones,
    column="service_zone",
    ai_context=ms.ai_context(
        business_definition="TLC service-zone classification for drop-off.",
        guardrails=ZONE_GUARDRAILS,
    ),
)
