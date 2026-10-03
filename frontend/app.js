/**
 * AgroSense AI — Frontend Application Logic v5.0
 * Fixed: ID mismatches, animation performance, Grok AI integration, Vercel-ready
 */
"use strict";

// ─── SESSION ─────────────────────────────────────────────────────────────────
const SESSION = { token: null, role: null, name: null, username: null };
const STATE   = {
  statesDistricts: {},
  regions: {},
  stateCoords: {},
  presets: {},
  metrics: null,
  cropMetadata: {},
  cropProfiles: {},
  currentSoilData: null,
  selectedRegion: null,
  weatherAbortCtrl: null,
};

const $ = id => document.getElementById(id);

// ─── PERFORMANCE: throttled rAF ─────────────────────────────────────────────
let _globeAnimId = null;
let _loginAnimId = null;
let _globeLastFrame = 0;
const GLOBE_FPS = 30; // cap to 30fps to avoid lag
const LOGIN_FPS = 24;

// ═══════════════════════════════════════════════════════════════════════════════
// LOGIN CANVAS — lightweight particle system (optimized)
// ═══════════════════════════════════════════════════════════════════════════════
function initLoginCanvas() {
  const canvas = $("loginCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let W, H, particles = [];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize, { passive: true });

  // Reduced particle count for performance
  const PARTICLE_COUNT = Math.min(40, Math.floor(window.innerWidth / 30));
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push({
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      r: Math.random() * 1.5 + 0.5,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      opacity: Math.random() * 0.4 + 0.1,
    });
  }

  function draw(ts) {
    _loginAnimId = requestAnimationFrame(draw);
    if (ts - _globeLastFrame < 1000 / LOGIN_FPS) return;
    _globeLastFrame = ts;

    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x % W, p.y % H, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(34,197,94,${p.opacity})`;
      ctx.fill();
    });

    // Draw connection lines (only nearby particles)
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(34,197,94,${0.12 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }
  requestAnimationFrame(draw);
}

function stopLoginCanvas() {
  if (_loginAnimId) { cancelAnimationFrame(_loginAnimId); _loginAnimId = null; }
}

// ═══════════════════════════════════════════════════════════════════════════════
// FARM BACKGROUND SLIDESHOW — rotates images every 5 seconds
// ═══════════════════════════════════════════════════════════════════════════════
let _farmBgInterval = null;
let _farmBgCurrentIndex = 0;

function initFarmBackgroundSlideshow() {
  const container = $("farmBgContainer");
  if (!container) return;
  const slides = container.querySelectorAll(".geo-hero__farm-slide");
  if (!slides.length) return;

  // Activate first slide
  slides.forEach((s, i) => s.classList.toggle("active", i === 0));
  _farmBgCurrentIndex = 0;

  // Clear any existing interval
  if (_farmBgInterval) clearInterval(_farmBgInterval);

  _farmBgInterval = setInterval(() => {
    slides[_farmBgCurrentIndex].classList.remove("active");
    _farmBgCurrentIndex = (_farmBgCurrentIndex + 1) % slides.length;
    slides[_farmBgCurrentIndex].classList.add("active");
  }, 5000);
}

function stopFarmBackgroundSlideshow() {
  if (_farmBgInterval) { clearInterval(_farmBgInterval); _farmBgInterval = null; }
}

// ═══════════════════════════════════════════════════════════════════════════════
// GLOBE CANVAS — optimized CSS-based rotating sphere (no heavy 3D math)
// ═══════════════════════════════════════════════════════════════════════════════
function initGlobe() {
  const canvas = $("globeCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let size = canvas.parentElement.offsetWidth || 400;
  canvas.width = size;
  canvas.height = size;

  let rotation = 0;
  let lastTs = 0;

  // Precomputed static land dots for India region
  const DOTS = generateGlobeDots(size);

  function generateGlobeDots(sz) {
    const dots = [];
    const r = sz / 2 - 4;
    // Generate lat/lon grid points
    for (let lat = -80; lat <= 80; lat += 8) {
      const cosLat = Math.cos(lat * Math.PI / 180);
      const numLon = Math.max(4, Math.round(36 * cosLat));
      for (let i = 0; i < numLon; i++) {
        const lon = (i / numLon) * 360 - 180;
        dots.push({ lat, lon, r: Math.random() * 1.5 + 0.8 });
      }
    }
    return dots;
  }

  function drawGlobe(ts) {
    _globeAnimId = requestAnimationFrame(drawGlobe);
    const dt = ts - lastTs;
    if (dt < 1000 / GLOBE_FPS) return;
    lastTs = ts;

    rotation += 0.003;
    const cx = size / 2, cy = size / 2, R = size / 2 - 4;

    ctx.clearRect(0, 0, size, size);

    // Sphere base
    const grad = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R);
    grad.addColorStop(0, "rgba(20,50,30,0.9)");
    grad.addColorStop(0.5, "rgba(10,25,15,0.95)");
    grad.addColorStop(1, "rgba(5,13,8,1)");
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Grid lines
    ctx.strokeStyle = "rgba(34,197,94,0.06)";
    ctx.lineWidth = 0.5;
    for (let lat = -60; lat <= 60; lat += 30) {
      const y = cy + R * Math.sin(lat * Math.PI / 180);
      const rLat = R * Math.cos(lat * Math.PI / 180);
      ctx.beginPath();
      ctx.ellipse(cx, y, rLat, rLat * 0.3, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    for (let lon = 0; lon < 360; lon += 30) {
      const a = (lon + rotation * 180 / Math.PI) * Math.PI / 180;
      ctx.beginPath();
      ctx.ellipse(cx, cy, Math.abs(R * Math.cos(a)) * 0.3, R, 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Dots
    DOTS.forEach(d => {
      const lonRad = (d.lon * Math.PI / 180) + rotation;
      const latRad = d.lat * Math.PI / 180;
      const cosLon = Math.cos(lonRad);
      if (cosLon < 0) return; // back face culling

      const x = cx + R * cosLon * Math.cos(latRad);
      const y = cy - R * Math.sin(latRad);
      const brightness = 0.1 + 0.4 * cosLon;

      ctx.beginPath();
      ctx.arc(x, y, d.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(34,197,94,${brightness})`;
      ctx.fill();
    });

    // Highlight India region (approx center ~20°N, 78°E)
    const indiaLon = (78 * Math.PI / 180) + rotation;
    const indiaLat = 20 * Math.PI / 180;
    const indCos = Math.cos(indiaLon);
    if (indCos > 0) {
      const ix = cx + R * indCos * Math.cos(indiaLat);
      const iy = cy - R * Math.sin(indiaLat);
      const glow = ctx.createRadialGradient(ix, iy, 0, ix, iy, 30);
      glow.addColorStop(0, "rgba(34,197,94,0.5)");
      glow.addColorStop(1, "rgba(34,197,94,0)");
      ctx.beginPath();
      ctx.arc(ix, iy, 30, 0, Math.PI * 2);
      ctx.fillStyle = glow;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(ix, iy, 4, 0, Math.PI * 2);
      ctx.fillStyle = "#22c55e";
      ctx.fill();
    }

    // Atmosphere rim
    const rimGrad = ctx.createRadialGradient(cx, cy, R * 0.85, cx, cy, R);
    rimGrad.addColorStop(0, "transparent");
    rimGrad.addColorStop(1, "rgba(34,197,94,0.08)");
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.fillStyle = rimGrad;
    ctx.fill();
  }

  requestAnimationFrame(drawGlobe);

  // Resize observer
  const ro = new ResizeObserver(() => {
    size = canvas.parentElement.offsetWidth || 400;
    canvas.width = size;
    canvas.height = size;
  });
  ro.observe(canvas.parentElement);
}

