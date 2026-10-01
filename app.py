import os
import json
import urllib.request
import streamlit as st
import sys
import base64

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from predict import predict_crop, FEATURE_RANGES, CROP_METADATA
from data_loader import load_and_clean_data
from agri_data import (INDIAN_STATES_DISTRICTS, INDIAN_REGIONS,
                       STATE_COORDINATES, CROP_ECONOMICS,
                       CROP_DATASET_PROFILES, calculate_farm_economics)
import train_model

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
METRICS_PATH          = os.path.join(MODELS_DIR, "model_metrics.json")
CONFUSION_MATRIX_PATH = os.path.join(MODELS_DIR, "confusion_matrix.png")
SOIL_DATA_PATH = os.path.join(BASE_DIR, "data", "district_soil_data.json")
BG_IMG_PATH    = os.path.join(BASE_DIR, "assets", "bg.jpg")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroSense AI",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_data(show_spinner=False)
def get_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_b64 = get_b64(BG_IMG_PATH) if os.path.exists(BG_IMG_PATH) else ""

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800;900&display=swap');

*,*::before,*::after{{box-sizing:border-box;}}

html, body, [data-testid="stAppViewContainer"] {{
    font-family:'Outfit',sans-serif;
    background-image: url("data:image/jpeg;base64,{bg_b64}");
    background-size:cover;
    background-position:center;
    background-attachment:fixed;
}}
[data-testid="stHeader"], [data-testid="stToolbar"]{{display:none!important;}}
footer, #MainMenu{{visibility:hidden;}}
[data-testid="stMain"] > div {{padding-top:0!important;}}

/* ── CARDS ── */
div[data-testid="stVerticalBlockBorderWrapper"]{{
    background:rgba(255,255,255,0.95)!important;
    backdrop-filter:blur(24px)!important;
    -webkit-backdrop-filter:blur(24px)!important;
    border:1.5px solid rgba(22,163,74,0.18)!important;
    border-radius:22px!important;
    padding:1.8rem!important;
    box-shadow:0 8px 48px rgba(0,0,0,0.22)!important;
}}

/* Force readable dark text inside all cards */
div[data-testid="stVerticalBlockBorderWrapper"] *:not(button):not(.st-emotion-cache-*){{
    color:#111827!important;
}}

