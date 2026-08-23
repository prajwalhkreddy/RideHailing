"""NYC Yellow Taxi ingestion and NB2-compatible trip preparation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


LEGACY_TRIP_COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "passenger_count",
    "trip_distance",
    "fare_amount",
]
COORDINATE_COLUMNS = {
    "pickup": ("pickup_longitude", "pickup_latitude"),
    "dropoff": ("dropoff_longitude", "dropoff_latitude"),
}


def inspect_taxi_schema(path: str | Path) -> dict[str, Any]:
    """Inspect parquet metadata without loading the January data into memory."""
    parquet_path = Path(path)
    if not parquet_path.is_file():
        raise FileNotFoundError(f"Yellow Taxi parquet not found: {parquet_path}")
    source = pq.ParquetFile(parquet_path)
    return {
        "path": str(parquet_path),
        "records": source.metadata.num_rows,
        "row_groups": source.metadata.num_row_groups,
        "columns": source.schema_arrow.names,
        "schema": str(source.schema_arrow),
    }


def load_taxi_data(path: str | Path) -> pd.DataFrame:
    """Load only columns used by the legacy NB2 trip-assignment workflow.

    Legacy reference: ``NB2_GridToTripAssignment``, which selected these seven
    fields before validating location IDs. The current January 2026 file has
    no pickup/dropoff coordinates; callers must use the explicit legacy
    zone-to-grid assignment path unless a coordinate-bearing source is used.
    """
    schema = inspect_taxi_schema(path)
    missing = set(LEGACY_TRIP_COLUMNS) - set(schema["columns"])
    if missing:
        raise ValueError(
            "Yellow Taxi input is incompatible with legacy NB2; missing columns: "
            f"{sorted(missing)} in {path}"
        )
    return pd.read_parquet(path, columns=LEGACY_TRIP_COLUMNS)


def prepare_legacy_trips(
    trips: pd.DataFrame, valid_zone_ids: set[int]
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply the documented NB2 location-ID filtering without new filters.

    NB2 drops missing pickup/dropoff location IDs, converts them to ``int16``,
    and retains records only when both IDs appear in the NB1 zone-to-grid map.
    It does not filter on fare, passenger count, distance, or duration; this
    implementation deliberately preserves that behavior.
    """
    missing = set(LEGACY_TRIP_COLUMNS) - set(trips.columns)
    if missing:
        raise ValueError(f"Trip frame missing legacy columns: {sorted(missing)}")

    records_loaded = len(trips)
    prepared = trips.dropna(subset=["PULocationID", "DOLocationID"]).copy()
    missing_location_ids = records_loaded - len(prepared)
    prepared["PULocationID"] = prepared["PULocationID"].astype(np.int16)
    prepared["DOLocationID"] = prepared["DOLocationID"].astype(np.int16)

    location_mask = prepared["PULocationID"].isin(valid_zone_ids) & prepared[
        "DOLocationID"
    ].isin(valid_zone_ids)
    valid = prepared.loc[location_mask].copy().reset_index(drop=True)
    invalid_zone_ids = len(prepared) - len(valid)
    return valid, {
        "records_loaded": records_loaded,
        "missing_location_ids": missing_location_ids,
        "invalid_zone_ids": invalid_zone_ids,
        "records_after_filtering": len(valid),
    }