function stopGlobe() {
  if (_globeAnimId) { cancelAnimationFrame(_globeAnimId); _globeAnimId = null; }
}

// ═══════════════════════════════════════════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════════════════════════════════════════
function setupLoginScreen() {
  const loginScreen = $("loginScreen");
  const appRoot     = $("appRoot");
  const tabFarmer   = $("tabFarmer");
  const tabMeteo    = $("tabMeteo");
  const loginUser   = $("loginUser");
  const loginPass   = $("loginPass");
  const loginBtn    = $("loginBtn");
  const loginError  = $("loginError");
  const logoutBtn   = $("logoutBtn");
  const demoFarmer  = $("demoFarmerChip");
  const demoMeteo   = $("demoMeteoChip");

  let selectedRole = "farmer";
  let isRegisterMode = false;

  const regNameGroup = $("regNameGroup");
  const loginName    = $("loginName");
  const toggleRegText= $("toggleRegText");
  const toggleRegGroup = $("toggleRegGroup");

  function selectRole(role) {
    selectedRole = role;
    tabFarmer.classList.toggle("active", role === "farmer");
    tabMeteo.classList.toggle("active", role === "meteorologist");
    if (role === "meteorologist" && isRegisterMode) {
        toggleRegMode();
    }
    if (role === "meteorologist") {
        toggleRegGroup.style.display = "none";
    } else {
        toggleRegGroup.style.display = "block";
    }
  }
  tabFarmer.addEventListener("click", () => selectRole("farmer"));
  tabMeteo.addEventListener("click",  () => selectRole("meteorologist"));

  function toggleRegMode() {
      isRegisterMode = !isRegisterMode;
      if (isRegisterMode) {
          regNameGroup.style.display = "block";
          $("loginBtnText").textContent = "Create Account";
          toggleRegText.innerHTML = `Already have an account? <span style="color: #16a34a; font-weight: bold;">Log in</span>`;
      } else {
          regNameGroup.style.display = "none";
          $("loginBtnText").textContent = "Access Platform";
          toggleRegText.innerHTML = `Don't have an account? <span style="color: #16a34a; font-weight: bold;">Create one</span>`;
      }
      loginError.classList.add("hidden");
  }

  if (toggleRegText) {
      toggleRegText.addEventListener("click", toggleRegMode);
  }

  if (demoFarmer) {
    demoFarmer.addEventListener("click", () => {
      selectRole("farmer");
      if (isRegisterMode) toggleRegMode();
      loginUser.value = "farmer";
      loginPass.value = "farmer123";
      loginError.classList.add("hidden");
    });
  }
  if (demoMeteo) {
    demoMeteo.addEventListener("click", () => {
      selectRole("meteorologist");
      if (isRegisterMode) toggleRegMode();
      loginUser.value = "meteo";
      loginPass.value = "meteo123";
      loginError.classList.add("hidden");
    });
  }

  [loginUser, loginPass, loginName].forEach(el => {
    if(el) el.addEventListener("keydown", e => { if (e.key === "Enter") loginBtn.click(); });
  });

  loginBtn.addEventListener("click", async () => {
    const username = loginUser.value.trim();
    const password = loginPass.value;
    const name = loginName ? loginName.value.trim() : "";
    loginError.classList.add("hidden");

    if (!username || !password || (isRegisterMode && !name)) {
      showLoginError("Please enter all required fields.");
      return;
    }

    const btnText = $("loginBtnText");
    loginBtn.disabled = true;
    if (btnText) btnText.textContent = isRegisterMode ? "Registering…" : "Signing in…";

    try {
      if (isRegisterMode) {
          const res = await fetch("/api/register", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ username, password, name, role: selectedRole })
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || "Registration failed");
          
          toggleRegMode();
          showLoginError("Registration successful. You can now log in.");
          loginError.classList.remove("shake");
          loginError.style.color = "#16a34a"; // green
      } else {
          loginError.style.color = ""; // reset color
          const res  = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || "Invalid credentials");

          if (data.role !== selectedRole) selectRole(data.role);

          SESSION.token    = data.token;
          SESSION.role     = data.role;
          SESSION.name     = data.name;
          SESSION.username = data.username;

          // Stop heavy login canvas before transition
          stopLoginCanvas();

          loginScreen.classList.add("login-screen--out");
          setTimeout(() => {
            loginScreen.classList.add("hidden");
            appRoot.classList.remove("hidden");
            initApp();
          }, 350);
      }
    } catch (err) {
      loginError.style.color = "";
      showLoginError(err.message);
    } finally {
      loginBtn.disabled = false;
      if (btnText) btnText.textContent = isRegisterMode ? "Create Account" : "Access Platform";
    }
  });

  function showLoginError(msg) {
    loginError.textContent = "⚠ " + msg;
    loginError.classList.remove("hidden");
    loginError.classList.add("shake");
    setTimeout(() => loginError.classList.remove("shake"), 500);
  }

  logoutBtn.addEventListener("click", async () => {
    if (SESSION.token) {
      await fetch("/api/logout", {
        method: "POST",
        headers: { Authorization: "Bearer " + SESSION.token }
      }).catch(() => {});
    }
    stopGlobe();
    stopFarmBackgroundSlideshow();
    SESSION.token = SESSION.role = SESSION.name = SESSION.username = null;
    appRoot.classList.add("hidden");
    loginScreen.classList.remove("hidden", "login-screen--out");
    loginUser.value = "";
    loginPass.value = "";
    loginError.classList.add("hidden");
    // Restart login canvas
    initLoginCanvas();
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// APP INIT
// ═══════════════════════════════════════════════════════════════════════════════
async function initApp() {
  // Set nav role badge
  const navBadge = $("navBadge");
  const navUser  = $("navUser");
  if (navBadge) {
    navBadge.textContent = SESSION.role === "meteorologist" ? "🔬 Meteorologist" : "👨‍🌾 Farmer";
    navBadge.className = SESSION.role === "meteorologist"
      ? "topnav__badge topnav__badge--meteo"
      : "topnav__badge topnav__badge--farmer";
  }
  if (navUser) navUser.textContent = SESSION.name || SESSION.username || "";

  // Show role dashboards
  const farmerDash = $("farmerDash");
  const meteoDash  = $("meteoDash");
  if (SESSION.role === "meteorologist") {
    if (farmerDash) farmerDash.classList.add("hidden");
    if (meteoDash)  meteoDash.classList.remove("hidden");
  } else {
    if (farmerDash) farmerDash.classList.remove("hidden");
    if (meteoDash)  meteoDash.classList.add("hidden");
  }

  // Init globe (farmer only)
  if (SESSION.role === "farmer") {
    initGlobe();
    initFarmBackgroundSlideshow();
  }

  // Fetch metadata
  try {
    const res  = await fetch("/api/metadata");
    const data = await res.json();
    STATE.statesDistricts = data.states_districts || {};
    STATE.regions         = data.regions || {};
    STATE.stateCoords     = data.state_coordinates || {};
    STATE.presets         = data.presets || {};
    STATE.metrics         = data.model_metrics || null;
    STATE.cropMetadata    = data.crop_metadata || {};
    STATE.cropProfiles    = data.crop_profiles || {};

    populateRegions();
    populateStates();
    populatePresets();
    populateTechMetrics();

    // Meteo: populate state select too
    if (SESSION.role === "meteorologist") {
      populateMeteoStates();
    }
  } catch (err) {
    console.error("Metadata fetch failed:", err);
  }

  // Wire listeners
  wireListeners();
}

// ─── REGIONS ─────────────────────────────────────────────────────────────────
function populateRegions() {
  const grid = $("regionGrid");
  if (!grid) return;
  const regions = Object.keys(STATE.regions);
  if (!regions.length) return;

  grid.innerHTML = regions.map(r =>
    `<button class="region-btn" data-region="${escHtml(r)}">${escHtml(r)}</button>`
  ).join("");

  grid.querySelectorAll(".region-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      grid.querySelectorAll(".region-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      STATE.selectedRegion = btn.dataset.region;
      filterStatesByRegion(btn.dataset.region);
    });
  });
}

