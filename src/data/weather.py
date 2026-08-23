"""Legacy-compatible validation of the processed Meteostat weather artifact."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import pandas as pd


WEATHER_COLUMNS = ["Datetime", "Temperature", "WindSpeed", "WeatherCode"]
LEGACY_METEOSTAT_VERSION = "1.7.6"


def prepare_processed_weather(weather: pd.DataFrame) -> pd.DataFrame:
    """Reproduce the legacy utility's weather preparation semantics.

    Legacy reference: ``Utility_WeatherDownloader.ipynb`` retains Meteostat's
    hourly ``temp``, ``wspd``, and ``coco`` fields after renaming them, sorts
    by ``Datetime``, then forward-fills and backward-fills missing values. No
    interpolation, lag, timezone conversion, or normalization is performed.
    """
    missing = set(WEATHER_COLUMNS) - set(weather.columns)
    if missing:
        raise ValueError(f"Processed weather is missing required columns: {sorted(missing)}")
    prepared = weather[WEATHER_COLUMNS].copy()
    prepared["Datetime"] = pd.to_datetime(prepared["Datetime"], errors="raise")
    if prepared["Datetime"].dt.tz is not None:
        raise ValueError(
            "Weather Datetime values are timezone-aware. NB3 preserves legacy "
            "timezone-naive timestamp semantics; provide a validated naive artifact "
            "or make an explicit research decision before building demand data."
        )
    if prepared["Datetime"].isna().any():
        raise ValueError("Processed weather contains missing Datetime values.")
    prepared = prepared.sort_values("Datetime").reset_index(drop=True)
    return prepared.ffill().bfill()


def validate_processed_weather_contract(weather: pd.DataFrame, month: str) -> None:
    """Validate the hourly weather input required for a complete NB3 month.

    This is an engineering contract around the legacy data: NB3's left join
    asserts no missing weather values. A complete, unique hourly calendar is
    therefore required instead of silently treating a source outage as demand
    data with missing features.
    """
    prepared = prepare_processed_weather(weather)
    start = pd.Timestamp(f"{month}-01 00:00:00")
    end = start + pd.offsets.MonthBegin(1)
    expected = pd.date_range(start, end, freq="h", inclusive="left")
    if prepared["Datetime"].duplicated().any():
        raise ValueError("Processed weather contains duplicate hourly Datetime values.")
    actual = pd.DatetimeIndex(prepared["Datetime"])
    if not actual.equals(expected):
        raise ValueError(
            f"Weather timestamps must cover every hour of {month} ({len(expected)} rows) "
            "with timezone-naive hourly values."
        )
    if prepared[WEATHER_COLUMNS[1:]].isna().any().any():
        raise ValueError("Processed weather still contains missing feature values after legacy filling.")


def load_processed_weather(path: str | Path, month: str) -> pd.DataFrame:
    """Load and validate the required persisted legacy weather input.

    The stage never downloads weather or chooses a replacement provider. The
    absent artifact is an actionable external input requirement, not a reason
    to build a partial demand table.
    """
    weather_path = Path(path)
    if not weather_path.is_file():
        raise FileNotFoundError(
            "NB3 requires the legacy-compatible processed weather artifact: "
            f"{weather_path}. Expected columns are {WEATHER_COLUMNS}. "
            "Create or place the reviewed Meteostat-derived artifact explicitly; "
            "this build will not download or substitute weather data."
        )
    weather = prepare_processed_weather(pd.read_parquet(weather_path))
    validate_processed_weather_contract(weather, month)
    return weather


def fetch_hourly_weather(
    latitude: float, longitude: float, altitude_m: int, start: str, end: str
) -> pd.DataFrame:
    """Fetch the exact legacy ``Hourly(Point(...))`` Meteostat response.

    Legacy utility behaviour is intentionally retained: use Meteostat 1.7.6,
    construct a point at the supplied NYC coordinates, pass naive start/end
    datetimes, and call ``Hourly(point, start, end).fetch()``. No timezone is
    supplied or transformed here because the notebook did neither.
    """
    installed_version = importlib.metadata.version("meteostat")
    if installed_version != LEGACY_METEOSTAT_VERSION:
        raise RuntimeError(
            f"Legacy weather reproduction requires Meteostat {LEGACY_METEOSTAT_VERSION}, "
            f"but {installed_version} is installed. Do not substitute a 2.x API silently."
        )
    from meteostat import Hourly, Point

    point = Point(latitude, longitude, altitude_m)
    response = Hourly(point, pd.Timestamp(start).to_pydatetime(), pd.Timestamp(end).to_pydatetime()).fetch()
    if response is None or response.empty:
        raise RuntimeError(
            "Meteostat Hourly(Point(...)).fetch() returned no January weather data. "
            "No partial artifact was written."
        )
    required = {"temp", "wspd", "coco"}
    if missing := required - set(response.columns):
        raise RuntimeError(f"Meteostat response lacks legacy required fields: {sorted(missing)}")
    return response


def prepare_weather(raw_weather: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, int]]]:
    """Retain and fill the legacy Meteostat variables without new features.

    The utility notebook resets the Meteostat ``time`` index, retains only
    ``temp``, ``wspd``, and ``coco``, renames them, sorts, forward-fills, and
    then backward-fills leading gaps. The implementation keeps exactly that
    operation order; no interpolation, normalization, lags, or rolling fields
    are introduced.
    """
    table = raw_weather.reset_index()
    timestamp_column = "time" if "time" in table.columns else table.columns[0]
    required = {timestamp_column, "temp", "wspd", "coco"}
    if missing := required - set(table.columns):
        raise ValueError(f"Meteostat response cannot be prepared; missing fields: {sorted(missing)}")
    selected = table[[timestamp_column, "temp", "wspd", "coco"]].rename(
        columns={timestamp_column: "Datetime", "temp": "Temperature", "wspd": "WindSpeed", "coco": "WeatherCode"}
    )
    before = selected[WEATHER_COLUMNS[1:]].isna().sum().astype(int).to_dict()
    prepared = prepare_processed_weather(selected)
    after = prepared[WEATHER_COLUMNS[1:]].isna().sum().astype(int).to_dict()
    return prepared, {"before_fill": before, "after_fill": after}


def validate_weather(weather: pd.DataFrame, month: str) -> None:
    """Validate the persisted weather against the complete legacy NB3 contract."""
    validate_processed_weather_contract(weather, month)


def weather_metadata_path(output_path: str | Path) -> Path:
    """Return the provenance sidecar for the four-column legacy weather table."""
    output = Path(output_path)
    return output.with_name("weather_metadata_2026_01.json")


def save_weather(
    weather: pd.DataFrame,
    output_path: str | Path,
    metadata: dict[str, Any],
) -> tuple[Path, Path]:
    """Persist the legacy four-column artifact and its separate provenance JSON."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    weather.to_parquet(output, index=False)
    artifact_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    metadata_path = weather_metadata_path(output)
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump({**metadata, "weather_artifact_path": str(output), "output_sha256": artifact_hash}, handle, indent=2, sort_keys=True)
    return output, metadata_path


def build_weather_metadata(
    *, weather: pd.DataFrame, raw_row_count: int, fill_counts: dict[str, dict[str, int]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create traceability metadata while preserving the legacy table schema."""
    timezone = weather["Datetime"].dt.tz
    timezone_status = "timezone-naive returned by Meteostat; no conversion applied" if timezone is None else str(timezone)
    return {
        "provider": config["provider"],
        "meteostat_version": importlib.metadata.version("meteostat"),
        "latitude": config["latitude"],
        "longitude": config["longitude"],
        "altitude_m": config["altitude_m"],
        "start": config["start"],
        "end": config["end"],
        "query_method": "Hourly(Point(latitude, longitude, altitude_m), start, end).fetch()",
        "raw_row_count": raw_row_count,
        "processed_row_count": len(weather),
        "columns": WEATHER_COLUMNS,
        "missing_values": fill_counts,
        "timestamp_dtype": str(weather["Datetime"].dtype),
        "taxi_timezone_status": "naive / legacy unspecified",
        "weather_timezone_status": timezone_status,
        "timezone_alignment": "legacy behaviour reproduced; explicit research decision pending",
        "build_timestamp_utc": datetime.now(UTC).isoformat(),
    }
