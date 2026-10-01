"""
AgroSense AI - FastAPI REST Backend v4.0
Role-based login (Farmer / Meteorologist), district soil data CRUD,
ML inference + economics, live weather (Open-Meteo), static frontend.
"""

import os
import sys
import json
import base64
import uuid
import time
import threading
from pathlib import Path
from typing import Optional, Dict

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "src"))

from predict import predict_crop, FEATURE_RANGES, CROP_METADATA
from agri_data import (
    INDIAN_STATES_DISTRICTS, INDIAN_REGIONS, STATE_COORDINATES,
    CROP_ECONOMICS, CROP_DATASET_PROFILES,
    calculate_farm_economics
)

MODELS_DIR = BASE_DIR / "models"
METRICS_PATH = MODELS_DIR / "model_metrics.json"
CONFUSION_MATRIX_PATH = MODELS_DIR / "confusion_matrix.png"
FRONTEND_DIR = BASE_DIR / "frontend"
SOIL_DATA_PATH = BASE_DIR / "data" / "district_soil_data.json"

app = FastAPI(title="AgroSense AI API", version="4.0.0")

USERS = {
    "farmer":  {"password": "farmer123",  "role": "farmer",        "name": "Farmer User"},
    "meteo":   {"password": "meteo123",   "role": "meteorologist", "name": "Meteorologist"},
}
_tokens: Dict[str, dict] = {}
_tokens_lock = threading.Lock()


def create_token(username, role, name):
    token = uuid.uuid4().hex
    with _tokens_lock:
        _tokens[token] = {"username": username, "role": role, "name": name}
    return token

def get_session(token):
    with _tokens_lock:
        return _tokens.get(token)

def remove_token(token):
    with _tokens_lock:
        _tokens.pop(token, None)

_soil_lock = threading.Lock()

def load_soil_data():
    with _soil_lock:
        if SOIL_DATA_PATH.exists():
            with open(SOIL_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}

