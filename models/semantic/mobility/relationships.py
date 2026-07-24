import marivo.semantic as ms

ms.relationship(
    name="trips_to_pickup_zones",
    from_entity=ms.ref.entity("mobility.yellow_trips"),
    to_entity=ms.ref.entity("mobility.pickup_zones"),
    keys=[
        ms.join_on(
            ms.ref.dimension("mobility.yellow_trips.pickup_location_id"),
            ms.ref.dimension("mobility.pickup_zones.location_id"),
        )
    ],
    ai_context=ms.ai_context(
        business_definition="Many published trips map to one official pickup Taxi Zone.",
        guardrails=[
            "Use trip-owned pickup and drop-off role dimensions for combined OD analysis."
        ],
    ),
)

ms.relationship(
    name="trips_to_dropoff_zones",
    from_entity=ms.ref.entity("mobility.yellow_trips"),
    to_entity=ms.ref.entity("mobility.dropoff_zones"),
    keys=[
        ms.join_on(
            ms.ref.dimension("mobility.yellow_trips.dropoff_location_id"),
            ms.ref.dimension("mobility.dropoff_zones.location_id"),
        )
    ],
    ai_context=ms.ai_context(
        business_definition="Many published trips map to one official drop-off Taxi Zone.",
        guardrails=[
            "Use trip-owned pickup and drop-off role dimensions for combined OD analysis."
        ],
    ),
)