function filterStatesByRegion(region) {
  const stateSelect = $("stateSelect");
  if (!stateSelect) return;
  const regionStates = STATE.regions[region] || [];
  const states = regionStates.length ? regionStates : Object.keys(STATE.statesDistricts);
  stateSelect.innerHTML = states.sort().map(s =>
    `<option value="${escHtml(s)}">${escHtml(s)}</option>`
  ).join("");
  populateDistricts(stateSelect.value);
  onLocationChange();
}

// ─── STATES & DISTRICTS ─────────────────────────────────────────────────────
function populateStates() {
  const stateSelect = $("stateSelect");
  if (!stateSelect) return;
  const states = Object.keys(STATE.statesDistricts).sort();
  stateSelect.innerHTML = states.map(s =>
    `<option value="${escHtml(s)}"${s === "Punjab" ? " selected" : ""}>${escHtml(s)}</option>`
  ).join("");
  populateDistricts(stateSelect.value);
  onLocationChange();
}

function populateDistricts(state) {
  const districtSelect = $("districtSelect");
  if (!districtSelect) return;
  const districts = STATE.statesDistricts[state] || [];
  districtSelect.innerHTML = districts.length
    ? districts.map(d => `<option value="${escHtml(d)}">${escHtml(d)}</option>`).join("")
    : `<option value="">No districts</option>`;
}

function populateMeteoStates() {
  const mSel = $("mStateSelect");
  if (!mSel) return;
  const states = Object.keys(STATE.statesDistricts).sort();
  mSel.innerHTML = states.map(s =>
    `<option value="${escHtml(s)}">${escHtml(s)}</option>`
  ).join("");
  populateMeteoDistricts(mSel.value);
}

function populateMeteoDistricts(state) {
  const mDSel = $("mDistrictSelect");
  if (!mDSel) return;
  const districts = STATE.statesDistricts[state] || [];
  mDSel.innerHTML = districts.length
    ? districts.map(d => `<option value="${escHtml(d)}">${escHtml(d)}</option>`).join("")
    : `<option value="">No districts</option>`;
}

// ─── LOCATION CHANGE ─────────────────────────────────────────────────────────
function onLocationChange() {
  const state    = ($("stateSelect") || {}).value || "";
  const district = ($("districtSelect") || {}).value || "";
  if (!state || !district) return;

  // Update globe pin
  updateGlobePin(state, district);

  // Update location display
  const locState    = $("locState");
  const locDistrict = $("locDistrict");
  if (locState)    locState.textContent    = state;
  if (locDistrict) locDistrict.textContent = district;

  // Load weather + soil
  loadWeather(state);
  loadSoilForDistrict(false);
}

function updateGlobePin(state, district) {
  const pin      = $("globePin");
  const pinLabel = $("globePinLabel");
  const hint     = $("globeHint");
  if (!pin) return;
  pin.classList.remove("hidden");
  if (pinLabel) pinLabel.textContent = district;
  if (hint) hint.style.opacity = "0";

  const locCoords = $("locCoords");
  const coords = STATE.stateCoords[state];
  if (coords && locCoords) {
    const lat = coords.lat || coords[0];
    const lon = coords.lon || coords[1];
    locCoords.textContent = `${lat.toFixed(1)}°N, ${lon.toFixed(1)}°E`;
  }
}