def save_soil_data(data):
    with _soil_lock:
        with open(SOIL_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

_weather_cache: Dict[str, dict] = {}
_weather_lock = threading.Lock()
WEATHER_TTL = 600

def get_cached_weather(key):
    with _weather_lock:
        e = _weather_cache.get(key)
        if e and (time.time() - e["ts"]) < WEATHER_TTL:
            return e["data"]
    return None

def set_cached_weather(key, data):
    with _weather_lock:
        _weather_cache[key] = {"data": data, "ts": time.time()}


class LoginRequest(BaseModel):
    username: str
    password: str

class PredictRequest(BaseModel):
    n: float = Field(..., ge=0, le=150)
    p: float = Field(..., ge=0, le=150)
    k: float = Field(..., ge=0, le=210)
    temperature: float = Field(..., ge=0, le=55)
    humidity: float = Field(..., ge=5, le=100)
    ph: float = Field(..., ge=3.5, le=10.0)
    rainfall: float = Field(..., ge=10, le=350)
    farm_acres: float = Field(default=2.5, ge=0.25, le=500)
    user_budget: float = Field(default=60000.0, ge=5000)
    state: str = Field(default="Punjab")
    district: str = Field(default="Ludhiana")
    farming_method: str = Field(default="regular")

class SoilUpdateRequest(BaseModel):
    state: str
    district: str
    n: float = Field(..., ge=0, le=150)
    p: float = Field(..., ge=0, le=150)
    k: float = Field(..., ge=0, le=210)
    ph: float = Field(..., ge=3.5, le=10.0)
    temperature: float = Field(..., ge=0, le=55)
    humidity: float = Field(..., ge=5, le=100)
    rainfall: float = Field(..., ge=10, le=350)


@app.post("/api/login")
def login(req: LoginRequest):
    user = USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_token(req.username, user["role"], user["name"])
    return JSONResponse({"token": token, "role": user["role"], "name": user["name"], "username": req.username})

@app.post("/api/logout")
def logout(authorization: str = Header(default="")):
    token = authorization.split()[-1] if authorization else ""
    remove_token(token)
    return {"status": "ok"}

@app.get("/api/soil-data")
def get_soil_data(state: str, district: str):
    data = load_soil_data()
    district_data = data.get(state, {}).get(district)
    if not district_data:
        return JSONResponse({
            "found": False,
            "data": {"n": 50, "p": 50, "k": 50, "ph": 6.5, "temperature": 25, "humidity": 70, "rainfall": 100},
            "message": f"No specific data for {district}, {state}."
        })
    return JSONResponse({"found": True, "data": district_data, "message": f"Soil data for {district}, {state}"})

@app.put("/api/soil-data")
def update_soil_data(req: SoilUpdateRequest, authorization: str = Header(default="")):
    token = authorization.split()[-1] if authorization else ""
    session = get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Authentication required")
    if session["role"] != "meteorologist":
        raise HTTPException(status_code=403, detail="Only meteorologists can update soil data")
    data = load_soil_data()
    if req.state not in data:
        data[req.state] = {}
    data[req.state][req.district] = {
        "n": req.n, "p": req.p, "k": req.k, "ph": req.ph,
        "temperature": req.temperature, "humidity": req.humidity, "rainfall": req.rainfall
    }
    save_soil_data(data)
    return JSONResponse({"status": "ok", "message": f"Updated {req.district}, {req.state}", "data": data[req.state][req.district]})


@app.get("/api/weather")
def get_weather(lat: float, lon: float):
    import urllib.request
    cache_key = f"{round(lat,2)}_{round(lon,2)}"
    cached = get_cached_weather(cache_key)
    if cached:
        return JSONResponse({**cached, "cached": True})
    params = (
        f"latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        "precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m"
        "&timezone=auto&forecast_days=1"
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    try:
        req_obj = urllib.request.Request(url, headers={"User-Agent": "AgroSenseAI/4.0"})
        with urllib.request.urlopen(req_obj, timeout=8) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return JSONResponse({"available": False, "error": str(exc), "message": "Live climate data unavailable"})

    curr = raw.get("current", {})
    wc = curr.get("weather_code", 0)

    def decode_wmo(code):
        if code == 0: return "Clear Sky", "clear"
        if code in (1, 2): return "Partly Cloudy", "partly_cloudy"
        if code == 3: return "Overcast", "overcast"
        if 45 <= code <= 49: return "Foggy", "fog"
        if 51 <= code <= 57: return "Drizzle", "drizzle"
        if 61 <= code <= 67: return "Rain", "rain"
        if 71 <= code <= 77: return "Snow", "snow"
        if 80 <= code <= 82: return "Rain Showers", "rain"
        if 95 <= code <= 99: return "Thunderstorm", "storm"
        return "Variable", "overcast"

    cond, code_str = decode_wmo(wc)
    result = {
        "available": True,
        "temperature": curr.get("temperature_2m"),
        "feels_like": curr.get("apparent_temperature"),
        "humidity": curr.get("relative_humidity_2m"),
        "precipitation": curr.get("precipitation", 0),
        "rain": curr.get("rain", 0),
        "wind_speed": curr.get("wind_speed_10m"),
        "wind_direction": curr.get("wind_direction_10m"),
        "weather_code": wc,
        "condition": cond,
        "condition_code": code_str,
        "cached": False
    }
    set_cached_weather(cache_key, result)
    return JSONResponse(result)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AgroSense AI", "version": "4.0.0"}


@app.get("/api/metadata")
def metadata():
    metrics = None
    if METRICS_PATH.exists():
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)

    presets = {
        "Rice / Paddy Farm (West Bengal)": {"state": "West Bengal", "district": "Purba Bardhaman", "acres": 3.0, "budget": 65000.0, "n": 90.0, "p": 42.0, "k": 43.0, "temp": 21.0, "hum": 82.5, "ph": 6.5, "rain": 205.0},
        "High-Altitude Coffee (Karnataka)": {"state": "Karnataka", "district": "Hassan", "acres": 4.0, "budget": 150000.0, "n": 101.0, "p": 28.0, "k": 32.0, "temp": 26.5, "hum": 58.8, "ph": 6.7, "rain": 158.4},
        "Bt Cotton Cash Crop (Gujarat)": {"state": "Gujarat", "district": "Rajkot", "acres": 5.0, "budget": 120000.0, "n": 118.0, "p": 46.0, "k": 19.0, "temp": 24.0, "hum": 79.8, "ph": 6.8, "rain": 90.7},
        "Rabi Chickpea (Madhya Pradesh)": {"state": "Madhya Pradesh", "district": "Sehore", "acres": 2.0, "budget": 35000.0, "n": 40.0, "p": 67.0, "k": 79.0, "temp": 17.0, "hum": 16.8, "ph": 7.3, "rain": 79.4},
        "Apple Orchard (Himachal Pradesh)": {"state": "Himachal Pradesh", "district": "Shimla", "acres": 1.5, "budget": 180000.0, "n": 20.0, "p": 134.0, "k": 199.0, "temp": 22.6, "hum": 92.8, "ph": 5.86, "rain": 112.6},
        "Hybrid Maize (Bihar)": {"state": "Bihar", "district": "Samastipur", "acres": 2.5, "budget": 45000.0, "n": 71.0, "p": 54.0, "k": 20.0, "temp": 22.6, "hum": 65.0, "ph": 6.0, "rain": 85.0},
        "Watermelon Riverbed (Uttar Pradesh)": {"state": "Uttar Pradesh", "district": "Varanasi", "acres": 1.5, "budget": 30000.0, "n": 100.0, "p": 18.0, "k": 50.0, "temp": 26.0, "hum": 88.0, "ph": 6.5, "rain": 50.0}
    }

    profiles_serializable = {}
    for k, v in CROP_DATASET_PROFILES.items():
        profiles_serializable[k] = {feat: list(rng) for feat, rng in v.items()}

    return JSONResponse({
        "states_districts": INDIAN_STATES_DISTRICTS,
        "regions": INDIAN_REGIONS,
        "state_coordinates": STATE_COORDINATES,
        "presets": presets,
        "crop_metadata": CROP_METADATA,
        "crop_profiles": profiles_serializable,
        "model_metrics": metrics,
        "feature_ranges": {k: {"min": v[0], "max": v[1], "description": v[2]} for k, v in FEATURE_RANGES.items()}
    })


@app.post("/api/predict")
def predict(req: PredictRequest):
    try:
        result = predict_crop(n=req.n, p=req.p, k=req.k, temperature=req.temperature, humidity=req.humidity, ph=req.ph, rainfall=req.rainfall, top_n=4)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ML inference error: {str(exc)}")

    top_crop = result["recommended_crop"]
    eco = calculate_farm_economics(crop_name=top_crop, farm_size_acres=req.farm_acres, user_budget_inr=req.user_budget, selected_state=req.state, farming_method=req.farming_method)

    enriched = []
    for c in result["top_candidates"]:
        ce = calculate_farm_economics(crop_name=c["crop"], farm_size_acres=req.farm_acres, user_budget_inr=req.user_budget, selected_state=req.state, farming_method=req.farming_method)
        enriched.append({**c, "economics": ce})

    crop_key = top_crop.lower()
    profile = CROP_DATASET_PROFILES.get(crop_key, {})
    inputs_map = {"N": req.n, "P": req.p, "K": req.k, "temperature": req.temperature, "humidity": req.humidity, "ph": req.ph, "rainfall": req.rainfall}
    why_analysis = []
    within_count = 0
    for feature, value in inputs_map.items():
        rng = profile.get(feature)
        if rng:
            lo, hi = rng
            within = lo <= value <= hi
            if within:
                within_count += 1
            span = max(hi - lo, 1)
            center = (lo + hi) / 2
            dist = abs(value - center) / (span / 2 + 0.001)
            if value < lo:
                alignment = max(0, 100 - int((lo - value) / span * 200))
                align_label = "Below Range"
            elif value > hi:
                alignment = max(0, 100 - int((value - hi) / span * 200))
                align_label = "Above Range"
            else:
                alignment = int((1 - min(1.0, dist)) * 70) + 30
                align_label = "Strong Match" if dist < 0.4 else "Within Range"
        else:
            within, alignment, align_label = True, 70, "Within Range"
            within_count += 1
        why_analysis.append({"feature": feature, "value": round(value, 2), "range_lo": rng[0] if rng else None, "range_hi": rng[1] if rng else None, "within_range": within, "alignment_pct": alignment, "alignment_label": align_label})

    return JSONResponse({
        "recommended_crop": result["recommended_crop"],
        "recommended_crop_display": result["recommended_crop_display"],
        "confidence_pct": result["confidence_pct"],
        "metadata": result["metadata"],
        "top_candidates": enriched,
        "economics": eco,
        "why_analysis": why_analysis,
        "within_range_count": within_count,
        "total_features": 7,
        "inputs": {"n": req.n, "p": req.p, "k": req.k, "temperature": req.temperature, "humidity": req.humidity, "ph": req.ph, "rainfall": req.rainfall, "farm_acres": req.farm_acres, "user_budget": req.user_budget, "state": req.state, "district": req.district, "farming_method": req.farming_method}
    })


@app.get("/api/confusion_matrix")
def confusion_matrix_image():
    if not CONFUSION_MATRIX_PATH.exists():
        raise HTTPException(status_code=404, detail="Confusion matrix not found.")
    with open(CONFUSION_MATRIX_PATH, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    return JSONResponse({"image_base64": img_b64, "mime": "image/png"})


@app.post("/api/retrain")
def retrain_model(authorization: str = Header(default="")):
    token = authorization.split()[-1] if authorization else ""
    session = get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Authentication required")
    if session["role"] != "meteorologist":
        raise HTTPException(status_code=403, detail="Only meteorologists can retrain the model")
    try:
        train_src = str(BASE_DIR / "src")
        if train_src not in sys.path:
            sys.path.insert(0, train_src)
        import predict as pred_module
        pred_module._pipeline_cache = None
        import importlib
        import train_model as tm
        importlib.reload(tm)
        metrics = tm.train_and_evaluate()
        pred_module._pipeline_cache = None
        return JSONResponse({"status": "ok", "message": "Model retrained successfully", "accuracy": metrics.get("accuracy"), "f1_score_weighted": metrics.get("f1_score_weighted"), "train_samples": metrics.get("train_samples"), "test_samples": metrics.get("test_samples")})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(exc)}")


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">\U0001f33e</text></svg>'
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
