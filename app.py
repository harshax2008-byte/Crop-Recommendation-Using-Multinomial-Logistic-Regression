import os
import json
import urllib.request
import streamlit as st
import sys
import base64
import streamlit.components.v1 as components

# Import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from predict import predict_crop, FEATURE_RANGES, CROP_METADATA
from data_loader import load_and_clean_data
from agri_data import INDIAN_STATES_DISTRICTS, INDIAN_REGIONS, STATE_COORDINATES, CROP_ECONOMICS, CROP_DATASET_PROFILES, calculate_farm_economics
import train_model

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
METRICS_PATH          = os.path.join(MODELS_DIR, "model_metrics.json")
CONFUSION_MATRIX_PATH = os.path.join(MODELS_DIR, "confusion_matrix.png")
DATA_DIR       = os.path.join(BASE_DIR, "data")
SOIL_DATA_PATH = os.path.join(DATA_DIR, "district_soil_data.json")
BG_IMG_PATH    = os.path.join(BASE_DIR, "assets", "bg.jpg")

# UI Config
st.set_page_config(
    page_title="AgroSense AI | Agricultural Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_b64 = get_b64(BG_IMG_PATH) if os.path.exists(BG_IMG_PATH) else ""

# Global CSS
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpeg;base64,{bg_b64}");
    background-size: cover;
    background-position: center center;
    background-attachment: fixed;
    font-family: 'Outfit', sans-serif;
}}

