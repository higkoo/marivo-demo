import marivo.datasource as md
import marivo.semantic as ms

PUBLISHED_RECORD_GUARDRAILS = [
    "Published records include corrections and incomplete values; pair conclusions with quality and coverage metrics.",
]
MONEY_GUARDRAILS = [
    "Negative correction-like amounts are retained; assess record quality before interpreting totals.",
]
LOCAL_TIME_GUARDRAILS = [
    "Interpret values in America/New_York and distinguish pickup time from source-file month.",
]
QUALITY_GUARDRAILS = [
    "These are transparent demo checks, not TLC validity determinations.",
]

yellow_trips = ms.entity(
    name="yellow_trips",
    datasource=ms.ref.datasource("warehouse"),
    source=md.table("yellow_trips"),
    ai_context=ms.ai_context(
        business_definition=(
            "One row per record in the official monthly NYC TLC Yellow Taxi Parquet files."
        ),
        guardrails=[
            "A row is a published trip record, not a stable passenger or driver.",
            *PUBLISHED_RECORD_GUARDRAILS,
        ],
    ),
)

source_month = ms.dimension_column(
    name="source_month",
    entity=yellow_trips,
    column="source_month",
    ai_context=ms.ai_context(
        business_definition="Month encoded in the official source Parquet filename.",
        guardrails=[
            "This is a file-partition label; use picked_up_at for actual trip calendar analysis."
        ],
    ),
)
vendor_id = ms.dimension_column(
    name="vendor_id",
    entity=yellow_trips,
    column="vendor_id",
    ai_context=ms.ai_context(
        business_definition="Raw TLC code for the TPEP provider.",
        guardrails=["Use vendor for presentation and vendor_id for source-code auditing."],
    ),
)
vendor = ms.dimension_column(
    name="vendor",
    entity=yellow_trips,
    column="vendor",
    ai_context=ms.ai_context(
        business_definition="TPEP provider that supplied the trip record.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
payment_type_id = ms.dimension_column(
    name="payment_type_id",
    entity=yellow_trips,
    column="payment_type_id",
    ai_context=ms.ai_context(
        business_definition="Raw TLC payment-type code.",
        guardrails=["Use payment_type for presentation and payment_type_id for source-code auditing."],
    ),
)
payment_type = ms.dimension_column(
    name="payment_type",
    entity=yellow_trips,
    column="payment_type",
    ai_context=ms.ai_context(
        business_definition="TLC payment category for the trip.",
        guardrails=[
            "Cash tips are generally not recorded; isolate credit-card trips for rider tip analysis."
        ],
    ),
)
rate_code_id = ms.dimension_column(
    name="rate_code_id",
    entity=yellow_trips,
    column="rate_code_id",
    ai_context=ms.ai_context(
        business_definition="Raw final TLC rate code.",
        guardrails=["Use rate_code for presentation and rate_code_id for source-code auditing."],
    ),
)
rate_code = ms.dimension_column(
    name="rate_code",
    entity=yellow_trips,
    column="rate_code",
    ai_context=ms.ai_context(
        business_definition="Final TLC rate code in effect for the trip.",
        guardrails=["Not reported is distinct from TLC code 99 and unmapped codes."],
    ),
)
store_and_forward = ms.dimension_column(
    name="store_and_forward",
    entity=yellow_trips,
    column="store_and_forward",
    ai_context=ms.ai_context(
        business_definition="Whether the vehicle held the record before sending it.",
        guardrails=["Not reported is retained as a separate category."],
    ),
)

pickup_location_id = ms.dimension_column(
    name="pickup_location_id",
    entity=yellow_trips,
    column="pickup_location_id",
    ai_context=ms.ai_context(
        business_definition="Official TLC pickup Taxi Zone key.",
        guardrails=["Use pickup_zone or pickup_borough for presentation."],
    ),
)
dropoff_location_id = ms.dimension_column(
    name="dropoff_location_id",
    entity=yellow_trips,
    column="dropoff_location_id",
    ai_context=ms.ai_context(
        business_definition="Official TLC drop-off Taxi Zone key.",
        guardrails=["Use dropoff_zone or dropoff_borough for presentation."],
    ),
)
pickup_borough = ms.dimension_column(
    name="pickup_borough",
    entity=yellow_trips,
    column="pickup_borough",
    ai_context=ms.ai_context(
        business_definition="Borough of the official pickup Taxi Zone at trip grain.",
        guardrails=["Use this trip-owned role dimension for combined pickup/drop-off analysis."],
    ),
)
pickup_zone = ms.dimension_column(
    name="pickup_zone",
    entity=yellow_trips,
    column="pickup_zone",
    ai_context=ms.ai_context(
        business_definition="Official pickup Taxi Zone name at trip grain.",
        guardrails=["Use this trip-owned role dimension for combined pickup/drop-off analysis."],
    ),
)
pickup_service_zone = ms.dimension_column(
    name="pickup_service_zone",
    entity=yellow_trips,
    column="pickup_service_zone",
    ai_context=ms.ai_context(
        business_definition="TLC service-zone classification for pickup at trip grain.",
        guardrails=["Unknown or missing zones remain visible for quality assessment."],
    ),
)
dropoff_borough = ms.dimension_column(
    name="dropoff_borough",
    entity=yellow_trips,
    column="dropoff_borough",
    ai_context=ms.ai_context(
        business_definition="Borough of the official drop-off Taxi Zone at trip grain.",
        guardrails=["Use this trip-owned role dimension for combined pickup/drop-off analysis."],
    ),
)
dropoff_zone = ms.dimension_column(
    name="dropoff_zone",
    entity=yellow_trips,
    column="dropoff_zone",
    ai_context=ms.ai_context(
        business_definition="Official drop-off Taxi Zone name at trip grain.",
        guardrails=["Use this trip-owned role dimension for combined pickup/drop-off analysis."],
    ),
)
dropoff_service_zone = ms.dimension_column(
    name="dropoff_service_zone",
    entity=yellow_trips,
    column="dropoff_service_zone",
    ai_context=ms.ai_context(
        business_definition="TLC service-zone classification for drop-off at trip grain.",
        guardrails=["Unknown or missing zones remain visible for quality assessment."],
    ),
)

pickup_hour = ms.dimension_column(
    name="pickup_hour",
    entity=yellow_trips,
    column="pickup_hour",
    ai_context=ms.ai_context(
        business_definition="Pickup hour of day from 0 through 23 in America/New_York.",
        guardrails=LOCAL_TIME_GUARDRAILS,
    ),
)
pickup_weekday_number = ms.dimension_column(
    name="pickup_weekday_number",
    entity=yellow_trips,
    column="pickup_weekday_number",
    ai_context=ms.ai_context(
        business_definition="ISO pickup weekday number, Monday 1 through Sunday 7.",
        guardrails=LOCAL_TIME_GUARDRAILS,
    ),
)
pickup_weekday = ms.dimension_column(
    name="pickup_weekday",
    entity=yellow_trips,
    column="pickup_weekday",
    ai_context=ms.ai_context(
        business_definition="English pickup weekday name in America/New_York.",
        guardrails=["Use pickup_weekday_number when deterministic calendar ordering matters."],
    ),
)
pickup_is_weekend = ms.dimension_column(
    name="pickup_is_weekend",
    entity=yellow_trips,
    column="pickup_is_weekend",
    ai_context=ms.ai_context(
        business_definition="Whether pickup occurred on Saturday or Sunday local time.",
        guardrails=LOCAL_TIME_GUARDRAILS,
    ),
)

pickup_time_matches_source_month = ms.dimension_column(
    name="pickup_time_matches_source_month",
    entity=yellow_trips,
    column="pickup_time_matches_source_month",
    ai_context=ms.ai_context(
        business_definition="Whether pickup calendar month matches the source-file month.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
has_positive_duration = ms.dimension_column(
    name="has_positive_duration",
    entity=yellow_trips,
    column="has_positive_duration",
    ai_context=ms.ai_context(
        business_definition="Whether drop-off occurs strictly after pickup.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
has_nonnegative_distance = ms.dimension_column(
    name="has_nonnegative_distance",
    entity=yellow_trips,
    column="has_nonnegative_distance",
    ai_context=ms.ai_context(
        business_definition="Whether taximeter-reported distance is nonnegative.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
has_positive_distance = ms.dimension_column(
    name="has_positive_distance",
    entity=yellow_trips,
    column="has_positive_distance",
    ai_context=ms.ai_context(
        business_definition="Whether taximeter-reported distance is strictly positive.",
        guardrails=["A zero-distance record is a review flag, not automatic proof of invalidity."],
    ),
)
has_reasonable_distance = ms.dimension_column(
    name="has_reasonable_distance",
    entity=yellow_trips,
    column="has_reasonable_distance",
    ai_context=ms.ai_context(
        business_definition="Whether reported distance is between 0 and 200 miles inclusive.",
        guardrails=["The 200-mile ceiling is a transparent demo plausibility threshold."],
    ),
)
has_reasonable_duration = ms.dimension_column(
    name="has_reasonable_duration",
    entity=yellow_trips,
    column="has_reasonable_duration",
    ai_context=ms.ai_context(
        business_definition="Whether elapsed duration is greater than 0 and no more than 24 hours.",
        guardrails=["The 24-hour ceiling is a transparent demo plausibility threshold."],
    ),
)
has_reasonable_speed = ms.dimension_column(
    name="has_reasonable_speed",
    entity=yellow_trips,
    column="has_reasonable_speed",
    ai_context=ms.ai_context(
        business_definition="Whether implied speed is no more than 100 mph, allowing zero distance.",
        guardrails=["The 100-mph ceiling is a transparent demo plausibility threshold."],
    ),
)
has_nonnegative_fare = ms.dimension_column(
    name="has_nonnegative_fare",
    entity=yellow_trips,
    column="has_nonnegative_fare",
    ai_context=ms.ai_context(
        business_definition="Whether metered fare amount is nonnegative.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
has_nonnegative_total = ms.dimension_column(
    name="has_nonnegative_total",
    entity=yellow_trips,
    column="has_nonnegative_total",
    ai_context=ms.ai_context(
        business_definition="Whether total passenger charge is nonnegative.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
has_known_passenger_count = ms.dimension_column(
    name="has_known_passenger_count",
    entity=yellow_trips,
    column="has_known_passenger_count",
    ai_context=ms.ai_context(
        business_definition="Whether driver-entered passenger count is present.",
        guardrails=["Missing values are unknown, not zero passengers."],
    ),
)
has_valid_pickup_zone = ms.dimension_column(
    name="has_valid_pickup_zone",
    entity=yellow_trips,
    column="has_valid_pickup_zone",
    ai_context=ms.ai_context(
        business_definition="Whether pickup location resolves to the official TLC zone lookup.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
has_valid_dropoff_zone = ms.dimension_column(
    name="has_valid_dropoff_zone",
    entity=yellow_trips,
    column="has_valid_dropoff_zone",
    ai_context=ms.ai_context(
        business_definition="Whether drop-off location resolves to the official TLC zone lookup.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
is_plausible_record = ms.dimension_column(
    name="is_plausible_record",
    entity=yellow_trips,
    column="is_plausible_record",
    ai_context=ms.ai_context(
        business_definition=(
            "Technical analysis predicate requiring source-month alignment, positive duration, "
            "bounded distance, duration, and implied speed, nonnegative fare and total, "
            "plus valid pickup and drop-off zones."
        ),
        guardrails=QUALITY_GUARDRAILS,
    ),
)

picked_up_at = ms.time_dimension_column(
    name="picked_up_at",
    entity=yellow_trips,
    column="picked_up_at",
    granularity="second",
    parse=ms.datetime(timezone="America/New_York"),
    is_default=True,
    ai_context=ms.ai_context(
        business_definition="Passenger pickup wall-clock time in America/New_York.",
        guardrails=LOCAL_TIME_GUARDRAILS,
    ),
)
dropped_off_at = ms.time_dimension_column(
    name="dropped_off_at",
    entity=yellow_trips,
    column="dropped_off_at",
    granularity="second",
    parse=ms.datetime(timezone="America/New_York"),
    ai_context=ms.ai_context(
        business_definition="Passenger drop-off wall-clock time in America/New_York.",
        guardrails=LOCAL_TIME_GUARDRAILS,
    ),
)

fare_amount = ms.measure_column(
    name="fare_amount",
    entity=yellow_trips,
    column="fare_amount_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Metered time-and-distance fare in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
extra_amount = ms.measure_column(
    name="extra_amount",
    entity=yellow_trips,
    column="extra_amount_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Miscellaneous TLC extras and surcharges in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
mta_tax_amount = ms.measure_column(
    name="mta_tax_amount",
    entity=yellow_trips,
    column="mta_tax_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="MTA tax amount in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
tip_amount = ms.measure_column(
    name="tip_amount",
    entity=yellow_trips,
    column="tip_amount_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Automatically recorded credit-card tip in USD.",
        guardrails=["Cash tips are generally not included."],
    ),
)
tolls_amount = ms.measure_column(
    name="tolls_amount",
    entity=yellow_trips,
    column="tolls_amount_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Passenger-paid tolls in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
improvement_surcharge_amount = ms.measure_column(
    name="improvement_surcharge_amount",
    entity=yellow_trips,
    column="improvement_surcharge_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="TLC improvement surcharge in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
total_amount = ms.measure_column(
    name="total_amount",
    entity=yellow_trips,
    column="total_amount_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Total passenger charge excluding cash tips.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
congestion_surcharge_amount = ms.measure_column(
    name="congestion_surcharge_amount",
    entity=yellow_trips,
    column="congestion_surcharge_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="NYS congestion surcharge in USD.",
        guardrails=["Do not conflate this field with the 2025 CBD congestion fee."],
    ),
)
airport_fee_amount = ms.measure_column(
    name="airport_fee_amount",
    entity=yellow_trips,
    column="airport_fee_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Published pickup airport fee in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
cbd_congestion_fee = ms.measure_column(
    name="cbd_congestion_fee",
    entity=yellow_trips,
    column="cbd_congestion_fee_usd",
    additivity="additive",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Congestion Relief Zone fee published on 2025 records.",
        guardrails=["The field applies from January 5, 2025; do not treat earlier zeros as noncompliance."],
    ),
)
trip_distance = ms.measure_column(
    name="trip_distance",
    entity=yellow_trips,
    column="trip_distance_miles",
    additivity="additive",
    unit="mile",
    ai_context=ms.ai_context(
        business_definition="Taximeter-reported trip distance in miles.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
trip_duration = ms.measure_column(
    name="trip_duration",
    entity=yellow_trips,
    column="trip_duration_minutes",
    additivity="additive",
    unit="minute",
    ai_context=ms.ai_context(
        business_definition="Elapsed minutes from pickup to drop-off.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
trip_duration_hours = ms.measure_column(
    name="trip_duration_hours",
    entity=yellow_trips,
    column="trip_duration_hours",
    additivity="additive",
    unit="hour",
    ai_context=ms.ai_context(
        business_definition="Elapsed hours from pickup to drop-off.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
passenger_count = ms.measure_column(
    name="passenger_count",
    entity=yellow_trips,
    column="passenger_count",
    additivity="additive",
    unit="passenger",
    ai_context=ms.ai_context(
        business_definition="Driver-entered passenger count when reported.",
        guardrails=["Missing values are unknown and must not be interpreted as zero."],
    ),
)

trip_count = ms.count(
    name="trip_count",
    entity=yellow_trips,
    ai_context=ms.ai_context(
        business_definition="Count of published Yellow Taxi trip records.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
fare_revenue = ms.aggregate(
    name="fare_revenue",
    measure=fare_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of metered fare amount in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
extra_charges = ms.aggregate(
    name="extra_charges",
    measure=extra_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of miscellaneous TLC extras and surcharges in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
mta_taxes = ms.aggregate(
    name="mta_taxes",
    measure=mta_tax_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of MTA tax amounts in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
tips = ms.aggregate(
    name="tips",
    measure=tip_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of automatically recorded tips in USD.",
        guardrails=["Cash tips are generally not included."],
    ),
)
tolls = ms.aggregate(
    name="tolls",
    measure=tolls_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of passenger-paid tolls in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
improvement_surcharges = ms.aggregate(
    name="improvement_surcharges",
    measure=improvement_surcharge_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of TLC improvement surcharges in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
total_charged = ms.aggregate(
    name="total_charged",
    measure=total_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of total passenger charges excluding unrecorded cash tips.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
congestion_surcharges = ms.aggregate(
    name="congestion_surcharges",
    measure=congestion_surcharge_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of NYS congestion surcharges in USD.",
        guardrails=["Do not conflate this field with total_cbd_congestion_fees."],
    ),
)
airport_fees = ms.aggregate(
    name="airport_fees",
    measure=airport_fee_amount,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of published airport fees in USD.",
        guardrails=MONEY_GUARDRAILS,
    ),
)
total_cbd_congestion_fees = ms.aggregate(
    name="total_cbd_congestion_fees",
    measure=cbd_congestion_fee,
    agg="sum",
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Sum of published Congestion Relief Zone fees in USD.",
        guardrails=["The field applies from January 5, 2025."],
    ),
)
total_surcharges = ms.linear(
    name="total_surcharges",
    add=[
        extra_charges,
        mta_taxes,
        improvement_surcharges,
        congestion_surcharges,
        airport_fees,
        total_cbd_congestion_fees,
    ],
    unit="USD",
    ai_context=ms.ai_context(
        business_definition=(
            "Sum of miscellaneous extras, MTA tax, improvement, congestion, airport, "
            "and CBD fee components."
        ),
        guardrails=["Excludes metered fare, tips, and tolls."],
    ),
)
total_trip_distance = ms.aggregate(
    name="total_trip_distance",
    measure=trip_distance,
    agg="sum",
    unit="mile",
    ai_context=ms.ai_context(
        business_definition="Sum of taximeter-reported trip miles.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
total_trip_duration = ms.aggregate(
    name="total_trip_duration",
    measure=trip_duration,
    agg="sum",
    unit="minute",
    ai_context=ms.ai_context(
        business_definition="Sum of elapsed trip minutes.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
total_trip_duration_hours = ms.aggregate(
    name="total_trip_duration_hours",
    measure=trip_duration_hours,
    agg="sum",
    unit="hour",
    ai_context=ms.ai_context(
        business_definition="Sum of elapsed trip hours.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
total_passengers = ms.aggregate(
    name="total_passengers",
    measure=passenger_count,
    agg="sum",
    unit="passenger",
    ai_context=ms.ai_context(
        business_definition="Sum of available driver-entered passenger counts.",
        guardrails=["Missing passenger counts are excluded from the sum."],
    ),
)

plausible_trip_count = ms.count(
    name="plausible_trip_count",
    entity=yellow_trips,
    filter=ms.where(is_plausible_record=True),
    ai_context=ms.ai_context(
        business_definition="Count of rows passing the demo's technical plausibility predicate.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
plausible_fare_revenue = ms.aggregate(
    name="plausible_fare_revenue",
    measure=fare_amount,
    agg="sum",
    filter=ms.where(is_plausible_record=True),
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Metered fare revenue from technically plausible records.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
plausible_total_trip_distance = ms.aggregate(
    name="plausible_total_trip_distance",
    measure=trip_distance,
    agg="sum",
    filter=ms.where(is_plausible_record=True),
    unit="mile",
    ai_context=ms.ai_context(
        business_definition="Reported miles from technically plausible records.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
plausible_total_trip_duration = ms.aggregate(
    name="plausible_total_trip_duration",
    measure=trip_duration,
    agg="sum",
    filter=ms.where(is_plausible_record=True),
    unit="minute",
    ai_context=ms.ai_context(
        business_definition="Elapsed minutes from technically plausible records.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
plausible_total_trip_duration_hours = ms.aggregate(
    name="plausible_total_trip_duration_hours",
    measure=trip_duration_hours,
    agg="sum",
    filter=ms.where(is_plausible_record=True),
    unit="hour",
    ai_context=ms.ai_context(
        business_definition="Elapsed hours from technically plausible records.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
plausible_total_passengers = ms.aggregate(
    name="plausible_total_passengers",
    measure=passenger_count,
    agg="sum",
    filter=ms.where(is_plausible_record=True, has_known_passenger_count=True),
    unit="passenger",
    ai_context=ms.ai_context(
        business_definition="Reported passengers from technically plausible records.",
        guardrails=["Missing values are excluded, not treated as zero."],
    ),
)
known_plausible_passenger_trip_count = ms.count(
    name="known_plausible_passenger_trip_count",
    entity=yellow_trips,
    filter=ms.where(is_plausible_record=True, has_known_passenger_count=True),
    ai_context=ms.ai_context(
        business_definition="Technically plausible records with a reported passenger count.",
        guardrails=["Use as the denominator for average_passengers."],
    ),
)
known_passenger_trip_count = ms.count(
    name="known_passenger_trip_count",
    entity=yellow_trips,
    filter=ms.where(has_known_passenger_count=True),
    ai_context=ms.ai_context(
        business_definition="Count of published records with a reported passenger count.",
        guardrails=["Use as the denominator for average_passengers."],
    ),
)
credit_card_trip_count = ms.count(
    name="credit_card_trip_count",
    entity=yellow_trips,
    filter=ms.where(payment_type="Credit card"),
    ai_context=ms.ai_context(
        business_definition="Count of records whose payment type is credit card.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
credit_card_fare_revenue = ms.aggregate(
    name="credit_card_fare_revenue",
    measure=fare_amount,
    agg="sum",
    filter=ms.where(payment_type="Credit card", is_plausible_record=True),
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Metered fare revenue from plausible credit-card records.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
credit_card_tips = ms.aggregate(
    name="credit_card_tips",
    measure=tip_amount,
    agg="sum",
    filter=ms.where(payment_type="Credit card", is_plausible_record=True),
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Automatically recorded tips from plausible credit-card records.",
        guardrails=["Cash tips and technically implausible records are outside this metric by design."],
    ),
)

average_fare = ms.ratio(
    name="average_fare",
    numerator=plausible_fare_revenue,
    denominator=plausible_trip_count,
    unit="USD",
    ai_context=ms.ai_context(
        business_definition="Metered fare revenue per technically plausible trip.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
average_trip_distance = ms.ratio(
    name="average_trip_distance",
    numerator=plausible_total_trip_distance,
    denominator=plausible_trip_count,
    unit="mile",
    ai_context=ms.ai_context(
        business_definition="Taximeter-reported miles per technically plausible trip.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
average_trip_duration = ms.ratio(
    name="average_trip_duration",
    numerator=plausible_total_trip_duration,
    denominator=plausible_trip_count,
    unit="minute",
    ai_context=ms.ai_context(
        business_definition="Elapsed minutes per technically plausible trip.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
average_passengers = ms.ratio(
    name="average_passengers",
    numerator=plausible_total_passengers,
    denominator=known_plausible_passenger_trip_count,
    unit="passenger",
    ai_context=ms.ai_context(
        business_definition=(
            "Average driver-entered passenger count among technically plausible records that report it."
        ),
        guardrails=[
            "Pair with plausible_passenger_count_coverage; missing values are excluded, not treated as zero."
        ],
    ),
)
passenger_count_coverage = ms.ratio(
    name="passenger_count_coverage",
    numerator=known_passenger_trip_count,
    denominator=trip_count,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Share of published records with a reported passenger count.",
        guardrails=["Use with average_passengers to assess representativeness."],
    ),
)
plausible_passenger_count_coverage = ms.ratio(
    name="plausible_passenger_count_coverage",
    numerator=known_plausible_passenger_trip_count,
    denominator=plausible_trip_count,
    unit="1",
    ai_context=ms.ai_context(
        business_definition=(
            "Share of technically plausible records with a reported passenger count."
        ),
        guardrails=["Use with average_passengers to assess its exact denominator coverage."],
    ),
)
tip_rate = ms.ratio(
    name="tip_rate",
    numerator=tips,
    denominator=fare_revenue,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Automatically recorded tips divided by metered fare revenue.",
        guardrails=["Use credit_card_tip_rate for rider tipping behavior."],
    ),
)
credit_card_tip_rate = ms.ratio(
    name="credit_card_tip_rate",
    numerator=credit_card_tips,
    denominator=credit_card_fare_revenue,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Recorded credit-card tips divided by credit-card metered fare revenue.",
        guardrails=["Represents recorded tips, not all rider gratuities."],
    ),
)
credit_card_trip_share = ms.ratio(
    name="credit_card_trip_share",
    numerator=credit_card_trip_count,
    denominator=trip_count,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Share of published records paid by credit card.",
        guardrails=PUBLISHED_RECORD_GUARDRAILS,
    ),
)
fare_per_mile = ms.ratio(
    name="fare_per_mile",
    numerator=plausible_fare_revenue,
    denominator=plausible_total_trip_distance,
    unit="USD/mile",
    ai_context=ms.ai_context(
        business_definition="Metered fare revenue per reported mile among plausible records.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
average_speed_mph = ms.ratio(
    name="average_speed_mph",
    numerator=plausible_total_trip_distance,
    denominator=plausible_total_trip_duration_hours,
    unit="mile/hour",
    ai_context=ms.ai_context(
        business_definition=(
            "Aggregate reported distance divided by aggregate elapsed hours among plausible records."
        ),
        guardrails=["The plausible subset caps record-level implied speed at 100 mph."],
    ),
)

implausible_trip_count = ms.linear(
    name="implausible_trip_count",
    add=[trip_count],
    subtract=[plausible_trip_count],
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Published rows failing at least one technical plausibility condition.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
implausible_record_rate = ms.ratio(
    name="implausible_record_rate",
    numerator=implausible_trip_count,
    denominator=trip_count,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Share of published rows failing the technical plausibility predicate.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
pickup_time_mismatch_count = ms.count(
    name="pickup_time_mismatch_count",
    entity=yellow_trips,
    filter=ms.where(pickup_time_matches_source_month=False),
    ai_context=ms.ai_context(
        business_definition="Count of rows whose pickup month differs from source-file month.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
nonpositive_duration_count = ms.count(
    name="nonpositive_duration_count",
    entity=yellow_trips,
    filter=ms.where(has_positive_duration=False),
    ai_context=ms.ai_context(
        business_definition="Count of rows whose drop-off is not after pickup.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
nonpositive_distance_count = ms.count(
    name="nonpositive_distance_count",
    entity=yellow_trips,
    filter=ms.where(has_positive_distance=False),
    ai_context=ms.ai_context(
        business_definition="Count of rows with zero, negative, or missing reported distance.",
        guardrails=["Zero-distance records are review flags, not automatic proof of invalidity."],
    ),
)
negative_fare_count = ms.count(
    name="negative_fare_count",
    entity=yellow_trips,
    filter=ms.where(has_nonnegative_fare=False),
    ai_context=ms.ai_context(
        business_definition="Count of rows with negative or missing metered fare.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
negative_total_count = ms.count(
    name="negative_total_count",
    entity=yellow_trips,
    filter=ms.where(has_nonnegative_total=False),
    ai_context=ms.ai_context(
        business_definition="Count of rows with negative or missing total charge.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
invalid_pickup_zone_count = ms.count(
    name="invalid_pickup_zone_count",
    entity=yellow_trips,
    filter=ms.where(has_valid_pickup_zone=False),
    ai_context=ms.ai_context(
        business_definition="Count of rows whose pickup zone key does not resolve.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
invalid_dropoff_zone_count = ms.count(
    name="invalid_dropoff_zone_count",
    entity=yellow_trips,
    filter=ms.where(has_valid_dropoff_zone=False),
    ai_context=ms.ai_context(
        business_definition="Count of rows whose drop-off zone key does not resolve.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
pickup_time_mismatch_rate = ms.ratio(
    name="pickup_time_mismatch_rate",
    numerator=pickup_time_mismatch_count,
    denominator=trip_count,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Share of rows whose pickup month differs from source-file month.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
nonpositive_duration_record_rate = ms.ratio(
    name="nonpositive_duration_record_rate",
    numerator=nonpositive_duration_count,
    denominator=trip_count,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Share of rows whose drop-off is not after pickup.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
nonpositive_distance_record_rate = ms.ratio(
    name="nonpositive_distance_record_rate",
    numerator=nonpositive_distance_count,
    denominator=trip_count,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Share of rows with nonpositive or missing reported distance.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
negative_fare_record_rate = ms.ratio(
    name="negative_fare_record_rate",
    numerator=negative_fare_count,
    denominator=trip_count,
    unit="1",
    ai_context=ms.ai_context(
        business_definition="Share of rows with negative or missing metered fare.",
        guardrails=QUALITY_GUARDRAILS,
    ),
)
