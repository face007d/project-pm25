const fs = require("node:fs");
const path = require("node:path");

const notebookPath = path.resolve("notebooks", "pm25_nextday_clean_colab.ipynb");
const uploadPath = path.resolve("notebooks", "UPLOAD_THIS_TO_COLAB_pm25_nextday_clean.ipynb");
const nasaUploadPath = path.resolve("notebooks", "UPLOAD_THIS_TO_COLAB_pm25_nextday_clean_nasa.ipynb");

function lines(text) {
  const normalized = text.replace(/^\n/, "").replace(/\n$/, "");
  return normalized.split("\n").map((line) => `${line}\n`);
}

function md(text) {
  return {
    cell_type: "markdown",
    metadata: {},
    source: lines(text),
  };
}

function code(text) {
  return {
    cell_type: "code",
    execution_count: null,
    metadata: {},
    outputs: [],
    source: lines(text),
  };
}

const cells = [
  md(`
# PM2.5 Next-Day Forecasting Clean Colab + NASA FIRMS

Notebook ใหม่นี้ทำงานแบบเรียงตรง:

1. upload Excel dataset
2. ดึง NASA FIRMS hotspot แล้วสร้าง fire / wind-distance features
3. สร้าง lag / rolling / spatial features จากข้อมูลย้อนหลังเท่านั้น
4. เทรนหลายโมเดลเพื่อทำนาย PM2.5 ล่วงหน้า 24 ชั่วโมง
5. เปรียบเทียบ RMSE, MAE, R2 และ forecast accuracy ภายใน tolerance เช่น +/-10, +/-20 ug/m3
6. export ตาราง กราฟ โมเดล และ ZIP

โจทย์หลักคือ numeric forecasting ไม่ใช่ anomaly classification
`),

  code(`
# =========================
# 0. Setup and config
# =========================

!pip -q install openpyxl joblib scikit-learn matplotlib

import json
import math
import os
import io
import getpass
import requests
import shutil
import time
import warnings
import zipfile
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

LOCAL_XLSX = "/content/pm25_training_dataset_5stations_2020-2026.xlsx"
OUTPUT_DIR = Path("/content/pm25_nextday_clean_outputs")
FIGURE_DIR = OUTPUT_DIR / "figures"
MODEL_DIR = OUTPUT_DIR / "models"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

HORIZON_HOURS = 24
LAGS_HOURS = [0, 1, 3, 6, 12, 24, 48, 72, 168]
ROLLING_WINDOWS_HOURS = [24, 48, 72, 168]
ERROR_TOLERANCES = [5, 10, 15, 20, 25, 30]
RUN_DEEP_LEARNING_MODELS = False
DL_LOOKBACK_STEPS = 72
DL_EPOCHS = 45
DL_BATCH_SIZE = 256
DL_PATIENCE = 7
SAVE_LARGE_MODEL_FILES = False

# NASA FIRMS hotspot features.
# MAP_KEY is free from https://firms.modaps.eosdis.nasa.gov/api/map_key/
RUN_NASA_FIRMS_HOTSPOT_FEATURES = True
FIRMS_MAP_KEY = ""
if RUN_NASA_FIRMS_HOTSPOT_FEATURES and not FIRMS_MAP_KEY.strip():
    FIRMS_MAP_KEY = getpass.getpass("Paste NASA FIRMS MAP_KEY: ").strip()

FIRMS_SOURCES = ["VIIRS_SNPP_SP", "VIIRS_NOAA20_SP"]
FIRMS_DAY_RANGE = 5
FIRMS_BBOX_BUFFER_DEGREES = 3.0
FIRMS_MAX_DISTANCE_KM = 300.0
FIRMS_DISTANCE_DECAY_KM = 100.0
FIRMS_MIN_CONFIDENCE_SCORE = 30.0
FIRMS_REQUEST_SLEEP_SECONDS = 0.08

FIRE_FEATURE_COLUMNS = [
    "hotspot_count_24h",
    "hotspot_count_48h",
    "hotspot_count_72h",
    "hotspot_count_168h",
    "hotspot_frp_sum_24h",
    "hotspot_frp_sum_72h",
    "hotspot_frp_sum_168h",
    "nearest_hotspot_distance_km",
    "upwind_hotspot_count_24h",
    "upwind_hotspot_count_72h",
    "upwind_frp_weighted_24h",
    "upwind_frp_weighted_72h",
]

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15

print("Output folder:", OUTPUT_DIR)
`),

  code(`
# =========================
# 1. Upload or reuse Excel dataset
# =========================

def is_valid_xlsx(path):
    if not os.path.exists(path) or not zipfile.is_zipfile(path):
        return False
    with zipfile.ZipFile(path) as zf:
        return "xl/workbook.xml" in set(zf.namelist())

if os.path.exists(LOCAL_XLSX) and not is_valid_xlsx(LOCAL_XLSX):
    print("Removing invalid local file:", LOCAL_XLSX)
    os.remove(LOCAL_XLSX)

if not os.path.exists(LOCAL_XLSX):
    from google.colab import files
    print("Upload this Excel file:")
    print("pm25_training_dataset_5stations_2020-2026.xlsx")
    uploaded = files.upload()
    if not uploaded:
        raise RuntimeError("No file uploaded.")
    xlsx_names = [name for name in uploaded.keys() if name.lower().endswith(".xlsx")]
    selected_name = xlsx_names[0] if xlsx_names else next(iter(uploaded.keys()))
    with open(LOCAL_XLSX, "wb") as fh:
        fh.write(uploaded[selected_name])
    print("Uploaded:", selected_name)

print("Local file:", LOCAL_XLSX)
print("File size:", os.path.getsize(LOCAL_XLSX), "bytes")
print("Valid xlsx:", is_valid_xlsx(LOCAL_XLSX))
if not is_valid_xlsx(LOCAL_XLSX):
    raise RuntimeError("Uploaded file is not a valid .xlsx workbook.")
`),

  code(`
# =========================
# 2. Load workbook
# =========================

required_sheets = [
    "model_ready_openmeteo_aq",
    "train_ready_pm25",
    "stations",
    "data_quality",
    "sources",
]

book = pd.read_excel(LOCAL_XLSX, sheet_name=required_sheets, engine="openpyxl")
model_raw = book["model_ready_openmeteo_aq"].copy()
obs_raw = book["train_ready_pm25"].copy()
stations = book["stations"].copy()
quality = book["data_quality"].copy()
sources = book["sources"].copy()

def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

model_raw = normalize_columns(model_raw)
obs_raw = normalize_columns(obs_raw)
stations = normalize_columns(stations)
quality = normalize_columns(quality)
sources = normalize_columns(sources)

print("Open-Meteo/CAMS rows:", len(model_raw))
print("Air4Thai rows:", len(obs_raw))
print("Stations:")
display(stations[["station_id", "province", "latitude", "longitude"]].drop_duplicates())
display(quality)
display(sources)
`),

  code(`
# =========================
# 3. Clean data and build next-day features
# =========================

numeric_cols = [
    "latitude",
    "longitude",
    "pm25",
    "pm10",
    "o3",
    "co",
    "no2",
    "so2",
    "wind_speed",
    "wind_direction",
    "temperature",
    "relative_humidity",
    "pressure",
    "precipitation",
]

df = model_raw.copy()
df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
df = df.dropna(subset=["datetime", "station_id"]).copy()
df["station_id"] = df["station_id"].astype(str)
df["province"] = df["province"].astype(str)

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.sort_values(["station_id", "datetime"]).reset_index(drop=True)
df["hour"] = df["datetime"].dt.hour
df["dayofyear"] = df["datetime"].dt.dayofyear
df["month"] = df["datetime"].dt.month
df["target_datetime"] = df["datetime"] + pd.Timedelta(hours=HORIZON_HOURS)

df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
df["doy_sin"] = np.sin(2 * np.pi * df["dayofyear"] / 366)
df["doy_cos"] = np.cos(2 * np.pi * df["dayofyear"] / 366)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

if "wind_direction" in df.columns:
    df["wind_dir_sin"] = np.sin(np.deg2rad(df["wind_direction"]))
    df["wind_dir_cos"] = np.cos(np.deg2rad(df["wind_direction"]))

def date_chunks(start_ts, end_ts, day_range):
    current = pd.Timestamp(start_ts).floor("D")
    end = pd.Timestamp(end_ts).floor("D")
    while current <= end:
        days = min(day_range, int((end - current).days) + 1)
        yield current.strftime("%Y-%m-%d"), days
        current = current + pd.Timedelta(days=days)

def firms_bbox_from_stations(station_frame, buffer_degrees):
    lat = pd.to_numeric(station_frame["latitude"], errors="coerce")
    lon = pd.to_numeric(station_frame["longitude"], errors="coerce")
    west = max(float(lon.min() - buffer_degrees), -180.0)
    south = max(float(lat.min() - buffer_degrees), -90.0)
    east = min(float(lon.max() + buffer_degrees), 180.0)
    north = min(float(lat.max() + buffer_degrees), 90.0)
    return f"{west:.4f},{south:.4f},{east:.4f},{north:.4f}"

def confidence_to_score(value):
    text = str(value).strip().lower()
    if text in ["h", "high"]:
        return 80.0
    if text in ["n", "nominal"]:
        return 50.0
    if text in ["l", "low"]:
        return 20.0
    try:
        return float(text)
    except Exception:
        return np.nan

def download_firms_hotspots(map_key, sources, bbox, start_ts, end_ts):
    rows = []
    request_count = 0
    for source in sources:
        for start_date, days in date_chunks(start_ts, end_ts, FIRMS_DAY_RANGE):
            request_count += 1
            url = (
                "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
                f"{map_key}/{source}/{bbox}/{days}/{start_date}"
            )
            try:
                response = requests.get(url, timeout=90)
                if response.status_code == 429:
                    print("FIRMS rate limit, sleeping 30 seconds:", source, start_date)
                    time.sleep(30)
                    response = requests.get(url, timeout=90)
                response.raise_for_status()
                text = response.text.strip()
                if text and "latitude" in text.splitlines()[0].lower():
                    chunk = pd.read_csv(io.StringIO(text))
                    if len(chunk):
                        chunk["firms_source"] = source
                        rows.append(chunk)
                if request_count % 50 == 0:
                    print("FIRMS requests completed:", request_count)
            except Exception as exc:
                print("FIRMS download skipped:", source, start_date, exc)
            time.sleep(FIRMS_REQUEST_SLEEP_SECONDS)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True).drop_duplicates()

def prepare_firms_hotspots(hotspots):
    if len(hotspots) == 0:
        return hotspots
    hotspots = hotspots.copy()
    hotspots["latitude"] = pd.to_numeric(hotspots["latitude"], errors="coerce")
    hotspots["longitude"] = pd.to_numeric(hotspots["longitude"], errors="coerce")
    frp_values = (
        hotspots["frp"]
        if "frp" in hotspots.columns
        else pd.Series(0.0, index=hotspots.index)
    )
    hotspots["frp"] = pd.to_numeric(frp_values, errors="coerce").fillna(0.0)
    confidence_values = (
        hotspots["confidence"]
        if "confidence" in hotspots.columns
        else pd.Series(np.nan, index=hotspots.index)
    )
    hotspots["confidence_score"] = confidence_values.apply(confidence_to_score)
    acq_time = hotspots["acq_time"].astype(str).str.replace(".0", "", regex=False).str.zfill(4)
    acquired_utc = pd.to_datetime(
        hotspots["acq_date"].astype(str) + acq_time,
        format="%Y-%m-%d%H%M",
        errors="coerce",
        utc=True,
    )
    hotspots["datetime"] = acquired_utc.dt.tz_convert("Asia/Bangkok").dt.tz_localize(None)
    hotspots["hotspot_hour"] = hotspots["datetime"].dt.floor("h")
    hotspots = hotspots.dropna(subset=["latitude", "longitude", "datetime"])
    hotspots = hotspots[hotspots["confidence_score"].fillna(0) >= FIRMS_MIN_CONFIDENCE_SCORE]
    return hotspots

def haversine_km_vector(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    )
    return 2 * r * np.arcsin(np.sqrt(a))

def bearing_deg_vector(lat1, lon1, lat2, lon2):
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlon_rad = np.radians(lon2 - lon1)
    y = np.sin(dlon_rad) * np.cos(lat2_rad)
    x = (
        np.cos(lat1_rad) * np.sin(lat2_rad)
        - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon_rad)
    )
    return (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0

def sector_weighted_lookup(rolling_sector_df, wind_direction):
    arr = rolling_sector_df.to_numpy(dtype="float32")
    wind = (
        pd.to_numeric(wind_direction, errors="coerce")
        .interpolate(limit_direction="both")
        .ffill()
        .bfill()
        .fillna(0.0)
    )
    sectors = np.floor(((wind.to_numpy(dtype="float32") + 22.5) % 360.0) / 45.0).astype(int) % 8
    row_idx = np.arange(len(sectors))
    return (
        arr[row_idx, sectors]
        + 0.5 * arr[row_idx, (sectors - 1) % 8]
        + 0.5 * arr[row_idx, (sectors + 1) % 8]
    )

def make_default_fire_features(base_df):
    fire = base_df[["datetime", "station_id"]].drop_duplicates().copy()
    for col in FIRE_FEATURE_COLUMNS:
        fire[col] = 0.0
    fire["nearest_hotspot_distance_km"] = FIRMS_MAX_DISTANCE_KM
    return fire

def build_fire_features_by_station_hour(hotspots, base_df, station_frame):
    frames = []
    timeline = pd.date_range(
        start=base_df["datetime"].min().floor("h"),
        end=base_df["datetime"].max().ceil("h"),
        freq="h",
    )
    station_frame = station_frame.drop_duplicates("station_id").copy()

    for _, station in station_frame.iterrows():
        sid = str(station["station_id"])
        station_lat = float(station["latitude"])
        station_lon = float(station["longitude"])
        station_rows = (
            base_df[base_df["station_id"] == sid][["datetime", "wind_direction"]]
            .drop_duplicates("datetime")
            .sort_values("datetime")
        )

        station_hotspots = hotspots.copy()
        if len(station_hotspots):
            station_hotspots["distance_km"] = haversine_km_vector(
                station_lat,
                station_lon,
                station_hotspots["latitude"].to_numpy(),
                station_hotspots["longitude"].to_numpy(),
            )
            station_hotspots = station_hotspots[
                station_hotspots["distance_km"] <= FIRMS_MAX_DISTANCE_KM
            ].copy()

        hourly = pd.DataFrame(index=timeline)
        hourly["fire_count_hour"] = 0.0
        hourly["frp_sum_hour"] = 0.0
        hourly["nearest_hour"] = np.nan

        if len(station_hotspots):
            station_hotspots["bearing_deg"] = bearing_deg_vector(
                station_lat,
                station_lon,
                station_hotspots["latitude"].to_numpy(),
                station_hotspots["longitude"].to_numpy(),
            )
            station_hotspots["bearing_sector"] = (
                np.floor(((station_hotspots["bearing_deg"] + 22.5) % 360.0) / 45.0)
                .astype(int)
                % 8
            )
            station_hotspots["frp_distance_weighted"] = (
                station_hotspots["frp"]
                * np.exp(-station_hotspots["distance_km"] / FIRMS_DISTANCE_DECAY_KM)
            )
            grouped = station_hotspots.groupby("hotspot_hour").agg(
                fire_count_hour=("latitude", "size"),
                frp_sum_hour=("frp", "sum"),
                nearest_hour=("distance_km", "min"),
            )
            hourly.update(grouped)
            sector_count = (
                station_hotspots
                .pivot_table(index="hotspot_hour", columns="bearing_sector", values="latitude", aggfunc="count", fill_value=0)
                .reindex(timeline, fill_value=0)
            )
            sector_frp_weighted = (
                station_hotspots
                .pivot_table(index="hotspot_hour", columns="bearing_sector", values="frp_distance_weighted", aggfunc="sum", fill_value=0)
                .reindex(timeline, fill_value=0)
            )
        else:
            sector_count = pd.DataFrame(0.0, index=timeline, columns=range(8))
            sector_frp_weighted = pd.DataFrame(0.0, index=timeline, columns=range(8))

        for sector in range(8):
            if sector not in sector_count.columns:
                sector_count[sector] = 0.0
            if sector not in sector_frp_weighted.columns:
                sector_frp_weighted[sector] = 0.0
        sector_count = sector_count[range(8)].sort_index(axis=1)
        sector_frp_weighted = sector_frp_weighted[range(8)].sort_index(axis=1)

        hourly = hourly.fillna({"fire_count_hour": 0.0, "frp_sum_hour": 0.0})
        hourly["hotspot_count_24h"] = hourly["fire_count_hour"].rolling("24h", min_periods=1).sum()
        hourly["hotspot_count_48h"] = hourly["fire_count_hour"].rolling("48h", min_periods=1).sum()
        hourly["hotspot_count_72h"] = hourly["fire_count_hour"].rolling("72h", min_periods=1).sum()
        hourly["hotspot_count_168h"] = hourly["fire_count_hour"].rolling("168h", min_periods=1).sum()
        hourly["hotspot_frp_sum_24h"] = hourly["frp_sum_hour"].rolling("24h", min_periods=1).sum()
        hourly["hotspot_frp_sum_72h"] = hourly["frp_sum_hour"].rolling("72h", min_periods=1).sum()
        hourly["hotspot_frp_sum_168h"] = hourly["frp_sum_hour"].rolling("168h", min_periods=1).sum()
        hourly["nearest_hotspot_distance_km"] = (
            hourly["nearest_hour"].rolling("24h", min_periods=1).min().fillna(FIRMS_MAX_DISTANCE_KM)
        )

        station_wind = (
            station_rows.set_index("datetime")
            .reindex(timeline)["wind_direction"]
            .astype("float32")
        )
        hourly["upwind_hotspot_count_24h"] = sector_weighted_lookup(
            sector_count.rolling("24h", min_periods=1).sum(),
            station_wind,
        )
        hourly["upwind_hotspot_count_72h"] = sector_weighted_lookup(
            sector_count.rolling("72h", min_periods=1).sum(),
            station_wind,
        )
        hourly["upwind_frp_weighted_24h"] = sector_weighted_lookup(
            sector_frp_weighted.rolling("24h", min_periods=1).sum(),
            station_wind,
        )
        hourly["upwind_frp_weighted_72h"] = sector_weighted_lookup(
            sector_frp_weighted.rolling("72h", min_periods=1).sum(),
            station_wind,
        )

        feature_frame = hourly[FIRE_FEATURE_COLUMNS].reset_index().rename(columns={"index": "datetime"})
        feature_frame["station_id"] = sid
        frames.append(feature_frame)

    return pd.concat(frames, ignore_index=True)

station_frame = df[["station_id", "province", "latitude", "longitude"]].drop_duplicates("station_id").copy()
fire_feature_status = {
    "enabled": bool(RUN_NASA_FIRMS_HOTSPOT_FEATURES and FIRMS_MAP_KEY.strip()),
    "source": "NASA FIRMS Area API",
    "sources": FIRMS_SOURCES,
    "status": "skipped",
    "hotspot_rows": 0,
    "note": "Features use current/past hotspot detections only, then roll over 24-168 hours.",
}
fire_features = make_default_fire_features(df)

if RUN_NASA_FIRMS_HOTSPOT_FEATURES and FIRMS_MAP_KEY.strip():
    bbox = firms_bbox_from_stations(station_frame, FIRMS_BBOX_BUFFER_DEGREES)
    print("Downloading NASA FIRMS hotspots for bbox:", bbox)
    firms_raw = download_firms_hotspots(
        FIRMS_MAP_KEY.strip(),
        FIRMS_SOURCES,
        bbox,
        df["datetime"].min() - pd.Timedelta(days=7),
        df["datetime"].max(),
    )
    firms_hotspots = prepare_firms_hotspots(firms_raw)
    fire_feature_status["hotspot_rows"] = int(len(firms_hotspots))
    if len(firms_hotspots):
        firms_raw.to_csv(OUTPUT_DIR / "nasa_firms_hotspots_raw.csv", index=False)
        firms_hotspots.to_csv(OUTPUT_DIR / "nasa_firms_hotspots_prepared.csv", index=False)
        fire_features = build_fire_features_by_station_hour(firms_hotspots, df, station_frame)
        fire_features.to_csv(OUTPUT_DIR / "nasa_fire_features_by_station_hour.csv", index=False)
        fire_feature_status["status"] = "enabled"

        fig, ax = plt.subplots(figsize=(8, 7))
        ax.scatter(
            firms_hotspots["longitude"],
            firms_hotspots["latitude"],
            s=np.clip(firms_hotspots["frp"].fillna(1).to_numpy(), 1, 80),
            alpha=0.20,
            c=firms_hotspots["frp"].fillna(0),
            cmap="inferno",
        )
        ax.scatter(station_frame["longitude"], station_frame["latitude"], s=90, c="#2563eb", edgecolor="white")
        for _, station in station_frame.iterrows():
            ax.text(station["longitude"], station["latitude"], station["station_id"], fontsize=9, ha="left", va="bottom")
        ax.set_title("NASA FIRMS Hotspots around the 5 PM2.5 Stations")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True, alpha=0.25)
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / "nasa_firms_hotspot_map.png", dpi=180, bbox_inches="tight")
        plt.show()
    else:
        fire_feature_status["status"] = "no_hotspots_returned"
        print("NASA FIRMS returned no hotspot rows after filtering. Default fire features will be used.")
else:
    print("Skipping NASA FIRMS hotspot features. Set RUN_NASA_FIRMS_HOTSPOT_FEATURES=True and provide FIRMS_MAP_KEY to enable.")

df = df.drop(columns=FIRE_FEATURE_COLUMNS, errors="ignore").merge(
    fire_features,
    on=["datetime", "station_id"],
    how="left",
)
for col in FIRE_FEATURE_COLUMNS:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    if col == "nearest_hotspot_distance_km":
        df[col] = df[col].fillna(FIRMS_MAX_DISTANCE_KM)
    else:
        df[col] = df[col].fillna(0.0)

with open(OUTPUT_DIR / "nasa_fire_feature_status.json", "w", encoding="utf-8") as fh:
    json.dump(fire_feature_status, fh, ensure_ascii=False, indent=2)

display(pd.DataFrame([fire_feature_status]))
display(df[["datetime", "station_id"] + FIRE_FEATURE_COLUMNS].head())

for lag in LAGS_HOURS:
    df[f"pm25_lag_{lag}h"] = df.groupby("station_id")["pm25"].shift(lag)

for window in ROLLING_WINDOWS_HOURS:
    grouped = df.groupby("station_id")["pm25"]
    df[f"pm25_roll_mean_{window}h"] = grouped.transform(lambda s: s.rolling(window, min_periods=max(3, window // 4)).mean())
    df[f"pm25_roll_max_{window}h"] = grouped.transform(lambda s: s.rolling(window, min_periods=max(3, window // 4)).max())
    df[f"pm25_roll_std_{window}h"] = grouped.transform(lambda s: s.rolling(window, min_periods=max(3, window // 4)).std())

target_lookup = df[["station_id", "datetime", "pm25"]].rename(
    columns={"datetime": "target_datetime", "pm25": "target_pm25"}
)
supervised = df.merge(target_lookup, on=["station_id", "target_datetime"], how="left")

spatial = df.groupby("datetime")["pm25"].agg(["sum", "count", "mean", "max"]).reset_index()
spatial = spatial.rename(columns={
    "sum": "spatial_pm25_sum",
    "count": "spatial_station_count",
    "mean": "spatial_pm25_mean",
    "max": "spatial_pm25_max",
})
supervised = supervised.merge(spatial, on="datetime", how="left")
supervised["other_station_pm25_mean"] = (
    (supervised["spatial_pm25_sum"] - supervised["pm25_lag_0h"])
    / (supervised["spatial_station_count"] - 1).replace(0, np.nan)
)
supervised["pm25_vs_spatial_mean"] = supervised["pm25_lag_0h"] - supervised["spatial_pm25_mean"]

feature_ready = supervised.dropna(subset=["pm25_lag_0h"]).copy()
feature_ready = feature_ready.sort_values(["datetime", "station_id"]).reset_index(drop=True)

supervised = feature_ready.dropna(subset=["target_pm25"]).copy()
supervised = supervised.sort_values(["datetime", "station_id"]).reset_index(drop=True)

print("Supervised rows:", len(supervised))
print("Date range:", supervised["datetime"].min(), "to", supervised["datetime"].max())
print("Feature-ready latest origin time:", feature_ready["datetime"].max())
display(supervised.head())
`),

  code(`
# =========================
# 4. Chronological split and feature lists
# =========================

candidate_features = [
    "station_id",
    "province",
    "latitude",
    "longitude",
    "pm10",
    "o3",
    "co",
    "no2",
    "so2",
    "wind_speed",
    "temperature",
    "relative_humidity",
    "pressure",
    "precipitation",
    "wind_dir_sin",
    "wind_dir_cos",
    "hour_sin",
    "hour_cos",
    "doy_sin",
    "doy_cos",
    "month_sin",
    "month_cos",
    "spatial_pm25_mean",
    "spatial_pm25_max",
    "other_station_pm25_mean",
    "pm25_vs_spatial_mean",
]
candidate_features += [f"pm25_lag_{lag}h" for lag in LAGS_HOURS]
for window in ROLLING_WINDOWS_HOURS:
    candidate_features += [
        f"pm25_roll_mean_{window}h",
        f"pm25_roll_max_{window}h",
        f"pm25_roll_std_{window}h",
    ]
candidate_features += FIRE_FEATURE_COLUMNS

feature_cols = [col for col in candidate_features if col in supervised.columns]
cat_cols = ["station_id", "province"]
cat_cols = [col for col in cat_cols if col in feature_cols]
num_cols = [col for col in feature_cols if col not in cat_cols]

unique_times = np.array(sorted(supervised["datetime"].drop_duplicates()))
train_cut = unique_times[int(len(unique_times) * TRAIN_RATIO)]
val_cut = unique_times[int(len(unique_times) * (TRAIN_RATIO + VAL_RATIO))]

train_df = supervised[supervised["datetime"] < train_cut].copy()
val_df = supervised[(supervised["datetime"] >= train_cut) & (supervised["datetime"] < val_cut)].copy()
test_df = supervised[supervised["datetime"] >= val_cut].copy()

X_train = train_df[feature_cols]
y_train = train_df["target_pm25"].astype("float32")
X_val = val_df[feature_cols]
y_val = val_df["target_pm25"].astype("float32")
X_test = test_df[feature_cols]
y_test = test_df["target_pm25"].astype("float32")

print("Features:", len(feature_cols))
print("Train/Val/Test rows:", len(train_df), len(val_df), len(test_df))
print("Train:", train_df["datetime"].min(), "to", train_df["datetime"].max())
print("Val:", val_df["datetime"].min(), "to", val_df["datetime"].max())
print("Test:", test_df["datetime"].min(), "to", test_df["datetime"].max())
display(pd.DataFrame({"feature": feature_cols}))
`),

  code(`
# =========================
# 5. Train candidate models
# =========================

def make_onehot():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)

linear_preprocess = ColumnTransformer(
    transformers=[
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), num_cols),
        ("cat", make_onehot(), cat_cols),
    ],
    remainder="drop",
)

tree_preprocess = ColumnTransformer(
    transformers=[
        ("num", SimpleImputer(strategy="median"), num_cols),
        ("cat", make_onehot(), cat_cols),
    ],
    remainder="drop",
)

candidate_models = {
    "Persistence_current_pm25": None,
    "Ridge_lag_rolling_spatial": Pipeline([
        ("preprocess", linear_preprocess),
        ("model", Ridge(alpha=10.0)),
    ]),
    "HistGradientBoosting_lag_rolling_spatial": Pipeline([
        ("preprocess", tree_preprocess),
        ("model", HistGradientBoostingRegressor(
            max_iter=450,
            learning_rate=0.035,
            l2_regularization=0.05,
            random_state=RANDOM_SEED,
        )),
    ]),
    "ExtraTrees_lag_rolling_spatial": Pipeline([
        ("preprocess", tree_preprocess),
        ("model", ExtraTreesRegressor(
            n_estimators=260,
            max_features=0.85,
            min_samples_leaf=2,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )),
    ]),
}

val_predictions = {}
test_predictions = {}
training_rows = []

for model_name, model in candidate_models.items():
    started = time.time()
    if model is None:
        val_pred = X_val["pm25_lag_0h"].to_numpy(dtype="float32")
        test_pred = X_test["pm25_lag_0h"].to_numpy(dtype="float32")
        artifact = ""
    else:
        model.fit(X_train, y_train)
        val_pred = np.clip(model.predict(X_val), 0, None).astype("float32")
        test_pred = np.clip(model.predict(X_test), 0, None).astype("float32")
        if SAVE_LARGE_MODEL_FILES or model_name != "ExtraTrees_lag_rolling_spatial":
            artifact = MODEL_DIR / f"{model_name}.pkl"
            joblib.dump(model, artifact)
        else:
            artifact = ""
    elapsed = time.time() - started
    val_predictions[model_name] = val_pred
    test_predictions[model_name] = test_pred
    training_rows.append({
        "model": model_name,
        "seconds": float(elapsed),
        "artifact": str(artifact),
    })
    print(f"Finished {model_name} in {elapsed:.1f}s")

def rmse(y_true, y_pred):
    return math.sqrt(mean_squared_error(y_true, y_pred))

val_rmse = {
    name: rmse(y_val, pred)
    for name, pred in val_predictions.items()
    if name != "Persistence_current_pm25"
}
top3 = sorted(val_rmse, key=val_rmse.get)[:3]
weights_raw = np.array([1 / max(val_rmse[name], 1e-6) for name in top3], dtype="float64")
weights = weights_raw / weights_raw.sum()

val_predictions["WeightedEnsemble_top3"] = np.sum(
    [val_predictions[name] * w for name, w in zip(top3, weights)],
    axis=0,
)
test_predictions["WeightedEnsemble_top3"] = np.sum(
    [test_predictions[name] * w for name, w in zip(top3, weights)],
    axis=0,
)
training_rows.append({
    "model": "WeightedEnsemble_top3",
    "seconds": 0.0,
    "artifact": "ensemble from " + ", ".join(top3),
})

training_log = pd.DataFrame(training_rows)
training_log.to_csv(OUTPUT_DIR / "model_training_log.csv", index=False)
pd.DataFrame({"model": top3, "weight": weights}).to_csv(OUTPUT_DIR / "ensemble_weights_top3.csv", index=False)
display(training_log)
display(pd.DataFrame({"model": top3, "weight": weights}))
`),

  code(`
# =========================
# 6. Train deep learning models with epochs
# =========================

if RUN_DEEP_LEARNING_MODELS:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers

    tf.keras.utils.set_random_seed(RANDOM_SEED)
    DL_DIR = OUTPUT_DIR / "deep_learning"
    DL_DIR.mkdir(parents=True, exist_ok=True)

    dl_feature_cols = [col for col in num_cols if col in supervised.columns]
    dl_train_mask = supervised["datetime"] < train_cut
    dl_imputer = SimpleImputer(strategy="median")
    dl_scaler = StandardScaler()
    dl_train_imputed = dl_imputer.fit_transform(supervised.loc[dl_train_mask, dl_feature_cols])
    dl_scaler.fit(dl_train_imputed)
    dl_all_features = dl_scaler.transform(
        dl_imputer.transform(supervised[dl_feature_cols])
    ).astype("float32")
    dl_row_pos = {idx: pos for pos, idx in enumerate(supervised.index)}

    X_seq, y_seq, seq_row_ids = [], [], []
    for station_id, group in supervised.sort_values(["station_id", "datetime"]).groupby("station_id"):
        row_ids = group.index.to_numpy()
        if len(row_ids) < DL_LOOKBACK_STEPS:
            continue
        for pos in range(DL_LOOKBACK_STEPS - 1, len(row_ids)):
            target_row_id = row_ids[pos]
            history_row_ids = row_ids[pos - DL_LOOKBACK_STEPS + 1:pos + 1]
            target_value = supervised.at[target_row_id, "target_pm25"]
            if not np.isfinite(target_value):
                continue
            X_seq.append(dl_all_features[[dl_row_pos[row_id] for row_id in history_row_ids]])
            y_seq.append(float(target_value))
            seq_row_ids.append(target_row_id)

    X_seq = np.asarray(X_seq, dtype="float32")
    y_seq = np.asarray(y_seq, dtype="float32").reshape(-1, 1)
    seq_row_ids = np.asarray(seq_row_ids)
    seq_times = supervised.loc[seq_row_ids, "datetime"].to_numpy()

    seq_train_mask = seq_times < np.datetime64(train_cut)
    seq_val_mask = (seq_times >= np.datetime64(train_cut)) & (seq_times < np.datetime64(val_cut))
    seq_test_mask = seq_times >= np.datetime64(val_cut)

    X_dl_train = X_seq[seq_train_mask]
    y_dl_train = y_seq[seq_train_mask]
    X_dl_val = X_seq[seq_val_mask]
    y_dl_val = y_seq[seq_val_mask]
    X_dl_test = X_seq[seq_test_mask]
    y_dl_test = y_seq[seq_test_mask]
    dl_test_row_ids = seq_row_ids[seq_test_mask]

    y_dl_scaler = StandardScaler()
    y_dl_train_s = y_dl_scaler.fit_transform(y_dl_train).astype("float32")
    y_dl_val_s = y_dl_scaler.transform(y_dl_val).astype("float32")

    print("Deep learning sequence shape:", X_seq.shape)
    print("DL train/val/test:", X_dl_train.shape, X_dl_val.shape, X_dl_test.shape)

    class TemporalAttention(layers.Layer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.score_dense = layers.Dense(1)

        def call(self, inputs):
            scores = self.score_dense(inputs)
            weights = tf.nn.softmax(scores, axis=1)
            return tf.reduce_sum(inputs * weights, axis=1)

    def build_dl_model(kind, input_shape, model_name):
        inputs = keras.Input(shape=input_shape)
        if kind == "lstm":
            x = layers.LSTM(72)(inputs)
        elif kind == "gru":
            x = layers.GRU(72)(inputs)
        elif kind == "bilstm":
            x = layers.Bidirectional(layers.LSTM(56))(inputs)
        elif kind == "cnn_lstm":
            x = layers.Conv1D(48, kernel_size=3, padding="causal", activation="relu")(inputs)
            x = layers.MaxPooling1D(pool_size=2)(x)
            x = layers.LSTM(64)(x)
        elif kind == "attention_bilstm":
            x = layers.Bidirectional(layers.LSTM(64, return_sequences=True))(inputs)
            x = layers.Dropout(0.20)(x)
            x = layers.Bidirectional(layers.LSTM(48, return_sequences=True))(x)
            x = TemporalAttention(name="temporal_attention")(x)
        else:
            raise ValueError(f"Unknown deep learning kind: {kind}")
        x = layers.Dense(96, activation="relu")(x)
        x = layers.Dropout(0.20)(x)
        outputs = layers.Dense(1, name="pm25_next_day")(x)
        model = keras.Model(inputs, outputs, name=model_name)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-3),
            loss="mse",
            metrics=[keras.metrics.MeanAbsoluteError(name="mae")],
        )
        return model

    dl_specs = [
        ("LSTM_sequence", "lstm"),
        ("GRU_sequence", "gru"),
        ("BiLSTM_sequence", "bilstm"),
        ("CNN_LSTM_sequence", "cnn_lstm"),
        ("Attention_BiLSTM_sequence", "attention_bilstm"),
    ]

    deep_learning_models = {}
    deep_history_frames = []
    epoch_rows = []
    test_position_by_index = {idx: pos for pos, idx in enumerate(test_df.index)}

    for model_name, kind in dl_specs:
        model = build_dl_model(kind, X_dl_train.shape[1:], model_name)
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=DL_PATIENCE,
                restore_best_weights=True,
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                patience=max(2, DL_PATIENCE // 2),
                factor=0.5,
                min_lr=1e-5,
            ),
        ]
        print("\\nTraining deep learning model:", model_name)
        started = time.time()
        history = model.fit(
            X_dl_train,
            y_dl_train_s,
            validation_data=(X_dl_val, y_dl_val_s),
            epochs=DL_EPOCHS,
            batch_size=DL_BATCH_SIZE,
            callbacks=callbacks,
            verbose=1,
        )
        elapsed = time.time() - started

        pred_s = model.predict(X_dl_test, verbose=0)
        pred = np.clip(y_dl_scaler.inverse_transform(pred_s).ravel(), 0, None).astype("float32")
        pred_full = np.full(len(test_df), np.nan, dtype="float32")
        for row_id, value in zip(dl_test_row_ids, pred):
            pos = test_position_by_index.get(row_id)
            if pos is not None:
                pred_full[pos] = value

        test_predictions[model_name] = pred_full
        deep_learning_models[model_name] = model

        history_df = pd.DataFrame(history.history)
        history_df["model"] = model_name
        history_df["epoch"] = np.arange(1, len(history_df) + 1)
        deep_history_frames.append(history_df)

        best_epoch_idx = int(history_df["val_loss"].idxmin())
        epoch_rows.append({
            "model": model_name,
            "epochs_run": int(len(history_df)),
            "max_epochs": int(DL_EPOCHS),
            "best_epoch": int(history_df.loc[best_epoch_idx, "epoch"]),
            "best_val_loss": float(history_df.loc[best_epoch_idx, "val_loss"]),
            "final_val_loss": float(history_df["val_loss"].iloc[-1]),
            "stopped_before_max_epoch": bool(len(history_df) < DL_EPOCHS),
            "seconds": float(elapsed),
        })

        artifact = DL_DIR / f"{model_name}.keras"
        try:
            model.save(artifact)
        except Exception as exc:
            artifact = DL_DIR / f"{model_name}.weights.h5"
            model.save_weights(artifact)
            print("Saved weights instead of full model for", model_name, "because:", exc)
        training_log = training_log[training_log["model"] != model_name].copy()
        training_log.loc[len(training_log)] = {
            "model": model_name,
            "seconds": float(elapsed),
            "artifact": str(artifact),
        }
        print(f"Finished {model_name}: epochs={len(history_df)}, best_epoch={epoch_rows[-1]['best_epoch']}")

    deep_learning_history = pd.concat(deep_history_frames, ignore_index=True)
    deep_learning_epoch_summary = pd.DataFrame(epoch_rows)
    deep_learning_history.to_csv(OUTPUT_DIR / "deep_learning_training_history.csv", index=False)
    deep_learning_epoch_summary.to_csv(OUTPUT_DIR / "deep_learning_epoch_summary.csv", index=False)
    training_log.to_csv(OUTPUT_DIR / "model_training_log.csv", index=False)

    fig, ax = plt.subplots(figsize=(11, 6))
    for model_name, group in deep_learning_history.groupby("model"):
        ax.plot(group["epoch"], group["val_loss"], linewidth=2, label=model_name)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Validation loss")
    ax.set_title("Deep Learning Validation Loss by Epoch")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    plt.tight_layout()
    dl_loss_fig = FIGURE_DIR / "deep_learning_loss_history.png"
    plt.savefig(dl_loss_fig, dpi=180, bbox_inches="tight")
    plt.show()

    display(deep_learning_epoch_summary)
else:
    print("Skipping deep learning models. Set RUN_DEEP_LEARNING_MODELS=True to enable.")
`),

  code(`
# =========================
# 7. Evaluate and compare models
# =========================

def regression_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype="float64")
    y_pred = np.asarray(y_pred, dtype="float64")
    valid_mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[valid_mask]
    y_pred = y_pred[valid_mask]
    if len(y_true) == 0:
        return {
            "rows_evaluated": 0,
            "mae": np.nan,
            "rmse": np.nan,
            "r2": np.nan,
            "bias_mean_error": np.nan,
            "median_abs_error": np.nan,
            "p90_abs_error": np.nan,
            "p95_abs_error": np.nan,
            **{f"within_{tol}ug_pct": np.nan for tol in ERROR_TOLERANCES},
        }
    errors = y_true - y_pred
    abs_errors = np.abs(errors)
    row = {
        "rows_evaluated": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(rmse(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "bias_mean_error": float(np.mean(errors)),
        "median_abs_error": float(np.median(abs_errors)),
        "p90_abs_error": float(np.percentile(abs_errors, 90)),
        "p95_abs_error": float(np.percentile(abs_errors, 95)),
    }
    for tol in ERROR_TOLERANCES:
        row[f"within_{tol}ug_pct"] = float(np.mean(abs_errors <= tol) * 100.0)
    return row

overall_rows = []
for model_name, pred in test_predictions.items():
    overall_rows.append({
        "model": model_name,
        "rows_total": int(len(y_test)),
        **regression_metrics(y_test, pred),
    })

model_comparison = (
    pd.DataFrame(overall_rows)
    .sort_values(["rmse", "mae"], ascending=[True, True])
    .reset_index(drop=True)
)
model_comparison["rank_by_rmse"] = np.arange(1, len(model_comparison) + 1)
model_comparison.to_csv(OUTPUT_DIR / "model_comparison_overall.csv", index=False)

station_rows = []
for model_name, pred in test_predictions.items():
    tmp = test_df[["station_id", "province", "datetime", "target_datetime", "target_pm25"]].copy()
    tmp["pred_pm25"] = pred
    tmp = tmp[np.isfinite(tmp["pred_pm25"])].copy()
    for (sid, province), group in tmp.groupby(["station_id", "province"]):
        station_rows.append({
            "model": model_name,
            "station_id": sid,
            "province": province,
            **regression_metrics(group["target_pm25"], group["pred_pm25"]),
        })

model_comparison_by_station = pd.DataFrame(station_rows)
model_comparison_by_station.to_csv(OUTPUT_DIR / "model_comparison_by_station.csv", index=False)

best_model_name = model_comparison.iloc[0]["model"]
best_model_summary = {
    "target": "next-day PM2.5 numeric forecasting",
    "horizon_hours": HORIZON_HOURS,
    "best_model": best_model_name,
    "selection_metric": "lowest RMSE on chronological test set",
    "metrics": model_comparison.iloc[0].to_dict(),
    "accuracy_note": "Percent accuracy is reported only as within an absolute error tolerance.",
}
with open(OUTPUT_DIR / "best_model_summary.json", "w", encoding="utf-8") as fh:
    json.dump(best_model_summary, fh, ensure_ascii=False, indent=2)

print("Best model:", best_model_name)
display(model_comparison)
display(model_comparison_by_station.sort_values(["model", "rmse"]).head(25))
`),

  code(`
# =========================
# 8. Save predictions and forecast-accuracy tables
# =========================

prediction_rows = []
for model_name, pred in test_predictions.items():
    tmp = test_df[["datetime", "target_datetime", "station_id", "province", "target_pm25"]].copy()
    tmp["model"] = model_name
    tmp["pred_pm25"] = pred
    tmp = tmp[np.isfinite(tmp["pred_pm25"])].copy()
    tmp["abs_error"] = (tmp["target_pm25"] - tmp["pred_pm25"]).abs()
    prediction_rows.append(tmp)
test_predictions_long = pd.concat(prediction_rows, ignore_index=True)
test_predictions_long.to_csv(OUTPUT_DIR / "test_predictions_long.csv", index=False)

accuracy_rows = []
for model_name, group in test_predictions_long.groupby("model"):
    for tol in ERROR_TOLERANCES:
        accuracy_rows.append({
            "model": model_name,
            "tolerance": f"+/-{tol} ug/m3",
            "tolerance_value": tol,
            "rows_evaluated": int(len(group)),
            "accuracy_pct": float((group["abs_error"] <= tol).mean() * 100.0),
        })
forecast_accuracy_by_tolerance = pd.DataFrame(accuracy_rows)
forecast_accuracy_by_tolerance.to_csv(OUTPUT_DIR / "forecast_accuracy_by_tolerance.csv", index=False)

display(test_predictions_long.head())
display(forecast_accuracy_by_tolerance)
`),

  code(`
# =========================
# 9. Visualize model comparison
# =========================

plt.style.use("default")

plot_df = model_comparison.sort_values("rmse", ascending=True)
fig, ax = plt.subplots(figsize=(11, 6))
ax.barh(plot_df["model"], plot_df["rmse"], color="#2563eb")
ax.set_xlabel("RMSE (ug/m3)")
ax.set_title("Next-Day PM2.5 Model Comparison by RMSE")
ax.grid(axis="x", alpha=0.25)
plt.tight_layout()
rmse_fig = FIGURE_DIR / "model_comparison_rmse.png"
plt.savefig(rmse_fig, dpi=180, bbox_inches="tight")
plt.show()

fig, ax = plt.subplots(figsize=(11, 6))
for model_name, group in forecast_accuracy_by_tolerance.groupby("model"):
    group = group.sort_values("tolerance_value")
    ax.plot(group["tolerance_value"], group["accuracy_pct"], marker="o", linewidth=2, label=model_name)
ax.axhline(95, color="#dc2626", linestyle="--", linewidth=2, label="95% target")
ax.set_xlabel("Allowed absolute error tolerance (+/- ug/m3)")
ax.set_ylabel("Forecast accuracy (%)")
ax.set_title("Forecast Accuracy by Error Tolerance")
ax.grid(True, alpha=0.25)
ax.legend(fontsize=8)
plt.tight_layout()
tol_fig = FIGURE_DIR / "forecast_accuracy_by_tolerance.png"
plt.savefig(tol_fig, dpi=180, bbox_inches="tight")
plt.show()

best_pred = test_predictions_long[test_predictions_long["model"] == best_model_name].copy()
sample_best = best_pred.sample(min(5000, len(best_pred)), random_state=RANDOM_SEED)
fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(sample_best["target_pm25"], sample_best["pred_pm25"], s=10, alpha=0.35, color="#0f766e")
limit = max(sample_best["target_pm25"].max(), sample_best["pred_pm25"].max())
ax.plot([0, limit], [0, limit], color="#111827", linestyle="--", linewidth=1.5)
ax.set_xlabel("True PM2.5")
ax.set_ylabel("Predicted PM2.5")
ax.set_title(f"True vs Predicted PM2.5 - {best_model_name}")
ax.grid(True, alpha=0.25)
plt.tight_layout()
scatter_fig = FIGURE_DIR / "best_model_true_vs_predicted.png"
plt.savefig(scatter_fig, dpi=180, bbox_inches="tight")
plt.show()

figures = sorted(str(p) for p in FIGURE_DIR.glob("*.png"))
pd.DataFrame({"figure": figures}).to_csv(FIGURE_DIR / "figure_index.csv", index=False)
print("Saved figures:")
for fig_path in figures:
    print("-", fig_path)
`),

  code(`
# =========================
# 10. Predict the next 24 hours from latest available row
# =========================

latest_time = feature_ready["datetime"].max()
latest_rows = feature_ready[feature_ready["datetime"] == latest_time].copy()

best_model = candidate_models.get(best_model_name)
if best_model_name == "WeightedEnsemble_top3":
    pred_latest = np.sum(
        [candidate_models[name].predict(latest_rows[feature_cols]) * w for name, w in zip(top3, weights)],
        axis=0,
    )
elif best_model_name == "Persistence_current_pm25":
    pred_latest = latest_rows["pm25_lag_0h"].to_numpy(dtype="float32")
elif "deep_learning_models" in globals() and best_model_name in deep_learning_models:
    dl_model = deep_learning_models[best_model_name]
    latest_pred_values = []
    for _, row in latest_rows.iterrows():
        station_history = (
            feature_ready[
                (feature_ready["station_id"] == row["station_id"])
                & (feature_ready["datetime"] <= row["datetime"])
            ]
            .sort_values("datetime")
            .tail(DL_LOOKBACK_STEPS)
        )
        if len(station_history) < DL_LOOKBACK_STEPS:
            latest_pred_values.append(np.nan)
            continue
        seq = dl_scaler.transform(
            dl_imputer.transform(station_history[dl_feature_cols])
        ).astype("float32")
        pred_s = dl_model.predict(seq.reshape(1, DL_LOOKBACK_STEPS, len(dl_feature_cols)), verbose=0)
        latest_pred_values.append(float(y_dl_scaler.inverse_transform(pred_s)[0, 0]))
    pred_latest = np.asarray(latest_pred_values, dtype="float32")
else:
    pred_latest = best_model.predict(latest_rows[feature_cols])

tomorrow_predictions = latest_rows[[
    "datetime",
    "target_datetime",
    "station_id",
    "province",
    "latitude",
    "longitude",
]].copy()
tomorrow_predictions["model"] = best_model_name
tomorrow_predictions["predicted_pm25_next_day"] = np.clip(pred_latest, 0, None)
tomorrow_predictions.to_csv(OUTPUT_DIR / "tomorrow_predictions.csv", index=False)

print("Latest origin time:", latest_time)
print("Prediction target time:", tomorrow_predictions["target_datetime"].iloc[0] if len(tomorrow_predictions) else None)
display(tomorrow_predictions)
`),

  code(`
# =========================
# 11. Export ZIP
# =========================

base_outputs = [
    "model_comparison_overall.csv",
    "model_comparison_by_station.csv",
    "forecast_accuracy_by_tolerance.csv",
    "test_predictions_long.csv",
    "tomorrow_predictions.csv",
    "best_model_summary.json",
    "figures/model_comparison_rmse.png",
    "figures/forecast_accuracy_by_tolerance.png",
    "figures/best_model_true_vs_predicted.png",
    "nasa_fire_feature_status.json",
    "nasa_firms_hotspots_prepared.csv",
    "nasa_fire_features_by_station_hour.csv",
    "figures/nasa_firms_hotspot_map.png",
]
if RUN_DEEP_LEARNING_MODELS:
    base_outputs += [
        "deep_learning_training_history.csv",
        "deep_learning_epoch_summary.csv",
        "figures/deep_learning_loss_history.png",
    ]

method_notes = {
    "task": "Next-day PM2.5 numeric forecasting",
    "horizon_hours": HORIZON_HOURS,
    "stations": stations[["station_id", "province", "latitude", "longitude"]].drop_duplicates().to_dict("records"),
    "feature_groups": {
        "lags_hours": LAGS_HOURS,
        "rolling_windows_hours": ROLLING_WINDOWS_HOURS,
        "spatial_features": ["spatial_pm25_mean", "spatial_pm25_max", "other_station_pm25_mean", "pm25_vs_spatial_mean"],
        "meteorology": [col for col in ["wind_speed", "temperature", "relative_humidity", "pressure", "precipitation"] if col in feature_cols],
        "nasa_firms_hotspot": [col for col in FIRE_FEATURE_COLUMNS if col in feature_cols],
    },
    "nasa_fire_feature_status": fire_feature_status if "fire_feature_status" in globals() else {"status": "not_run"},
    "models": list(test_predictions.keys()),
    "best_model": best_model_name,
    "outputs": base_outputs,
}
with open(OUTPUT_DIR / "method_notes.json", "w", encoding="utf-8") as fh:
    json.dump(method_notes, fh, ensure_ascii=False, indent=2)

zip_path = shutil.make_archive(
    "/content/pm25_nextday_clean_outputs_nasa",
    "zip",
    root_dir=str(OUTPUT_DIR),
)
print("ZIP created:", zip_path)

try:
    from google.colab import files
    files.download(zip_path)
except Exception as exc:
    print("Download manually from the Files panel:", zip_path)
    print("Download helper error:", exc)
`),
];

const notebook = {
  cells,
  metadata: {
    kernelspec: {
      display_name: "Python 3",
      language: "python",
      name: "python3",
    },
    language_info: {
      name: "python",
      pycodemirror_mode: { name: "ipython", version: 3 },
      version: "3.x",
    },
    colab: {
      name: "pm25_nextday_clean_colab.ipynb",
      provenance: [],
    },
  },
  nbformat: 4,
  nbformat_minor: 5,
};

fs.mkdirSync(path.dirname(notebookPath), { recursive: true });
fs.writeFileSync(notebookPath, JSON.stringify(notebook, null, 2), "utf8");
fs.copyFileSync(notebookPath, uploadPath);
fs.copyFileSync(notebookPath, nasaUploadPath);

console.log(`Created ${notebookPath}`);
console.log(`Created ${uploadPath}`);
console.log(`Created ${nasaUploadPath}`);