[data-testid="stHeader"]  {{ background: transparent !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: rgba(255,255,255,0.96) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(200,230,200,0.7) !important;
    border-radius: 20px !important;
    padding: 1.6rem 1.8rem !important;
    box-shadow: 0 8px 40px rgba(0,0,0,0.18) !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"] h1,
div[data-testid="stVerticalBlockBorderWrapper"] h2,
div[data-testid="stVerticalBlockBorderWrapper"] h3,
div[data-testid="stVerticalBlockBorderWrapper"] h4,
div[data-testid="stVerticalBlockBorderWrapper"] p,
div[data-testid="stVerticalBlockBorderWrapper"] span,
div[data-testid="stVerticalBlockBorderWrapper"] label,
div[data-testid="stVerticalBlockBorderWrapper"] div {{
    color: #111827 !important;
}}

[data-testid="stMetricValue"] {{ color: #15803d !important; font-weight: 800 !important; }}
[data-testid="stMetricLabel"] {{ color: #374151 !important; font-weight: 600 !important; }}

div.stButton > button {{
    background: linear-gradient(135deg, #16a34a, #15803d) !important;
    color: #fff !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 30px !important;
    padding: 0.75rem 2rem !important;
    box-shadow: 0 4px 20px rgba(22,163,74,0.45) !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    font-size: 1rem !important;
    font-family: 'Outfit', sans-serif !important;
}}
div.stButton > button:hover {{
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 30px rgba(22,163,74,0.6) !important;
}}

.flowing-banner {{
    background: linear-gradient(90deg, #14532d, #16a34a, #22c55e, #4ade80, #22c55e, #16a34a, #14532d);
    background-size: 400% 100%;
    animation: flowBg 8s linear infinite;
    padding: 0.9rem 0;
    border-radius: 0 0 24px 24px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.3);
    margin-bottom: 1.5rem;
    overflow: hidden;
    position: relative;
    z-index: 100;
}}
@keyframes flowBg {{
    0%   {{ background-position: 0% 50%; }}
    100% {{ background-position: 400% 50%; }}
}}
.flowing-banner marquee {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #fff !important;
    letter-spacing: 0.04em;
}}

.weather-badge {{
    background: rgba(255,255,255,0.97);
    padding: 1rem 1.4rem;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    border: 1px solid rgba(22,163,74,0.2);
}}

.main-title {{
    font-size: 4rem;
    font-weight: 800;
    color: #ffffff !important;
    text-shadow: 0 4px 20px rgba(0,0,0,0.6);
    line-height: 1.1;
    margin-bottom: 1rem;
}}
.sub-title {{
    font-size: 1.3rem;
    color: #f0fdf4 !important;
    text-shadow: 0 2px 12px rgba(0,0,0,0.5);
    max-width: 580px;
    margin-bottom: 2.5rem;
    line-height: 1.6;
}}

.result-card {{
    background: linear-gradient(135deg, #16a34a 0%, #14532d 100%);
    border-radius: 24px;
    padding: 2.5rem;
    box-shadow: 0 20px 50px rgba(0,0,0,0.3);
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.15);
}}

.nav-title {{
    font-size: 2rem;
    font-weight: 800;
    color: white !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.6);
    margin-bottom: 1rem;
}}

.section-h {{ font-size: 1.15rem; font-weight: 800; color: #111827 !important; margin-bottom: 0.2rem; }}
.section-cap {{ font-size: 0.82rem; color: #6b7280 !important; margin-bottom: 1rem; }}

.param-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.45rem 0.6rem;
    border-radius: 8px;
    margin-bottom: 0.35rem;
    font-size: 0.88rem;
    font-weight: 600;
    color: #111827 !important;
}}
.param-row.match   {{ background: rgba(22,163,74,0.1); }}
.param-row.nomatch {{ background: rgba(234,88,12,0.08); }}
.param-badge {{ font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.6rem; border-radius: 999px; }}
.match-badge   {{ background: #dcfce7; color: #15803d !important; }}
.nomatch-badge {{ background: #ffedd5; color: #c2410c !important; }}

.alt-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(22,163,74,0.1);
    border: 1.5px solid rgba(22,163,74,0.3);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    font-size: 0.88rem;
    font-weight: 700;
    color: #15803d !important;
    margin: 0.2rem 0.15rem;
}}

.ui-footer {{
    background: rgba(255,255,255,0.96);
    padding: 1.2rem 2rem;
    border-radius: 16px 16px 0 0;
    margin-top: 4rem;
    text-align: center;
    display: flex;
    justify-content: space-around;
    align-items: center;
    font-weight: 600;
    color: #374151;
    font-size: 0.95rem;
}}
</style>
""", unsafe_allow_html=True)

# Session State
for k, v in [("role", None), ("state", "Punjab"), ("district", "Ludhiana"),
              ("is_predicted", False), ("top_crop", "Wheat"),
              ("globe_lat", 20.5937), ("globe_lon", 78.9629), ("globe_alt", 1.8)]:
    if k not in st.session_state:
        st.session_state[k] = v

# Helpers
@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(lat, lon):
    try:
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
               f"precipitation,rain,weather_code,wind_speed_10m&timezone=auto")
        req = urllib.request.Request(url, headers={"User-Agent": "AgroSenseAI/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            return json.loads(resp.read().decode()).get("current", {})
    except Exception:
        return None

def load_soil_data():
    if os.path.exists(SOIL_DATA_PATH):
        with open(SOIL_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_soil_data(data):
    with open(SOIL_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def weather_desc(code):
    if code == 0:              return "Clear Sky",     "☀️"
    if code in (1, 2):         return "Partly Cloudy", "⛅"
    if code == 3:              return "Overcast",       "☁️"
    if 45 <= code <= 49:       return "Foggy",          "🌫️"
    if 51 <= code <= 57:       return "Drizzle",        "🌦️"
    if 61 <= code <= 67:       return "Rain",           "🌧️"
    if 71 <= code <= 77:       return "Snow",           "❄️"
    if 80 <= code <= 82:       return "Rain Showers",   "🌦️"
    if 95 <= code <= 99:       return "Thunderstorm",   "⛈️"
    return "Variable", "🌥️"

# Globe renderer
def render_globe(lat, lon, altitude, is_predicted, state_name):
    is_pred_js = "true" if is_predicted else "false"
    state_safe = state_name.replace("'", "\\'")
    rotate_speed = "0.1" if is_predicted else "0.3"

    html = (
        "<!DOCTYPE html><html><head>"
        "<style>html,body{margin:0;padding:0;background:transparent;overflow:hidden;width:100%;height:100%;}#g{width:100%;height:100%;}</style>"
        "<script src='https://unpkg.com/three@0.154.0/build/three.min.js'></script>"
        "<script src='https://unpkg.com/globe.gl@2.30.0/dist/globe.gl.min.js'></script>"
        "</head><body><div id='g'></div><script>"
        "(function(){"
        "var g=Globe({animateIn:false})"
        ".globeImageUrl('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')"
        ".bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')"
        ".backgroundColor('rgba(0,0,0,0)')"
        ".showAtmosphere(true)"
        ".atmosphereColor('lightskyblue')"
        ".atmosphereAltitude(0.22)"
        "(document.getElementById('g'));"
        "g.controls().autoRotate=true;"
        "g.controls().autoRotateSpeed=" + rotate_speed + ";"
        "g.controls().enableZoom=false;"
        "g.pointOfView({lat:" + str(lat) + ",lng:" + str(lon) + ",altitude:" + str(altitude) + "},2500);"
        "g.pointsData([{lat:" + str(lat) + ",lng:" + str(lon) + "}])"
        ".pointAltitude(0.03).pointColor(function(){return'#84cc16';}).pointRadius(0.4);"
        "if(" + is_pred_js + "){"
        "fetch('https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States')"
        ".then(function(r){return r.json();})"
        ".then(function(geo){"
        "g.polygonsData(geo.features)"
        ".polygonCapColor(function(d){"
        "return d.properties.NAME_1.toLowerCase()==='" + state_safe.lower() + "'"
        "?'rgba(132,204,22,0.35)':'rgba(0,0,0,0)';})"
        ".polygonSideColor(function(){return'rgba(0,0,0,0.04)';})"
        ".polygonStrokeColor(function(d){"
        "return d.properties.NAME_1.toLowerCase()==='" + state_safe.lower() + "'"
        "?'#84cc16':'rgba(255,255,255,0.08)';});"
        "}).catch(function(){});"
        "}"
        "})();"
        "</script></body></html>"
    )
    components.html(html, height=480, scrolling=False)


# ============================================================
# LOGIN PAGE
# ============================================================
def login_page():
    st.markdown("<h1 class='main-title'>Smart Farming for<br>Future Generations</h1>",
                unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Data-driven crop recommendations, live weather tracking,<br>and financial insights to empower every farmer.</p>",
                unsafe_allow_html=True)

    col1, col2, _ = st.columns([1, 1, 1.2])
    with col1:
        with st.container(border=True):
            st.markdown("### 👨‍🌾 Farmer Portal")
            st.caption("Personalized crop recommendations & economics.")
            f_user = st.text_input("Username", key="f_user", placeholder="farmer")
            f_pass = st.text_input("Password", type="password", key="f_pass", placeholder="farmer123")
            if st.button("Farmer Login", type="primary", use_container_width=True):
                if f_user == "farmer" and f_pass == "farmer123":
                    st.session_state.role = "farmer"
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with col2:
        with st.container(border=True):
            st.markdown("### 🔬 Meteorologist Console")
            st.caption("Manage soil datasets and retrain the ML model.")
            m_user = st.text_input("Username", key="m_user", placeholder="meteo")
            m_pass = st.text_input("Password", type="password", key="m_pass", placeholder="meteo123")
            if st.button("Meteorologist Login", type="primary", use_container_width=True):
                if m_user == "meteo" and m_pass == "meteo123":
                    st.session_state.role = "meteorologist"
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    st.markdown(
        '<div class="ui-footer">'
        '<div>🌾 Trusted by thousands of farmers across India</div>'
        '<div style="display:flex;gap:2rem;">'
        '<span>🌾 Agrovia</span><span>🚜 John Deere</span><span>🌱 Green Solutions</span>'
        '</div></div>',
        unsafe_allow_html=True
    )

if st.session_state.role is None:
    login_page()
    st.stop()

# ============================================================
# FARMER DASHBOARD
# ============================================================
if st.session_state.role == "farmer":

    # Banner — plain string, no f-string double-brace confusion
    _d = st.session_state.district
    _s = st.session_state.state
    _c = st.session_state.top_crop.upper()
    _b = ("✨  Best crop for " + _d + ", " + _s + " right now  →  " + _c +
          "  🌱  AgroSense AI · Live Weather + Soil Intelligence  ✨")

    st.markdown(
        '<div class="flowing-banner">'
        '<marquee scrollamount="9" behavior="scroll" direction="left">'
        + _b + '&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;' + _b +
        '</marquee></div>',
        unsafe_allow_html=True
    )

    # Nav
    c_nav1, c_nav2 = st.columns([8, 1])
    with c_nav1:
        st.markdown("<div class='nav-title'>🌾 AgroSense AI Dashboard</div>", unsafe_allow_html=True)
    with c_nav2:
        if st.button("Logout", use_container_width=True):
            st.session_state.role = None
            st.session_state.is_predicted = False
            st.session_state.top_crop = "Wheat"
            st.rerun()

    # Main 2-col layout
    col_globe, col_form = st.columns([1.6, 1], gap="large")

    with col_form:
        with st.container(border=True):
            st.markdown("### 🗺️ Geographic Intelligence")

            region    = st.selectbox("1. Select Region",   list(INDIAN_REGIONS.keys()))
            state     = st.selectbox("2. Select State",    INDIAN_REGIONS[region])
            districts = INDIAN_STATES_DISTRICTS.get(state, ["Central"])
            district  = st.selectbox("3. Select District", districts)

            if state != st.session_state.state or district != st.session_state.district:
                st.session_state.state        = state
                st.session_state.district     = district
                st.session_state.is_predicted = False
                coords = STATE_COORDINATES.get(state, {"lat": 20.59, "lon": 78.96})
                st.session_state.globe_lat = coords["lat"]
                st.session_state.globe_lon = coords["lon"]
                st.session_state.globe_alt = 1.2
                st.rerun()

            st.markdown("### 🚜 Farm Scale & Economics")
            farm_size = st.number_input("Farm Size (Acres)", 0.25, 500.0, 2.5, step=0.25)
            budget    = st.number_input("Investment Capital (₹)", 5000, 50_000_000, 60000, step=5000)
            method    = st.radio("Cultivation Method", ["Regular", "Organic"], horizontal=True)

            st.write("")
            predict_btn = st.button("🚀 Analyze & Predict Crop", type="primary", use_container_width=True)

    if predict_btn:
        st.session_state.is_predicted = True
        coords = STATE_COORDINATES.get(st.session_state.state, {"lat": 20.59, "lon": 78.96})
        st.session_state.globe_lat = coords["lat"]
        st.session_state.globe_lon = coords["lon"]
        st.session_state.globe_alt = 0.08  # zoom in tight

    # Resolve from session (consistent after rerun)
    state    = st.session_state.state
    district = st.session_state.district

    with col_globe:
        coords  = STATE_COORDINATES.get(state, {"lat": 20.5937, "lon": 78.9629})
        weather = fetch_weather(coords["lat"], coords["lon"])

        wc   = weather.get("weather_code", 0)           if weather else 0
        temp = weather.get("temperature_2m", 25.0)      if weather else 25.0
        hum  = weather.get("relative_humidity_2m", 70.0) if weather else 70.0

        if weather:
            cond_str, cond_emoji = weather_desc(wc)
            app_temp = weather.get("apparent_temperature", temp)
            precip   = weather.get("precipitation", 0)
            wind     = weather.get("wind_speed_10m", 0)

            badge = (
                '<div class="weather-badge">'
                '<div>'
                '<div style="font-size:0.78rem;color:#6b7280;font-weight:700;text-transform:uppercase;letter-spacing:1px;">'
                '🛰️ Live Climate · ' + state +
                '</div>'
                '<div style="font-size:1.8rem;font-weight:800;color:#111827;">' +
                str(temp) + '°C'
                '<span style="font-size:1rem;font-weight:600;color:#6b7280;"> Feels ' + str(app_temp) + '°C</span>'
                '</div>'
                '<div style="font-size:0.85rem;color:#6b7280;font-weight:600;">'
                '💨 ' + str(wind) + ' km/h &nbsp;|&nbsp; 🌧️ ' + str(precip) + 'mm'
                '</div></div>'
                '<div style="text-align:right;">'
                '<div style="font-size:2.2rem;">' + cond_emoji + '</div>'
                '<div style="font-size:1rem;font-weight:700;color:#111827;">' + cond_str + '</div>'
                '<div style="font-size:0.85rem;color:#6b7280;font-weight:600;">Humidity ' + str(hum) + '%</div>'
                '</div></div>'
            )
            st.markdown(badge, unsafe_allow_html=True)

        # Globe ALWAYS rendered
        render_globe(
            lat=st.session_state.globe_lat,
            lon=st.session_state.globe_lon,
            altitude=st.session_state.globe_alt,
            is_predicted=st.session_state.is_predicted,
            state_name=state
        )

    # ── Prediction Results ──────────────────────────────────────────────────
    if st.session_state.is_predicted:
        st.markdown("---")

        soil_db   = load_soil_data()
        d_profile = soil_db.get(state, {}).get(district)

        if not d_profile:
            st.warning("⚠️ No precise soil data for **" + district + ", " + state + "**. Using regional baseline.")
            d_profile = {"n": 50, "p": 50, "k": 50, "ph": 6.5,
                         "temperature": 25, "humidity": 70, "rainfall": 100}

        n, p, k, ph = d_profile["n"], d_profile["p"], d_profile["k"], d_profile["ph"]
        p_temp = round(float(temp), 1)
        p_hum  = round(float(hum), 1)
        p_rain = d_profile.get("rainfall", 100)

        with st.container(border=True):
            st.markdown(
                "✅ **Live Feature Vector** — "
                "N:" + str(n) + " | P:" + str(p) + " | K:" + str(k) +
                " | pH:" + str(ph) + " | Temp:" + str(p_temp) +
                "°C | Hum:" + str(p_hum) + "% | Rain:" + str(p_rain) + "mm"
            )

        with st.spinner("Running Agronomic ML Pipeline…"):
            try:
                res = predict_crop(n, p, k, p_temp, p_hum, ph, p_rain, top_n=5)

                top_crop = top_crop_disp = conf = meta = eco = None
                for cand in res["top_candidates"]:
                    c_eco = calculate_farm_economics(cand["crop"], farm_size, budget, state, method)
                    if c_eco["is_sufficient"]:
                        top_crop      = cand["crop"]
                        top_crop_disp = cand["crop_display"]
                        conf          = cand["confidence_pct"]
                        meta          = cand["metadata"]
                        eco           = c_eco
                        break

                if top_crop is None:
                    top_crop      = res["recommended_crop"]
                    top_crop_disp = res["recommended_crop_display"]
                    conf          = res["confidence_pct"]
                    meta          = res["metadata"]
                    eco           = calculate_farm_economics(top_crop, farm_size, budget, state, method)

                st.session_state.top_crop = top_crop_disp

                # Result card — built with plain concatenation to avoid any markdown/indentation issues
                emoji      = meta.get("emoji", "🌱")
                scientific = meta.get("scientific", "")
                category   = meta.get("category", "")
                desc       = meta.get("desc", "")

                st.markdown(
                    '<div class="result-card">'
                    '<div style="font-size:0.8rem;letter-spacing:2px;text-transform:uppercase;color:#bbf7d0;font-weight:700;margin-bottom:0.3rem;">🏆 Primary Recommendation</div>'
                    '<div style="font-size:3.2rem;font-weight:900;color:white;line-height:1;margin-bottom:0.2rem;">' + emoji + ' ' + top_crop_disp + '</div>'
                    '<div style="font-size:1.1rem;color:#dcfce7;font-style:italic;margin-bottom:1.2rem;">' + scientific + ' &bull; ' + category + '</div>'
                    '<div style="display:inline-block;background:rgba(255,255,255,0.18);border:2px solid rgba(255,255,255,0.4);padding:0.5rem 1.2rem;border-radius:999px;font-weight:800;font-size:1rem;color:white;margin-bottom:1.2rem;">🎯 Model Confidence: ' + str(conf) + '%</div>'
                    '<div style="font-size:1rem;line-height:1.7;color:#f0fdf4;max-width:820px;">' + desc + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

                col_eco, col_why = st.columns([1, 1], gap="large")

                with col_eco:
                    with st.container(border=True):
                        st.markdown(
                            '<div class="section-h">💰 Farm Economics & Yield</div>'
                            '<div class="section-cap">Based on ' + str(farm_size) + ' acres in ' + state + ' · ' + method + ' farming</div>',
                            unsafe_allow_html=True
                        )
                        st.metric("Estimated Investment", "₹{:,.0f}".format(eco['total_estimated_investment']))
                        r1, r2 = st.columns(2)
                        r1.metric("Expected Revenue", "₹{:,.0f}".format(eco['estimated_revenue']))
                        r2.metric("Projected Profit", "₹{:,.0f}".format(eco['estimated_profit']))

                        if eco["is_sufficient"]:
                            st.success("✅ Sufficient Capital (Surplus ₹{:,.0f})".format(eco['budget_difference']))
                        else:
                            st.error("⚠️ Capital Shortfall (Deficit ₹{:,.0f})".format(abs(eco['budget_difference'])))

                        st.markdown("**🌿 Viable Alternatives**")
                        alts = [c for c in res["top_candidates"] if c["crop"] != top_crop][:3]
                        pills = ""
                        for a in alts:
                            pills += ('<span class="alt-pill">🌾 ' + a["crop_display"] +
                                      ' <span style="font-size:0.78rem;opacity:0.7;">' + str(a["confidence_pct"]) + '%</span></span>')
                        st.markdown(pills, unsafe_allow_html=True)

                with col_why:
                    with st.container(border=True):
                        st.markdown(
                            '<div class="section-h">🧬 Why This Crop?</div>'
                            '<div class="section-cap">Your field fingerprint vs. optimal dataset range</div>',
                            unsafe_allow_html=True
                        )

                        profile = CROP_DATASET_PROFILES.get(top_crop.lower(), {})
                        param_list = [
                            ("🧪 Nitrogen (N)",   n,      profile.get("N")),
                            ("🧪 Phosphorus (P)", p,      profile.get("P")),
                            ("🧪 Potassium (K)",  k,      profile.get("K")),
                            ("🌡️ Temperature",    p_temp, profile.get("temperature")),
                            ("💧 Humidity",       p_hum,  profile.get("humidity")),
                            ("⚗️ Soil pH",        ph,     profile.get("ph")),
                            ("🌧️ Rainfall (mm)",  p_rain, profile.get("rainfall")),
                        ]

                        within = 0
                        rows_html = ""
                        for name, val, rng in param_list:
                            if rng:
                                lo, hi = rng
                                ok = lo <= val <= hi
                                if ok:
                                    within += 1
                                css_row   = "match"   if ok else "nomatch"
                                css_badge = "match-badge" if ok else "nomatch-badge"
                                badge_txt = ("✅ " + str(lo) + "–" + str(hi)) if ok else ("⚠️ Opt: " + str(lo) + "–" + str(hi))
                                rows_html += (
                                    '<div class="param-row ' + css_row + '">'
                                    '<span>' + name + ': <strong>' + str(val) + '</strong></span>'
                                    '<span class="param-badge ' + css_badge + '">' + badge_txt + '</span>'
                                    '</div>'
                                )
                            else:
                                within += 1
                                rows_html += (
                                    '<div class="param-row match">'
                                    '<span>' + name + ': <strong>' + str(val) + '</strong></span>'
                                    '<span class="param-badge match-badge">✅ OK</span>'
                                    '</div>'
                                )

                        st.markdown(rows_html, unsafe_allow_html=True)
                        st.info("**" + str(within) + " / 7** parameters align with the optimal range for **" + top_crop_disp + "**.")

                        if eco.get("is_prime_state"):
                            st.success("🌟 **" + state + "** is historically a prime region for " + top_crop_disp + ".")
                        else:
                            st.warning("⚠️ " + state + " may not be a traditional producer — but soil & climate indicate suitability.")

            except Exception as e:
                st.error("Inference Error: " + str(e))


# ============================================================
# METEOROLOGIST DASHBOARD
# ============================================================
elif st.session_state.role == "meteorologist":
    c_nav1, c_nav2 = st.columns([8, 1])
    with c_nav1:
        st.markdown("<div class='nav-title'>🔬 Meteorologist Console</div>", unsafe_allow_html=True)
    with c_nav2:
        if st.button("Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    with st.container(border=True):
        tab1, tab2, tab3 = st.tabs(["📝 District Soil Editor", "⚙️ Model Retraining", "📊 Performance Metrics"])

        with tab1:
            st.markdown("### Modify District Soil Profiles")
            st.caption("Saved instantly to the JSON dataset and reflected in farmer predictions.")

            m_state    = st.selectbox("State",    list(INDIAN_STATES_DISTRICTS.keys()), key="m_state")
            m_district = st.selectbox("District", INDIAN_STATES_DISTRICTS[m_state],     key="m_district")

            soil_db = load_soil_data()
            curr    = soil_db.get(m_state, {}).get(m_district,
                        {"n": 50, "p": 50, "k": 50, "ph": 6.5,
                         "temperature": 25.0, "humidity": 70.0, "rainfall": 100.0})

            c1, c2, c3 = st.columns(3)
            new_n = c1.number_input("Nitrogen (N)",   0,   150, int(curr.get("n", 50)))
            new_p = c2.number_input("Phosphorus (P)", 0,   150, int(curr.get("p", 50)))
            new_k = c3.number_input("Potassium (K)",  0,   210, int(curr.get("k", 50)))

            c4, c5, c6, c7 = st.columns(4)
            new_ph   = c4.number_input("pH",             3.5,  10.0, float(curr.get("ph",          6.5)), step=0.1)
            new_temp = c5.number_input("Temperature °C", 0.0,  55.0, float(curr.get("temperature", 25.0)), step=0.5)
            new_hum  = c6.number_input("Humidity %",     5.0, 100.0, float(curr.get("humidity",    70.0)), step=1.0)
            new_rain = c7.number_input("Rainfall mm",   10.0, 350.0, float(curr.get("rainfall",   100.0)), step=5.0)

            if st.button("💾 Save Profile", type="primary"):
                soil_db.setdefault(m_state, {})[m_district] = {
                    "n": new_n, "p": new_p, "k": new_k, "ph": new_ph,
                    "temperature": new_temp, "humidity": new_hum, "rainfall": new_rain
                }
                save_soil_data(soil_db)
                st.success("✅ Profile for **" + m_district + ", " + m_state + "** saved.")

        with tab2:
            st.markdown("### Retrain ML Pipeline")
            st.warning("⚠️ Retraining overwrites the existing model files.")
            data = load_and_clean_data()
            st.success("✅ Dataset: " + str(len(data)) + " records | " + str(data['label'].nunique()) + " crop classes")
            st.dataframe(data.head(), use_container_width=True)

            if st.button("🚀 Start Retraining", type="primary"):
                with st.spinner("Training…"):
                    metrics = train_model.train_and_evaluate()
                    import importlib
                    import predict as _predict
                    importlib.reload(_predict)
                    st.success("✅ Model retrained & saved.")
                    st.json(metrics)

        with tab3:
            st.markdown("### Model Evaluation Metrics")
            if os.path.exists(METRICS_PATH):
                with open(METRICS_PATH) as f:
                    metrics = json.load(f)
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Accuracy",  "{:.2f}%".format(metrics.get('accuracy', 0)*100))
                mc2.metric("Precision", "{:.2f}%".format(metrics.get('precision_weighted', 0)*100))
                mc3.metric("Recall",    "{:.2f}%".format(metrics.get('recall_weighted', 0)*100))
                mc4.metric("F1 Score",  "{:.2f}%".format(metrics.get('f1_score_weighted', 0)*100))
                if os.path.exists(CONFUSION_MATRIX_PATH):
                    st.image(CONFUSION_MATRIX_PATH, caption="Confusion Matrix", use_container_width=True)
            else:
                st.info("No metrics found. Please retrain the model first.")