// ─── WEATHER ─────────────────────────────────────────────────────────────────
async function loadWeather(state) {
  const coords = STATE.stateCoords[state];
  if (!coords) {
    showWeatherUnavailable();
    return;
  }

  const wpLocation = $("wpLocation");
  const wpLoading  = $("wpLoading");
  const wpData     = $("wpData");
  const wpUnavail  = $("wpUnavail");

  if (wpLocation) wpLocation.textContent = state;
  if (wpLoading)  { wpLoading.classList.remove("hidden"); }
  if (wpData)     wpData.classList.add("hidden");
  if (wpUnavail)  wpUnavail.classList.add("hidden");

  // Cancel previous request
  if (STATE.weatherAbortCtrl) STATE.weatherAbortCtrl.abort();
  STATE.weatherAbortCtrl = new AbortController();

  try {
    const lat = coords.lat || coords[0];
    const lon = coords.lon || coords[1];
    const res = await fetch(`/api/weather?lat=${lat}&lon=${lon}`, {
      signal: STATE.weatherAbortCtrl.signal
    });
    if (!res.ok) throw new Error("Weather API error");
    const w = await res.json();
    STATE.currentWeather = w;

    if (!w.available) throw new Error("Unavailable");

    const wpTempEl = $("wpTemp");
    if (wpTempEl)     wpTempEl.textContent = `${Math.round(w.temperature)}°C`;
    if ($("wpFeels")) $("wpFeels").textContent = w.feels_like != null ? `Feels ${Math.round(w.feels_like)}°C` : "";
    if ($("wpCondition")) $("wpCondition").textContent = w.condition || "—";
    if ($("wpStats")) {
      $("wpStats").innerHTML = `
        <div class="wp-stat"><div class="wp-stat-label">Humidity</div><div class="wp-stat-val">${w.humidity ?? "—"}%</div></div>
        <div class="wp-stat"><div class="wp-stat-label">Wind</div><div class="wp-stat-val">${w.wind_speed ?? "—"} km/h</div></div>
        <div class="wp-stat"><div class="wp-stat-label">Rain</div><div class="wp-stat-val">${w.rain ?? 0} mm</div></div>
        <div class="wp-stat"><div class="wp-stat-label">Precip.</div><div class="wp-stat-val">${w.precipitation ?? 0} mm</div></div>
      `;
    }
    if ($("wpUpdated")) $("wpUpdated").textContent = w.cached ? "Cached data" : `Updated just now`;
    if ($("wpLiveLabel")) $("wpLiveLabel").textContent = "LIVE CLIMATE";

    // Weather effect
    const effect = $("wpEffect");
    if (effect) {
      effect.className = "wp-effect " + (w.condition_code || "");
    }

    if (wpLoading) wpLoading.classList.add("hidden");
    if (wpData)    wpData.classList.remove("hidden");

  } catch (err) {
    if (err.name === "AbortError") return;
    showWeatherUnavailable();
  }
}

function showWeatherUnavailable() {
  const wpLoading = $("wpLoading");
  const wpData    = $("wpData");
  const wpUnavail = $("wpUnavail");
  if (wpLoading) wpLoading.classList.add("hidden");
  if (wpData)    wpData.classList.add("hidden");
  if (wpUnavail) wpUnavail.classList.remove("hidden");
}

// ─── SOIL DATA ───────────────────────────────────────────────────────────────
async function loadSoilForDistrict(skipPopulate = false) {
  const state    = ($("stateSelect") || {}).value || "";
  const district = ($("districtSelect") || {}).value || "";
  if (!state || !district) return;

  try {
    const res  = await fetch(`/api/soil-data?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`);
    const json = await res.json();
    STATE.currentSoilData = json.data;

    // Update soil tiles in weather panel
    const stN  = $("stN"),  stP  = $("stP"),  stK  = $("stK"),  stPH = $("stPH");
    const soil = json.data || {};
    if (stN)  stN.textContent  = soil.n  != null ? Number(soil.n).toFixed(0)  : "—";
    if (stP)  stP.textContent  = soil.p  != null ? Number(soil.p).toFixed(0)  : "—";
    if (stK)  stK.textContent  = soil.k  != null ? Number(soil.k).toFixed(0)  : "—";
    if (stPH) stPH.textContent = soil.ph != null ? Number(soil.ph).toFixed(1) : "—";
    const soilSrc = $("soilSrc");
    if (soilSrc) soilSrc.textContent = json.found ? "Dataset" : "Default";

    // Meteo: populate edit fields
    if (SESSION.role === "meteorologist" && !skipPopulate) {
      populateMeteoSoilFields(json.data);
    }

  } catch (err) {
    console.error("Soil data fetch failed:", err);
  }
}

function populateMeteoSoilFields(data) {
  if (!data) return;
  syncRangeNum($("mNRange"),    $("mNInput"),    data.n);
  syncRangeNum($("mPRange"),    $("mPInput"),    data.p);
  syncRangeNum($("mKRange"),    $("mKInput"),    data.k);
  syncRangeNum($("mTempRange"), $("mTempInput"), data.temperature);
  syncRangeNum($("mHumRange"),  $("mHumInput"),  data.humidity);
  syncRangeNum($("mRainRange"), $("mRainInput"), data.rainfall);
  if ($("mPhRange") && data.ph != null) {
    $("mPhRange").value = data.ph;
    updateMeteoPhDisplay();
  }
}

function syncRangeNum(range, num, val) {
  if (!range || !num || val == null) return;
  const v = parseFloat(val);
  range.value = Math.min(parseFloat(range.max), Math.max(parseFloat(range.min), v));
  num.value = v;
}

// ─── PRESETS ─────────────────────────────────────────────────────────────────
function populatePresets() {
  const presetGrid = $("presetGrid");
  if (!presetGrid) return;
  const presets = STATE.presets;
  if (!Object.keys(presets).length) {
    presetGrid.innerHTML = "<p style='color:#64748b;font-size:.85rem'>No presets available.</p>";
    return;
  }
  presetGrid.innerHTML = Object.entries(presets).map(([label]) =>
    `<button class="preset-btn" data-preset="${escHtml(label)}" type="button">${escHtml(label)}</button>`
  ).join("");

  presetGrid.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", () => applyPreset(btn.dataset.preset, btn));
  });
}