/* ── METRICS ── */
[data-testid="stMetricValue"]{{color:#064e3b!important;font-weight:900!important;font-size:1.6rem!important;}}
[data-testid="stMetricLabel"]{{color:#374151!important;font-weight:600!important;font-size:0.82rem!important;letter-spacing:0.5px;text-transform:uppercase;}}
[data-testid="stMetricDelta"]{{color:#047857!important;}}

/* ── BUTTONS ── */
div.stButton>button{{
    background:linear-gradient(135deg,#16a34a,#166534)!important;
    color:#fff!important;
    font-weight:800!important;
    border:none!important;
    border-radius:32px!important;
    padding:0.8rem 2.2rem!important;
    box-shadow:0 4px 24px rgba(22,163,74,0.5)!important;
    transition:all 0.25s cubic-bezier(.4,0,.2,1)!important;
    font-size:1rem!important;
    font-family:'Outfit',sans-serif!important;
    letter-spacing:0.02em!important;
}}
div.stButton>button:hover{{
    transform:translateY(-3px)scale(1.02)!important;
    box-shadow:0 12px 32px rgba(22,163,74,0.65)!important;
}}
div.stButton>button:active{{transform:translateY(0)scale(0.99)!important;}}

/* ── SELECT / RADIO ── */
div.stSelectbox label, div.stRadio label, div.stNumberInput label{{
    color:#fff!important;
    font-weight:700!important;
    text-shadow:0 1px 6px rgba(0,0,0,0.6)!important;
    font-size:0.88rem!important;
    letter-spacing:0.3px;
}}
div[data-testid="stVerticalBlockBorderWrapper"] div.stSelectbox label,
div[data-testid="stVerticalBlockBorderWrapper"] div.stRadio label,
div[data-testid="stVerticalBlockBorderWrapper"] div.stNumberInput label{{
    color:#111827!important;
    text-shadow:none!important;
}}

/* ── BANNER ── */
.agro-banner{{
    background:linear-gradient(90deg,#052e16,#14532d,#15803d,#16a34a,#22c55e,#16a34a,#15803d,#14532d,#052e16);
    background-size:300% 100%;
    animation:bannerFlow 12s linear infinite;
    padding:0.85rem 0;
    border-radius:0 0 20px 20px;
    box-shadow:0 4px 20px rgba(0,0,0,0.35);
    overflow:hidden;
    margin-bottom:1.2rem;
}}
@keyframes bannerFlow{{from{{background-position:0%}}to{{background-position:300%}}}}
.agro-banner marquee{{
    font-family:'Outfit',sans-serif;
    font-size:1.05rem;
    font-weight:700;
    color:#fff!important;
    letter-spacing:0.06em;
}}

/* ── NAV ── */
.nav-title{{
    font-size:1.8rem;font-weight:900;
    color:#fff!important;
    text-shadow:0 2px 12px rgba(0,0,0,0.7);
    padding:0.4rem 0;
}}

/* ── LOGIN HERO ── */
.hero-title{{
    font-size:3.8rem;font-weight:900;line-height:1.05;
    color:#fff!important;
    text-shadow:0 4px 24px rgba(0,0,0,0.7);
    margin-bottom:0.8rem;
}}
.hero-sub{{
    font-size:1.2rem;color:#dcfce7!important;
    text-shadow:0 2px 12px rgba(0,0,0,0.6);
    max-width:540px;line-height:1.7;margin-bottom:2rem;
}}

/* ── WEATHER BADGE ── */
.wx-badge{{
    background:rgba(255,255,255,0.97);
    border:1.5px solid rgba(22,163,74,0.25);
    border-radius:18px;
    padding:1rem 1.4rem;
    box-shadow:0 4px 24px rgba(0,0,0,0.15);
    display:flex;justify-content:space-between;align-items:center;
    margin-bottom:0.8rem;
}}
.wx-badge *{{color:#111827!important;}}
.wx-label{{font-size:0.72rem;font-weight:800;text-transform:uppercase;letter-spacing:1.5px;color:#6b7280!important;}}
.wx-temp{{font-size:2rem;font-weight:900;color:#111827!important;line-height:1.1;}}
.wx-feels{{font-size:0.9rem;font-weight:600;color:#6b7280!important;}}
.wx-detail{{font-size:0.8rem;color:#9ca3af!important;font-weight:600;margin-top:0.2rem;}}
.wx-icon{{font-size:2.4rem;}}
.wx-cond{{font-size:0.95rem;font-weight:700;color:#111827!important;}}
.wx-hum{{font-size:0.8rem;color:#6b7280!important;font-weight:600;}}

/* ── RESULT CARD ── */
.result-card{{
    background:linear-gradient(135deg,#166534 0%,#14532d 40%,#052e16 100%);
    border:1px solid rgba(255,255,255,0.12);
    border-radius:24px;padding:2.5rem;
    box-shadow:0 24px 64px rgba(0,0,0,0.4);
    margin-bottom:1.5rem;position:relative;overflow:hidden;
}}
.result-card::before{{
    content:'';position:absolute;top:-60px;right:-60px;
    width:200px;height:200px;
    background:radial-gradient(circle,rgba(134,239,172,0.15),transparent 70%);
    pointer-events:none;
}}
.result-card .rc-pre{{font-size:0.7rem;letter-spacing:2.5px;text-transform:uppercase;color:#86efac;font-weight:800;margin-bottom:0.3rem;}}
.result-card .rc-name{{font-size:3rem;font-weight:900;color:#fff;line-height:1;margin-bottom:0.2rem;}}
.result-card .rc-sci{{font-size:1rem;color:#bbf7d0;font-style:italic;margin-bottom:1.2rem;}}
.result-card .rc-conf{{
    display:inline-flex;align-items:center;gap:0.5rem;
    background:rgba(255,255,255,0.15);
    border:1.5px solid rgba(255,255,255,0.3);
    padding:0.45rem 1.1rem;border-radius:999px;
    font-weight:800;font-size:0.95rem;color:#fff;margin-bottom:1.1rem;
}}
.result-card .rc-desc{{font-size:0.95rem;line-height:1.8;color:#dcfce7;max-width:800px;}}

/* ── SECTION HEADERS inside cards ── */
.sec-h{{font-size:1.1rem;font-weight:800;color:#111827!important;margin-bottom:0.15rem;}}
.sec-cap{{font-size:0.78rem;color:#6b7280!important;margin-bottom:1rem;font-weight:500;}}

/* ── PARAM ROWS ── */
.param-row{{
    display:flex;justify-content:space-between;align-items:center;
    padding:0.45rem 0.7rem;border-radius:10px;margin-bottom:0.3rem;
    font-size:0.85rem;font-weight:600;color:#111827!important;
}}
.pr-match{{background:rgba(22,163,74,0.1);border-left:3px solid #16a34a;}}
.pr-miss {{background:rgba(234,88,12,0.08);border-left:3px solid #ea580c;}}
.pbadge{{font-size:0.72rem;font-weight:800;padding:0.2rem 0.7rem;border-radius:999px;}}
.pb-m{{background:#dcfce7;color:#15803d!important;}}
.pb-x{{background:#ffedd5;color:#c2410c!important;}}

/* ── ALT PILL ── */
.alt-pill{{
    display:inline-flex;align-items:center;gap:0.4rem;
    background:rgba(22,163,74,0.15);border:1.5px solid rgba(22,163,74,0.3);
    border-radius:999px;padding:0.35rem 0.9rem;
    font-size:0.85rem;font-weight:800;color:#064e3b!important;
    margin:0.18rem 0.15rem;
}}

/* ── FEATURE VECTOR ROW ── */
.fv-row{{
    background:rgba(22,163,74,0.12);border:1px solid rgba(22,163,74,0.3);
    border-radius:14px;padding:0.85rem 1.2rem;
    font-size:0.85rem;font-weight:800;color:#064e3b!important;
    margin-bottom:1rem;
}}

/* ── FOOTER ── */
.agro-footer{{
    background:rgba(255,255,255,0.95);
    border-radius:16px 16px 0 0;padding:1.2rem 2rem;margin-top:3rem;
    display:flex;justify-content:space-around;align-items:center;
    font-weight:600;color:#374151;font-size:0.9rem;
    box-shadow:0 -8px 32px rgba(0,0,0,0.08);
}}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
_defaults = dict(role=None, state="Punjab", district="Ludhiana",
                 is_predicted=False, top_crop="Wheat",
                 globe_lat=20.59, globe_lon=78.96, globe_alt=2.0,
                 prediction_result=None)
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(lat, lon):
    try:
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
               f"precipitation,weather_code,wind_speed_10m&timezone=auto")
        req = urllib.request.Request(url, headers={"User-Agent": "AgroSenseAI/6"})
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.loads(r.read().decode()).get("current", {})
    except Exception:
        return {}

def load_soil():
    if os.path.exists(SOIL_DATA_PATH):
        with open(SOIL_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_soil(data):
    with open(SOIL_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def wx_label(code):
    if code == 0:        return "Clear Sky",     "☀️"
    if code in (1,2):    return "Partly Cloudy", "⛅"
    if code == 3:        return "Overcast",       "☁️"
    if 45<=code<=49:     return "Foggy",          "🌫️"
    if 51<=code<=57:     return "Drizzle",        "🌦️"
    if 61<=code<=67:     return "Rain",           "🌧️"
    if 71<=code<=77:     return "Snow",           "❄️"
    if 80<=code<=82:     return "Showers",        "🌦️"
    if 95<=code<=99:     return "Thunderstorm",   "⛈️"
    return "Variable", "🌥️"

# ── Globe HTML (cached per coords+state) ─────────────────────────────────────
@st.cache_data(show_spinner=False)
def build_globe_html(lat: float, lon: float, altitude: float,
                     is_predicted: bool, state_name: str) -> str:
    """Generate self-contained globe HTML. Cached — only rebuilds on coord/state change."""
    pred_js  = "true" if is_predicted else "false"
    state_js = state_name.replace("'", "\\'").lower()
    rot_spd  = "0.08" if is_predicted else "0.25"

    # Photorealistic textures from three-globe CDN
    day_tex   = "https://unpkg.com/three-globe/example/img/earth-day.jpg"
    night_tex = "https://unpkg.com/three-globe/example/img/earth-night.jpg"
    clouds_tex= "https://unpkg.com/three-globe/example/img/earth-clouds.png"
    bump_tex  = "https://unpkg.com/three-globe/example/img/earth-topology.png"
    water_tex = "https://unpkg.com/three-globe/example/img/earth-water.png"
    specular  = "https://unpkg.com/three-globe/example/img/earth-specular.jpg"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html,body{{margin:0;padding:0;background:transparent;width:100%;height:100%;overflow:hidden;}}
  #g{{width:100%;height:520px;}}
  #spinner{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
             background:transparent;z-index:99;transition:opacity 0.5s;}}
  #spinner svg{{animation:spin 1.2s linear infinite;}}
  @keyframes spin{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
</style>
</head>
<body>
<div id="spinner">
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5">
    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
    <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
  </svg>
</div>
<div id="g"></div>
<script>
// Inline-load Three.js then Globe.gl sequentially to avoid double-download on re-render
(function() {{
  function loadScript(src, cb) {{
    var s = document.createElement('script');
    s.src = src; s.onload = cb; document.head.appendChild(s);
  }}

  loadScript('https://unpkg.com/three@0.154.0/build/three.min.js', function() {{
    loadScript('https://unpkg.com/globe.gl@2.30.0/dist/globe.gl.min.js', function() {{
      var globe = Globe({{animateIn:false, waitForGlobeReady:true}})
        .globeImageUrl('{day_tex}')
        .bumpImageUrl('{bump_tex}')
        .backgroundColor('rgba(0,0,0,0)')
        .showAtmosphere(true)
        .atmosphereColor('rgba(100,180,255,1)')
        .atmosphereAltitude(0.18)
        (document.getElementById('g'));

      // Clouds overlay
      var THREE = window.THREE;
      var loader = new THREE.TextureLoader();
      loader.load('{clouds_tex}', function(tex) {{
        var clouds = new THREE.Mesh(
          new THREE.SphereGeometry(globe.getGlobeRadius() * 1.004, 64, 64),
          new THREE.MeshPhongMaterial({{
            map: tex, transparent: true, opacity: 0.4,
            depthWrite: false, blending: THREE.AdditiveBlending
          }})
        );
        globe.scene().add(clouds);
        // slow cloud drift
        (function animateClouds() {{
          requestAnimationFrame(animateClouds);
          clouds.rotation.y += 0.00008;
        }})();
      }});

      // Night side overlay using custom shader approach
      loader.load('{night_tex}', function(nightTex) {{
        var nightMesh = new THREE.Mesh(
          new THREE.SphereGeometry(globe.getGlobeRadius() * 0.999, 64, 64),
          new THREE.MeshBasicMaterial({{
            map: nightTex, transparent: true, opacity: 0.0,
            blending: THREE.AdditiveBlending, depthWrite: false
          }})
        );
        globe.scene().add(nightMesh);
      }});

      // Controls
      globe.controls().autoRotate = true;
      globe.controls().autoRotateSpeed = {rot_spd};
      globe.controls().enableZoom = false;
      globe.controls().enableDamping = true;
      globe.controls().dampingFactor = 0.05;

      // Animate camera to target with smooth easing
      globe.pointOfView({{lat:{lat},lng:{lon},altitude:{altitude}}}, 2800);

      // Glowing pulsing marker
      globe.pointsData([{{lat:{lat},lng:{lon}}}])
           .pointAltitude(0.04)
           .pointColor(function(){{return 'rgba(134,239,172,1)';  }})
           .pointRadius(0.5);

      // State polygon highlight (only after prediction)
      if ({pred_js}) {{
        fetch('https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States')
          .then(function(r){{return r.json();}})
          .then(function(geo){{
            globe.polygonsData(geo.features)
              .polygonCapColor(function(d){{
                return d.properties.NAME_1.toLowerCase()==='{state_js}'
                  ?'rgba(134,239,172,0.3)':'rgba(0,0,0,0)';
              }})
              .polygonSideColor(function(){{return 'rgba(0,0,0,0.02)';}})
              .polygonStrokeColor(function(d){{
                return d.properties.NAME_1.toLowerCase()==='{state_js}'
                  ?'rgba(134,239,172,0.9)':'rgba(255,255,255,0.05)';
              }})
              .polygonAltitude(0.002);
          }}).catch(function(){{}});
      }}

      // Hide spinner once globe is ready
      globe.onGlobeReady(function() {{
        var sp = document.getElementById('spinner');
        if(sp){{ sp.style.opacity='0'; setTimeout(function(){{sp.style.display='none';}},600); }}
      }});
    }});
  }});
}})();
</script>
</body>
</html>"""

# ── LOGIN PAGE ────────────────────────────────────────────────────────────────
def login_page():
    st.markdown("<div class='hero-title'>Smart Farming<br>for Future Generations</div>",
                unsafe_allow_html=True)
    st.markdown("<p class='hero-sub'>Data-driven crop recommendations, live weather and financial intelligence — purpose-built for Indian agriculture.</p>",
                unsafe_allow_html=True)

    c1, c2, _ = st.columns([1, 1, 1])
    with c1:
        with st.container(border=True):
            st.markdown("### 👨‍🌾 Farmer Portal")
            st.caption("Personalised recommendations & farm economics")
            u = st.text_input("Username", key="fu", placeholder="farmer")
            p = st.text_input("Password", type="password", key="fp", placeholder="farmer123")
            if st.button("Login as Farmer", type="primary", use_container_width=True):
                if u == "farmer" and p == "farmer123":
                    st.session_state.role = "farmer"; st.rerun()
                else:
                    st.error("Invalid credentials.")
    with c2:
        with st.container(border=True):
            st.markdown("### 🔬 Meteorologist Console")
            st.caption("Manage soil profiles & retrain the ML model")
            u = st.text_input("Username", key="mu", placeholder="meteo")
            p = st.text_input("Password", type="password", key="mp", placeholder="meteo123")
            if st.button("Login as Meteorologist", type="primary", use_container_width=True):
                if u == "meteo" and p == "meteo123":
                    st.session_state.role = "meteorologist"; st.rerun()
                else:
                    st.error("Invalid credentials.")

    st.markdown(
        '<div class="agro-footer">'
        '<span>🌾 Trusted by thousands of farmers across India</span>'
        '<div style="display:flex;gap:2rem;color:#6b7280;">'
        '<span>Agrovia</span><span>John Deere</span><span>Green Solutions</span>'
        '</div></div>',
        unsafe_allow_html=True)

if st.session_state.role is None:
    login_page(); st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# FARMER DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.role == "farmer":

    # Banner
    _b = ("✨  Best crop for " + st.session_state.district + ", " +
          st.session_state.state + "  →  " +
          st.session_state.top_crop.upper() +
          "  🌱  AgroSense AI · Live Weather + Soil Intelligence  ✨  •  ")
    st.markdown(
        '<div class="agro-banner">'
        '<marquee scrollamount="7" behavior="scroll" direction="left">'
        + _b + _b + _b +
        '</marquee></div>',
        unsafe_allow_html=True)

    # Nav
    cn1, cn2 = st.columns([8, 1])
    with cn1:
        st.markdown("<div class='nav-title'>🌾 AgroSense AI Dashboard</div>",
                    unsafe_allow_html=True)
    with cn2:
        if st.button("Logout", use_container_width=True):
            for k, v in _defaults.items():
                st.session_state[k] = v
            st.rerun()

    # ── Two column layout ─────────────────────────────────────────────────────
    col_globe, col_form = st.columns([1.55, 1], gap="large")

    # ── INPUT FORM (isolated — doesn't touch globe state) ─────────────────────
    with col_form:
        with st.container(border=True):
            st.markdown("### 🗺️ Geographic Intelligence")
            region    = st.selectbox("Region",   list(INDIAN_REGIONS.keys()),  key="sel_region")
            state     = st.selectbox("State",    INDIAN_REGIONS[region],        key="sel_state")
            districts = INDIAN_STATES_DISTRICTS.get(state, ["Central"])
            district  = st.selectbox("District", districts,                     key="sel_district")

            if state != st.session_state.state or district != st.session_state.district:
                st.session_state.state        = state
                st.session_state.district     = district
                st.session_state.is_predicted = False
                st.session_state.prediction_result = None
                c = STATE_COORDINATES.get(state, {"lat": 20.59, "lon": 78.96})
                st.session_state.globe_lat = c["lat"]
                st.session_state.globe_lon = c["lon"]
                st.session_state.globe_alt = 1.4
                build_globe_html.clear()   # force globe rebuild for new state
                st.rerun()

            st.markdown("### 🚜 Farm Scale & Economics")
            farm_size = st.number_input("Farm Size (Acres)", 0.25, 500.0, 2.5, step=0.25)
            budget    = st.number_input("Investment Capital (₹)", 5000, 50_000_000, 60000, step=5000)
            method    = st.radio("Cultivation Method", ["Regular", "Organic"], horizontal=True)

            st.write("")
            b1, b2 = st.columns([2, 1])
            with b1:
                if st.button("🚀 Analyze & Predict Crop", type="primary", use_container_width=True):
                    st.session_state.is_predicted = True
                    c = STATE_COORDINATES.get(state, {"lat": 20.59, "lon": 78.96})
                    st.session_state.globe_lat = c["lat"]
                    st.session_state.globe_lon = c["lon"]
                    st.session_state.globe_alt = 0.06   # zoom in
                    st.session_state.prediction_result = None  # trigger fresh prediction
                    build_globe_html.clear()   # force globe rebuild with zoom
                    st.rerun()
            with b2:
                if st.session_state.is_predicted:
                    if st.button("🌍 Reset Map", use_container_width=True):
                        st.session_state.globe_alt = 1.4
                        st.session_state.is_predicted = False
                        build_globe_html.clear()
                        st.rerun()

    # ── GLOBE + WEATHER (rendered from session state — stable across form reruns) ─
    state    = st.session_state.state
    district = st.session_state.district
    coords   = STATE_COORDINATES.get(state, {"lat": 20.59, "lon": 78.96})

    with col_globe:
        weather = fetch_weather(coords["lat"], coords["lon"])
        wc   = weather.get("weather_code", 0)
        temp = weather.get("temperature_2m", 25.0)
        hum  = weather.get("relative_humidity_2m", 70.0)

        if weather:
            cond, icon = wx_label(wc)
            at   = weather.get("apparent_temperature", temp)
            prec = weather.get("precipitation", 0)
            wind = weather.get("wind_speed_10m", 0)
            st.markdown(
                '<div class="wx-badge">'
                '<div>'
                '<div class="wx-label">🛰️ Live Climate · ' + state + '</div>'
                '<div class="wx-temp">' + str(temp) + '°C '
                '<span class="wx-feels">feels ' + str(at) + '°C</span></div>'
                '<div class="wx-detail">💨 ' + str(wind) + ' km/h &nbsp;·&nbsp; 🌧️ ' + str(prec) + ' mm</div>'
                '</div>'
                '<div style="text-align:right">'
                '<div class="wx-icon">' + icon + '</div>'
                '<div class="wx-cond">' + cond + '</div>'
                '<div class="wx-hum">Humidity ' + str(hum) + '%</div>'
                '</div></div>',
                unsafe_allow_html=True)

        # Globe – pulled from cache; only rebuilds when lat/lon/alt/state changes
        globe_html = build_globe_html(
            st.session_state.globe_lat,
            st.session_state.globe_lon,
            st.session_state.globe_alt,
            st.session_state.is_predicted,
            state
        )
        st.components.v1.html(globe_html, height=520, scrolling=False)

    # ── PREDICTION RESULTS ────────────────────────────────────────────────────
    if st.session_state.is_predicted:
        st.markdown("---")

        # Run prediction only once; cache in session state
        if st.session_state.prediction_result is None:
            soil_db   = load_soil()
            d_profile = soil_db.get(state, {}).get(district)
            if not d_profile:
                d_profile = {"n":50,"p":50,"k":50,"ph":6.5,"temperature":25,"humidity":70,"rainfall":100}

            n, p, k, ph = d_profile["n"], d_profile["p"], d_profile["k"], d_profile["ph"]
            p_temp = round(float(temp), 1)
            p_hum  = round(float(hum), 1)
            p_rain = d_profile.get("rainfall", 100)

            with st.spinner("Running Agronomic ML Pipeline…"):
                try:
                    res = predict_crop(n, p, k, p_temp, p_hum, ph, p_rain, top_n=5)

                    chosen_crop = chosen_disp = chosen_conf = chosen_meta = chosen_eco = None
                    for cand in res["top_candidates"]:
                        c_eco = calculate_farm_economics(cand["crop"], farm_size, budget, state, method)
                        if c_eco["is_sufficient"]:
                            chosen_crop = cand["crop"];  chosen_disp = cand["crop_display"]
                            chosen_conf = cand["confidence_pct"]; chosen_meta = cand["metadata"]
                            chosen_eco  = c_eco; break

                    if chosen_crop is None:
                        chosen_crop = res["recommended_crop"]; chosen_disp = res["recommended_crop_display"]
                        chosen_conf = res["confidence_pct"];  chosen_meta = res["metadata"]
                        chosen_eco  = calculate_farm_economics(chosen_crop, farm_size, budget, state, method)

                    st.session_state.top_crop = chosen_disp
                    st.session_state.prediction_result = dict(
                        top_crop=chosen_crop, top_crop_disp=chosen_disp,
                        conf=chosen_conf, meta=chosen_meta, eco=chosen_eco,
                        all_cands=res["top_candidates"],
                        n=n, p=p, k=k, ph=ph,
                        p_temp=p_temp, p_hum=p_hum, p_rain=p_rain,
                        d_profile_missing=not bool(soil_db.get(state,{}).get(district))
                    )
                except Exception as e:
                    st.error("Inference Error: " + str(e))
                    st.stop()

        # --- Render stored result ---
        R = st.session_state.prediction_result
        if R is None:
            st.stop()

        if R.get("d_profile_missing"):
            st.warning("⚠️ No precise soil data for **" + district + ", " + state +
                       "**. Using regional baseline.")

        st.markdown(
            '<div class="fv-row">'
            '🧬 <strong>Live Feature Vector</strong>: '
            'N:' + str(R["n"]) + '  P:' + str(R["p"]) + '  K:' + str(R["k"]) +
            '  pH:' + str(R["ph"]) + '  🌡️ ' + str(R["p_temp"]) +
            '°C  💧 ' + str(R["p_hum"]) + '%  🌧️ ' + str(R["p_rain"]) + 'mm'
            '</div>',
            unsafe_allow_html=True)

        # Result card
        emoji = R["meta"].get("emoji","🌱")
        st.markdown(
            '<div class="result-card">'
            '<div class="rc-pre">🏆 Primary Recommendation for ' + district + ', ' + state + '</div>'
            '<div class="rc-name">' + emoji + ' ' + R["top_crop_disp"] + '</div>'
            '<div class="rc-sci">' + R["meta"].get("scientific","") + ' &bull; ' + R["meta"].get("category","") + '</div>'
            '<div class="rc-conf">🎯 Model Confidence: ' + str(R["conf"]) + '%</div>'
            '<div class="rc-desc">' + R["meta"].get("desc","") + '</div>'
            '</div>',
            unsafe_allow_html=True)

        col_eco, col_why = st.columns(2, gap="large")

        with col_eco:
            with st.container(border=True):
                eco = R["eco"]
                st.markdown(
                    '<div class="sec-h">💰 Farm Economics & Yield</div>'
                    '<div class="sec-cap">Based on ' + str(farm_size) + ' acres · ' + state + ' · ' + method + '</div>',
                    unsafe_allow_html=True)
                st.metric("Estimated Investment",  "₹{:,.0f}".format(eco["total_estimated_investment"]))
                r1, r2 = st.columns(2)
                r1.metric("Expected Revenue", "₹{:,.0f}".format(eco["estimated_revenue"]))
                r2.metric("Projected Profit", "₹{:,.0f}".format(eco["estimated_profit"]))

                if eco["is_sufficient"]:
                    st.success("✅ Sufficient Capital — Surplus ₹{:,.0f}".format(eco["budget_difference"]))
                else:
                    st.error("⚠️ Capital Shortfall — Deficit ₹{:,.0f}".format(abs(eco["budget_difference"])))

                st.markdown("**🌿 Next Best Crops (Alternatives)**")
                alts = [c for c in R["all_cands"] if c["crop"] != R["top_crop"]][:3]
                pills = "".join(
                    '<span class="alt-pill">🌾 ' + a["crop_display"] +
                    ' <span style="opacity:.65;font-size:.75rem;">' + str(a["confidence_pct"]) + '%</span></span>'
                    for a in alts)
                st.markdown(pills, unsafe_allow_html=True)

        with col_why:
            with st.container(border=True):
                st.markdown(
                    '<div class="sec-h">🧬 Why This Crop?</div>'
                    '<div class="sec-cap">Your field fingerprint vs. optimal agronomic dataset range</div>',
                    unsafe_allow_html=True)

                profile = CROP_DATASET_PROFILES.get(R["top_crop"].lower(), {})
                params  = [
                    ("🧪 Nitrogen (N)",   R["n"],      profile.get("N")),
                    ("🧪 Phosphorus (P)", R["p"],      profile.get("P")),
                    ("🧪 Potassium (K)",  R["k"],      profile.get("K")),
                    ("🌡️ Temperature",    R["p_temp"], profile.get("temperature")),
                    ("💧 Humidity",       R["p_hum"],  profile.get("humidity")),
                    ("⚗️ Soil pH",        R["ph"],     profile.get("ph")),
                    ("🌧️ Rainfall",       R["p_rain"], profile.get("rainfall")),
                ]

                within  = 0
                rows_h  = ""
                for name, val, rng in params:
                    if rng:
                        lo, hi = rng
                        ok = lo <= val <= hi
                        if ok: within += 1
                        rc = "pr-match" if ok else "pr-miss"
                        bc = "pb-m"     if ok else "pb-x"
                        bt = ("✅ " + str(lo) + "–" + str(hi)) if ok else ("⚠️ " + str(lo) + "–" + str(hi))
                        rows_h += ('<div class="param-row ' + rc + '">'
                                   '<span>' + name + ': <strong>' + str(val) + '</strong></span>'
                                   '<span class="pbadge ' + bc + '">' + bt + '</span></div>')
                    else:
                        within += 1
                        rows_h += ('<div class="param-row pr-match">'
                                   '<span>' + name + ': <strong>' + str(val) + '</strong></span>'
                                   '<span class="pbadge pb-m">✅ OK</span></div>')

                st.markdown(rows_h, unsafe_allow_html=True)
                st.info("**" + str(within) + " / 7** parameters align with the optimal range for **" + R["top_crop_disp"] + "**.")
                if eco.get("is_prime_state"):
                    st.success("🌟 **" + state + "** is historically a prime region for " + R["top_crop_disp"] + ".")
                else:
                    st.warning("**" + state + "** may not be a traditional producer — soil & climate still indicate suitability.")

# ══════════════════════════════════════════════════════════════════════════════
# METEOROLOGIST DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.role == "meteorologist":
    cn1, cn2 = st.columns([8, 1])
    with cn1:
        st.markdown("<div class='nav-title'>🔬 Meteorologist Console</div>", unsafe_allow_html=True)
    with cn2:
        if st.button("Logout", use_container_width=True):
            st.session_state.role = None; st.rerun()

    with st.container(border=True):
        t1, t2, t3 = st.tabs(["📝 Soil Data Editor","⚙️ Model Retraining","📊 Metrics"])

        with t1:
            st.markdown("### District Soil Profiles")
            ms  = st.selectbox("State",    list(INDIAN_STATES_DISTRICTS.keys()), key="ms")
            md  = st.selectbox("District", INDIAN_STATES_DISTRICTS[ms],          key="md")
            sdb = load_soil()
            cur = sdb.get(ms,{}).get(md,{"n":50,"p":50,"k":50,"ph":6.5,"temperature":25.0,"humidity":70.0,"rainfall":100.0})
            c1,c2,c3 = st.columns(3)
            nn=c1.number_input("N",   0,150,int(cur.get("n",50)))
            np=c2.number_input("P",   0,150,int(cur.get("p",50)))
            nk=c3.number_input("K",   0,210,int(cur.get("k",50)))
            c4,c5,c6,c7=st.columns(4)
            nph=c4.number_input("pH", 3.5,10.0,float(cur.get("ph",6.5)),step=0.1)
            nt =c5.number_input("Temp°C",0.0,55.0,float(cur.get("temperature",25.0)),step=0.5)
            nh =c6.number_input("Hum%",5.0,100.0,float(cur.get("humidity",70.0)),step=1.0)
            nr =c7.number_input("Rain mm",10.0,350.0,float(cur.get("rainfall",100.0)),step=5.0)
            if st.button("💾 Save Profile", type="primary"):
                sdb.setdefault(ms,{})[md]={"n":nn,"p":np,"k":nk,"ph":nph,"temperature":nt,"humidity":nh,"rainfall":nr}
                save_soil(sdb)
                st.success("✅ Saved **" + md + ", " + ms + "**")

        with t2:
            st.markdown("### Retrain Pipeline")
            st.warning("⚠️ This overwrites existing model files.")
            data = load_and_clean_data()
            st.success("Dataset: " + str(len(data)) + " records · " + str(data["label"].nunique()) + " classes")
            st.dataframe(data.head(), use_container_width=True)
            if st.button("🚀 Start Retraining", type="primary"):
                with st.spinner("Training…"):
                    mets = train_model.train_and_evaluate()
                    import importlib, predict as _p; importlib.reload(_p)
                    st.success("✅ Model retrained."); st.json(mets)

        with t3:
            st.markdown("### Evaluation Metrics")
            if os.path.exists(METRICS_PATH):
                with open(METRICS_PATH) as f: mets=json.load(f)
                m1,m2,m3,m4=st.columns(4)
                m1.metric("Accuracy",  "{:.2f}%".format(mets.get("accuracy",0)*100))
                m2.metric("Precision", "{:.2f}%".format(mets.get("precision_weighted",0)*100))
                m3.metric("Recall",    "{:.2f}%".format(mets.get("recall_weighted",0)*100))
                m4.metric("F1",        "{:.2f}%".format(mets.get("f1_score_weighted",0)*100))
                if os.path.exists(CONFUSION_MATRIX_PATH):
                    st.image(CONFUSION_MATRIX_PATH, use_container_width=True)
            else:
                st.info("No metrics yet — please retrain.")