function applyPreset(label, btnEl) {
  const p = STATE.presets[label];
  if (!p) return;
  $("presetGrid").querySelectorAll(".preset-btn").forEach(b => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");

  // Meteo state/district
  const mSel = $("mStateSelect");
  const mDSel = $("mDistrictSelect");
  if (mSel && p.state) {
    mSel.value = p.state;
    populateMeteoDistricts(p.state);
    if (mDSel && p.district) mDSel.value = p.district;
  }

  // Fill NPK etc.
  syncRangeNum($("mNRange"), $("mNInput"), p.n);
  syncRangeNum($("mPRange"), $("mPInput"), p.p);
  syncRangeNum($("mKRange"), $("mKInput"), p.k);
  syncRangeNum($("mTempRange"), $("mTempInput"), p.temp);
  syncRangeNum($("mHumRange"),  $("mHumInput"),  p.hum);
  syncRangeNum($("mRainRange"), $("mRainInput"), p.rain);
  if ($("mPhRange") && p.ph != null) {
    $("mPhRange").value = p.ph;
    updateMeteoPhDisplay();
  }
}

// ─── METEO PH DISPLAY ────────────────────────────────────────────────────────
function updateMeteoPhDisplay() {
  const phRange = $("mPhRange");
  if (!phRange) return;
  const v = parseFloat(phRange.value);
  const disp = $("mPhDisplay");
  if (disp) disp.textContent = v.toFixed(2);

  let tag = "Neutral";
  if (v < 5.5)      tag = "Strongly Acidic";
  else if (v < 6.0) tag = "Moderately Acidic";
  else if (v < 6.5) tag = "Slightly Acidic";
  else if (v < 7.0) tag = "Near Neutral";
  else if (v < 7.5) tag = "Neutral";
  else if (v < 8.0) tag = "Slightly Alkaline";
  else if (v < 9.0) tag = "Moderately Alkaline";
  else              tag = "Strongly Alkaline";

  const phTag = $("mPhTag");
  if (phTag) phTag.textContent = tag;
}

// ─── WIRE LISTENERS ──────────────────────────────────────────────────────────
let _listenersWired = false;
function wireListeners() {
  if (_listenersWired) return;
  _listenersWired = true;

  // Farmer: location selects
  const stateSelect = $("stateSelect");
  const distSelect  = $("districtSelect");
  if (stateSelect) {
    stateSelect.addEventListener("change", () => {
      populateDistricts(stateSelect.value);
      onLocationChange();
    });
  }
  if (distSelect) {
    distSelect.addEventListener("change", onLocationChange);
  }

  // Farming method toggle
  const methodToggle = $("methodToggle");
  if (methodToggle) {
    methodToggle.querySelectorAll(".method-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        methodToggle.querySelectorAll(".method-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
      });
    });
  }

  // Farmer predict button
  const farmerPredictBtn = $("farmerPredictBtn");
  if (farmerPredictBtn) {
    farmerPredictBtn.addEventListener("click", runPrediction);
  }

  // Tech panel toggle
  const techToggle = $("techToggle");
  if (techToggle) techToggle.addEventListener("click", toggleTechPanel);

  // Meteo: state change
  const mStateSelect = $("mStateSelect");
  const mDistrictSelect = $("mDistrictSelect");
  if (mStateSelect) {
    mStateSelect.addEventListener("change", () => {
      populateMeteoDistricts(mStateSelect.value);
      loadMeteoSoilData();
    });
  }
  if (mDistrictSelect) {
    mDistrictSelect.addEventListener("change", loadMeteoSoilData);
  }

  // Meteo pH
  const mPhRange = $("mPhRange");
  if (mPhRange) mPhRange.addEventListener("input", updateMeteoPhDisplay);

  // Synced range/number pairs
  const pairs = [
    ["mNRange", "mNInput"], ["mPRange", "mPInput"], ["mKRange", "mKInput"],
    ["mTempRange", "mTempInput"], ["mHumRange", "mHumInput"], ["mRainRange", "mRainInput"]
  ];
  pairs.forEach(([rid, nid]) => wirePair($( rid), $(nid)));

  // Farmer: acres range
  const acresRange = $("acresRange");
  const acresInput = $("acresInput");
  if (acresRange && acresInput) wirePair(acresRange, acresInput);

  // Budget input
  const budgetInput = $("budgetInput");
  // Already plain number input, no pairing needed

  // Save soil
  const saveSoilBtn = $("saveSoilBtn");
  if (saveSoilBtn) saveSoilBtn.addEventListener("click", saveSoilData);

  // Retrain
  const retrainBtn = $("retrainBtn");
  if (retrainBtn) retrainBtn.addEventListener("click", retrainModel);
}

function wirePair(rangeEl, numEl) {
  if (!rangeEl || !numEl) return;
  const min = parseFloat(rangeEl.min) || 0;
  const max = parseFloat(rangeEl.max) || 100;
  rangeEl.addEventListener("input", () => { numEl.value = rangeEl.value; });
  numEl.addEventListener("input", () => {
    let v = parseFloat(numEl.value);
    if (!isNaN(v)) {
      v = Math.min(max, Math.max(min, v));
      rangeEl.value = v;
    }
  });
  numEl.addEventListener("change", () => {
    let v = parseFloat(numEl.value);
    if (isNaN(v)) v = min;
    v = Math.min(max, Math.max(min, v));
    numEl.value = v;
    rangeEl.value = v;
  });
}

// ─── METEO SOIL DATA LOAD ────────────────────────────────────────────────────
async function loadMeteoSoilData() {
  const state    = ($("mStateSelect")    || {}).value || "";
  const district = ($("mDistrictSelect") || {}).value || "";
  if (!state || !district) return;
  try {
    const res  = await fetch(`/api/soil-data?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`);
    const json = await res.json();
    STATE.currentSoilData = json.data;
    populateMeteoSoilFields(json.data);
  } catch (err) {
    console.error("Meteo soil data fetch failed:", err);
  }
}

// ─── SAVE SOIL DATA (meteo) ──────────────────────────────────────────────────
async function saveSoilData() {
  const saveBtn    = $("saveSoilBtn");
  const saveStatus = $("saveStatus");
  const state      = ($("mStateSelect")    || {}).value || "";
  const district   = ($("mDistrictSelect") || {}).value || "";

  if (!state || !district) {
    showSaveStatus("❌ Please select a state and district first.", "error");
    return;
  }

  const payload = {
    state, district,
    n:           numOr($("mNInput")?.value,    50),
    p:           numOr($("mPInput")?.value,    50),
    k:           numOr($("mKInput")?.value,    50),
    ph:          numOr($("mPhRange")?.value,   6.5),
    temperature: numOr($("mTempInput")?.value, 25),
    humidity:    numOr($("mHumInput")?.value,  70),
    rainfall:    numOr($("mRainInput")?.value, 100),
  };

  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving…";
  }

  try {
    const res = await fetch("/api/soil-data", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + (SESSION.token || "")
      },
      body: JSON.stringify(payload)
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : "Save failed");
    showSaveStatus(`✅ Updated ${district}, ${state}`, "success");
    STATE.currentSoilData = json.data;
  } catch (err) {
    showSaveStatus(`❌ ${err.message}`, "error");
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = `<svg viewBox="0 0 20 20" fill="currentColor"><path d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L9 12.586l7.293-7.293a1 1 0 011.414 1.414l-8 8z"/></svg> Save Soil Data to District Dataset`;
    }
  }
}

function showSaveStatus(msg, type) {
  const el = $("saveStatus");
  if (!el) return;
  el.textContent = msg;
  el.className = `save-status${type === "error" ? " save-status--error" : " save-status--success"}`;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 4500);
}

// ─── RETRAIN MODEL ───────────────────────────────────────────────────────────
async function retrainModel() {
  const retrainBtn    = $("retrainBtn");
  const retrainStatus = $("retrainStatus");

  if (retrainBtn) { retrainBtn.disabled = true; retrainBtn.textContent = "Retraining…"; }
  if (retrainStatus) { retrainStatus.className = "retrain-status"; retrainStatus.textContent = "Running model retraining…"; retrainStatus.classList.remove("hidden"); }

  try {
    const res = await fetch("/api/retrain", {
      method: "POST",
      headers: { "Authorization": "Bearer " + (SESSION.token || "") }
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || "Retrain failed");
    if (retrainStatus) {
      retrainStatus.className = "retrain-status retrain-status--success";
      retrainStatus.textContent = `✅ Model retrained! Accuracy: ${(json.accuracy * 100).toFixed(2)}%`;
    }
    STATE.metrics = json;
    populateTechMetrics();
  } catch (err) {
    if (retrainStatus) {
      retrainStatus.className = "retrain-status retrain-status--error";
      retrainStatus.textContent = `❌ ${err.message}`;
    }
  } finally {
    if (retrainBtn) {
      retrainBtn.disabled = false;
      retrainBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg> Retrain ML Model Now`;
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PREDICTION — uses ML backend + Grok AI for insights
// ═══════════════════════════════════════════════════════════════════════════════
async function runPrediction() {
  const state    = ($("stateSelect")    || {}).value || "Punjab";
  const district = ($("districtSelect") || {}).value || "Ludhiana";
  const acres    = numOr($("acresInput")?.value, 2.5);
  const budget   = numOr($("budgetInput")?.value, 60000);

  // Farming method
  let farmingMethod = "regular";
  const activeMethod = document.querySelector(".method-btn.active");
  if (activeMethod) farmingMethod = activeMethod.dataset.method || "regular";

  // ALWAYS fetch fresh soil data before prediction (fixes race condition / stale data bug)
  let soil = STATE.currentSoilData || {};
  try {
    const soilRes = await fetch(`/api/soil-data?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`);
    const soilJson = await soilRes.json();
    soil = soilJson.data || soil;
    STATE.currentSoilData = soil;
    // Update soil display tiles right away
    if ($("stN"))   $("stN").textContent   = soil.n  != null ? Number(soil.n).toFixed(0)  : "—";
    if ($("stP"))   $("stP").textContent   = soil.p  != null ? Number(soil.p).toFixed(0)  : "—";
    if ($("stK"))   $("stK").textContent   = soil.k  != null ? Number(soil.k).toFixed(0)  : "—";
    if ($("stPH"))  $("stPH").textContent  = soil.ph != null ? Number(soil.ph).toFixed(1) : "—";
    if ($("soilSrc")) $("soilSrc").textContent = soilJson.found ? "Dataset" : "Regional";
  } catch(e) { console.warn("Soil pre-fetch failed, using cached:", e); }

  // Live weather for temp/humidity overlay, soil for rainfall baseline
  const weather  = STATE.currentWeather || {};
  const pTemp = weather.temperature != null ? weather.temperature : numOr(soil.temperature, 25);
  const pHum  = weather.humidity    != null ? weather.humidity    : numOr(soil.humidity, 70);
  const pRain = (weather.precipitation > 0) ? weather.precipitation * 30 : numOr(soil.rainfall, 100);

  const payload = {
    n:           numOr(soil.n, 75),
    p:           numOr(soil.p, 38),
    k:           numOr(soil.k, 42),
    ph:          numOr(soil.ph, 6.8),
    temperature: pTemp,
    humidity:    pHum,
    rainfall:    pRain,
    farm_acres:  acres,
    user_budget: budget,
    state, district,
    farming_method: farmingMethod,
  };

  const loadingOverlay   = $("loadingOverlay");
  const resultsSection   = $("resultsSection");
  const farmerPredictBtn = $("farmerPredictBtn");

  if (loadingOverlay)   loadingOverlay.classList.remove("hidden");
  if (resultsSection)   resultsSection.style.display = "none";
  if (farmerPredictBtn) { farmerPredictBtn.disabled = true; farmerPredictBtn.style.opacity = "0.7"; }

  try {
    // 1. Run ML prediction
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(SESSION.token ? { "Authorization": "Bearer " + SESSION.token } : {})
      },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(typeof err.detail === "string" ? err.detail : "Prediction failed");
    }
    const data = await res.json();

    // 2. Get Grok AI insights (non-blocking — renders immediately)
    renderResults(data, payload);

    // 3. Fetch Grok insights async and append
    fetchGrokInsights(data, payload);

  } catch (err) {
    showPredictionError(`Prediction failed: ${err.message}`);
  } finally {
    if (loadingOverlay)   loadingOverlay.classList.add("hidden");
    if (farmerPredictBtn) { farmerPredictBtn.disabled = false; farmerPredictBtn.style.opacity = ""; }
  }
}

// ─── GROK AI INSIGHTS ────────────────────────────────────────────────────────
async function fetchGrokInsights(predData, inputs) {
  const grokPanel = $("grokInsights");
  if (!grokPanel) return;

  grokPanel.innerHTML = `
    <div class="grok-loading">
      <div class="spinner-sm"></div>
      <span>Grok AI is analyzing your farm conditions…</span>
    </div>`;
  grokPanel.classList.remove("hidden");

  try {
    const res = await fetch("/api/grok-insights", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(SESSION.token ? { "Authorization": "Bearer " + SESSION.token } : {})
      },
      body: JSON.stringify({
        crop: predData.recommended_crop_display,
        confidence: predData.confidence_pct,
        state: inputs.state,
        district: inputs.district,
        n: inputs.n, p: inputs.p, k: inputs.k, ph: inputs.ph,
        temperature: inputs.temperature,
        humidity: inputs.humidity,
        rainfall: inputs.rainfall,
        farm_acres: inputs.farm_acres,
        farming_method: inputs.farming_method,
        top_alternatives: (predData.top_candidates || []).slice(1, 4).map(c => c.crop_display),
        economics: predData.economics,
      })
    });

    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || "Grok API error");

    grokPanel.innerHTML = `
      <div class="grok-header">
        <span class="grok-badge">🤖 Grok AI Agricultural Analysis</span>
        <span class="grok-model">${escHtml(json.model || "grok-2")}</span>
      </div>
      <div class="grok-content">${formatGrokResponse(json.insights || "")}</div>
    `;
  } catch (err) {
    grokPanel.innerHTML = `
      <div class="grok-header">
        <span class="grok-badge">🤖 Grok AI Analysis</span>
        <span class="grok-error">Unavailable — ${escHtml(err.message)}</span>
      </div>
      <div class="grok-content grok-content--muted">
        Configure <code>GROK_API_KEY</code> in your environment to enable live AI insights.<br>
        ML prediction above is fully functional without Grok.
      </div>
    `;
  }
}

function formatGrokResponse(text) {
  // Convert markdown-like formatting to HTML
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/^### (.*)/gm, "<h4>$1</h4>")
    .replace(/^## (.*)/gm, "<h3>$1</h3>")
    .replace(/^- (.*)/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>");
}

// ─── RENDER RESULTS ──────────────────────────────────────────────────────────
function renderResults(data, inputs) {
  const { recommended_crop_display, confidence_pct, metadata, economics, top_candidates, why_analysis, within_range_count, total_features } = data;
  const eco = economics || {};

  // Verify banner
  const verifyBanner = $("verifyBanner");
  if (verifyBanner) {
    verifyBanner.innerHTML = `
      <strong>✅ ML Model Execution Successful</strong> &nbsp;·&nbsp;
      N: <strong>${inputs.n}</strong> | P: <strong>${inputs.p}</strong> | K: <strong>${inputs.k}</strong> |
      Temp: <strong>${inputs.temperature}°C</strong> | Humidity: <strong>${inputs.humidity}%</strong> |
      pH: <strong>${inputs.ph}</strong> | Rainfall: <strong>${inputs.rainfall}mm</strong>
    `;
  }

  // Crop name & info
  const recCropName  = $("recCropName");
  const recScientific = $("recScientific");
  const recDesc      = $("recDesc");
  const recChips     = $("recChips");
  if (recCropName)   recCropName.textContent   = `${metadata?.emoji || "🌱"} ${recommended_crop_display}`;
  if (recScientific) recScientific.textContent = `${metadata?.scientific || ""} · ${metadata?.category || "Agricultural Crop"}`;
  if (recDesc)       recDesc.textContent       = metadata?.desc || "Optimal conditions identified for high yield.";
  if (recChips) {
    const chips = [
      metadata?.water    ? `💧 ${metadata.water}` : null,
      metadata?.season   ? `📅 ${metadata.season}` : null,
      eco.is_prime_state ? `⭐ Prime State` : null,
    ].filter(Boolean);
    recChips.innerHTML = chips.map(c => `<span class="rec-chip">${escHtml(c)}</span>`).join("");
  }

  // Confidence ring
  const crFill  = $("crFill");
  const crLabel = $("crLabel");
  const circumference = 314;
  if (crFill)  crFill.style.strokeDashoffset  = circumference - (confidence_pct / 100) * circumference;
  if (crLabel) crLabel.textContent            = `${confidence_pct}%`;

  // Region suitability
  const regionSuitability = $("regionSuitability");
  if (regionSuitability) {
    regionSuitability.textContent = eco.is_prime_state
      ? `⭐ Highly Suitable in ${inputs.state}`
      : `✓ Favorable in ${inputs.state}`;
  }

  // WHY THIS CROP — why match score
  const whyMatchScore = $("whyMatchScore");
  if (whyMatchScore) {
    whyMatchScore.textContent = `${within_range_count || 0} / ${total_features || 7} parameters match optimal range`;
  }

  // Why features breakdown
  const whyFeatures = $("whyFeatures");
  if (whyFeatures && why_analysis) {
    whyFeatures.innerHTML = why_analysis.map(f => {
      const cls = f.within_range ? "good" : (f.alignment_pct > 40 ? "warn" : "bad");
      return `
        <div class="why-feat">
          <span class="wf-label">${escHtml(f.feature)}</span>
          <div class="wf-bar-wrap">
            <div class="wf-bar wf-bar--${cls}" style="width:${f.alignment_pct}%"></div>
          </div>
          <span class="wf-tag wf-tag--${cls}">${escHtml(f.alignment_label)}</span>
        </div>
      `;
    }).join("");
  }

  // Radar chart
  drawRadarChart(why_analysis || []);

  // ECONOMICS
  renderEconomics(eco, inputs);

  // ALTERNATIVES
  const altList = $("altList");
  if (altList && top_candidates) {
    altList.innerHTML = top_candidates.map((cand, idx) => {
      const isTop = idx === 0;
      const ce = cand.economics || {};
      return `
        <div class="alt-item${isTop ? " alt-item--top" : ""}">
          <div class="alt-item__rank">${isTop ? "🏆" : `#${idx + 1}`}</div>
          <div class="alt-item__info">
            <div class="alt-item__name">${escHtml((cand.metadata?.emoji || "🌱") + " " + cand.crop_display)}</div>
            <div class="alt-item__sci">${escHtml(cand.metadata?.scientific || "")}</div>
            <div class="alt-confidence-bar">
              <div class="alt-bar-fill" style="width:${cand.confidence_pct}%"></div>
            </div>
            <div class="alt-conf-val">${cand.confidence_pct}% confidence</div>
          </div>
          <div class="alt-item__eco">
            <div class="alt-eco-val">₹${formatNum(ce.total_estimated_investment)}</div>
            <div class="alt-eco-label">Est. Investment</div>
          </div>
        </div>
      `;
    }).join("");
  }

  // Show results section
  const resultsSection = $("resultsSection");
  if (resultsSection) {
    resultsSection.style.display = "";
    setTimeout(() => {
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }
}

function renderEconomics(eco, inputs) {
  const ecoCosts = $("ecoCosts");
  if (ecoCosts) {
    ecoCosts.innerHTML = `
      <div class="eco-cost-row">
        <span class="eco-cost-label">Seed Cost</span>
        <span class="eco-cost-val">₹ ${formatNum(eco.total_seed_cost)}</span>
      </div>
      <div class="eco-cost-row">
        <span class="eco-cost-label">Fertilizer & Inputs</span>
        <span class="eco-cost-val">₹ ${formatNum(eco.total_fertilizer_cost)}</span>
      </div>
      <div class="eco-cost-row">
        <span class="eco-cost-label">Cultivation & Labor</span>
        <span class="eco-cost-val">₹ ${formatNum(eco.total_cultivation_cost)}</span>
      </div>
      <div class="eco-cost-row highlight">
        <span class="eco-cost-label">Total Investment</span>
        <span class="eco-cost-val">₹ ${formatNum(eco.total_estimated_investment)}</span>
      </div>
    `;
  }

  // Budget bar
  const ecoBudgetBar = $("ecoBudgetBar");
  if (ecoBudgetBar && eco.total_estimated_investment && inputs.user_budget) {
    const pct = Math.min(100, (eco.total_estimated_investment / inputs.user_budget) * 100).toFixed(1);
    const color = eco.is_sufficient ? "var(--green)" : "var(--red)";
    ecoBudgetBar.innerHTML = `
      <div class="eco-budget-bar-label">
        <span>Investment vs Budget</span>
        <span>${pct}% of budget</span>
      </div>
      <div style="height:8px;background:rgba(255,255,255,0.08);border-radius:4px;overflow:hidden;">
        <div style="height:100%;width:${pct}%;background:${color};border-radius:4px;transition:width 0.8s ease;"></div>
      </div>
    `;
  }

  // Revenue
  const ecoRevenue = $("ecoRevenue");
  if (ecoRevenue && eco.estimated_revenue) {
    const profit = (eco.estimated_revenue - eco.total_estimated_investment) || 0;
    ecoRevenue.innerHTML = `
      <div class="eco-cost-row">
        <span class="eco-cost-label">Estimated Revenue</span>
        <span class="eco-cost-val" style="color:var(--green)">₹ ${formatNum(eco.estimated_revenue)}</span>
      </div>
      <div class="eco-cost-row">
        <span class="eco-cost-label">Net Profit Estimate</span>
        <span class="eco-cost-val" style="color:${profit >= 0 ? "var(--green)" : "var(--red)"}">₹ ${formatNum(Math.abs(profit))} ${profit >= 0 ? "profit" : "loss"}</span>
      </div>
    `;
  }

  // Method badge
  const ecoMethodBadge = $("ecoMethodBadge");
  if (ecoMethodBadge) {
    const isOrganic = inputs.farming_method === "organic";
    ecoMethodBadge.textContent = isOrganic ? "🌿 Organic Farming" : "⚗️ Regular Farming";
    ecoMethodBadge.style.cssText = isOrganic
      ? "background:rgba(34,197,94,0.1);border-color:rgba(34,197,94,0.3);color:var(--green);"
      : "background:rgba(6,182,212,0.1);border-color:rgba(6,182,212,0.3);color:var(--cyan);";
  }

  // Eco sub
  const ecoSub = $("ecoSub");
  if (ecoSub) ecoSub.textContent = `${inputs.farm_acres} Acres · ${inputs.district}, ${inputs.state}`;
}

// ─── RADAR CHART ─────────────────────────────────────────────────────────────
function drawRadarChart(features) {
  const canvas = $("radarCanvas");
  if (!canvas || !features.length) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const R = Math.min(W, H) / 2 - 30;
  const n = features.length;

  ctx.clearRect(0, 0, W, H);

  // Web rings
  for (let ring = 1; ring <= 4; ring++) {
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
      const r = (ring / 4) * R;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = "rgba(255,255,255,0.06)";
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // Spokes
  features.forEach((_, i) => {
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + R * Math.cos(angle), cy + R * Math.sin(angle));
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 1;
    ctx.stroke();
  });

  // Data polygon
  ctx.beginPath();
  features.forEach((f, i) => {
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    const pct = (f.alignment_pct || 0) / 100;
    const x = cx + R * pct * Math.cos(angle);
    const y = cy + R * pct * Math.sin(angle);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = "rgba(34,197,94,0.15)";
  ctx.fill();
  ctx.strokeStyle = "rgba(34,197,94,0.8)";
  ctx.lineWidth = 2;
  ctx.stroke();

  // Data points
  features.forEach((f, i) => {
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    const pct = (f.alignment_pct || 0) / 100;
    const x = cx + R * pct * Math.cos(angle);
    const y = cy + R * pct * Math.sin(angle);
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fillStyle = f.within_range ? "#22c55e" : "#f59e0b";
    ctx.fill();
  });

  // Labels
  ctx.font = "bold 9px 'Outfit', sans-serif";
  ctx.fillStyle = "rgba(240,253,244,0.6)";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  features.forEach((f, i) => {
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    const lR = R + 18;
    const x = cx + lR * Math.cos(angle);
    const y = cy + lR * Math.sin(angle);
    ctx.fillText(f.feature, x, y);
  });
}

// ─── TECH PANEL ──────────────────────────────────────────────────────────────
function populateTechMetrics() {
  const m    = STATE.metrics;
  const grid = $("techMetrics");
  const mGrid = $("meteoTechMetrics");

  const renderGrid = (el) => {
    if (!el) return;
    if (!m) {
      el.innerHTML = `<p style="color:var(--text-4);font-size:.85rem">Run <code>python src/train_model.py</code> to generate metrics.</p>`;
      return;
    }
    const metrics = [
      { label: "Test Accuracy",        value: `${(m.accuracy * 100).toFixed(2)}%` },
      { label: "Precision (Weighted)", value: `${(m.precision_weighted * 100).toFixed(2)}%` },
      { label: "Recall (Weighted)",    value: `${(m.recall_weighted * 100).toFixed(2)}%` },
      { label: "F1-Score (Weighted)",  value: `${(m.f1_score_weighted * 100).toFixed(2)}%` },
    ];
    el.innerHTML = metrics.map(mt =>
      `<div class="tech-metric">
         <div class="tech-metric__label">${mt.label}</div>
         <div class="tech-metric__value">${mt.value}</div>
       </div>`
    ).join("");
  };

  renderGrid(grid);
  renderGrid(mGrid);
}

async function loadConfusionMatrix() {
  const cmLoader   = $("cmLoader");
  const confMatrix = $("confMatrix");
  const mCmLoader  = $("mCmLoader");
  const mConfMatrix = $("mConfMatrix");

  const load = async (loader, img) => {
    if (!img) return;
    try {
      const res = await fetch("/api/confusion_matrix");
      if (!res.ok) throw new Error("Not found");
      const { image_base64, mime } = await res.json();
      img.src = `data:${mime};base64,${image_base64}`;
      img.classList.remove("hidden");
      if (loader) loader.classList.add("hidden");
    } catch {
      if (loader) loader.innerHTML = `<span style="color:var(--text-4);font-size:.82rem">Run <code>python src/train_model.py</code> first.</span>`;
    }
  };

  await load(cmLoader, confMatrix);
  await load(mCmLoader, mConfMatrix);
}

function toggleTechPanel() {
  const techBody   = $("techBody");
  const techArrow  = $("techArrow");
  const techToggle = $("techToggle");
  if (!techBody) return;
  const isOpen = techBody.classList.contains("hidden");
  techBody.classList.toggle("hidden");
  techArrow?.classList.toggle("toggle-arrow--open", isOpen);
  techToggle?.setAttribute("aria-expanded", String(isOpen));
  if (isOpen) loadConfusionMatrix();
}

// ─── PREDICTION ERROR ────────────────────────────────────────────────────────
function showPredictionError(msg) {
  const resultsSection = $("resultsSection");
  const verifyBanner   = $("verifyBanner");
  if (resultsSection) resultsSection.style.display = "";
  if (verifyBanner) {
    verifyBanner.innerHTML = `<strong style="color:#dc2626">❌ ${escHtml(msg)}</strong>
      <span style="font-size:.82rem;margin-left:.5rem">Please verify inputs or ensure backend is running.</span>`;
  }
  if (resultsSection) resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ─── UTILITIES ───────────────────────────────────────────────────────────────
function numOr(val, def) {
  if (val == null) return def;
  const n = parseFloat(val);
  return isNaN(n) ? def : n;
}

function formatNum(n) {
  if (n == null || isNaN(n)) return "—";
  return Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function escHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── BOOTSTRAP ───────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initLoginCanvas();
  setupLoginScreen();
});
