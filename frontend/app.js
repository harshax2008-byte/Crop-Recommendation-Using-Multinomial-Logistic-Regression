/**
 * AgroSense AI — Premium Frontend Application Logic v4.0
 * Role-based: Farmer (view) | Meteorologist (edit dataset)
 * Vanilla JavaScript | Fetch API | Dynamic DOM rendering
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// SESSION STATE
// ─────────────────────────────────────────────────────────────────────────────
const SESSION = {
  token:    null,
  role:     null,   // 'farmer' | 'meteorologist'
  name:     null,
  username: null
};

const STATE = {
  statesDistricts: {},
  presets: {},
  metrics: null,
  activePreset: null,
  currentSoilData: null   // data loaded from dataset for current district
};

// ─────────────────────────────────────────────────────────────────────────────
// DOM REFS (lazy — resolved after login when app is visible)
// ─────────────────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ─────────────────────────────────────────────────────────────────────────────
// ════════════════════════ AUTH / LOGIN ════════════════════════
// ─────────────────────────────────────────────────────────────────────────────

function setupLoginScreen() {
  const loginScreen  = $("loginScreen");
  const appContainer = $("appContainer");
  const roleFarmer   = $("roleFarmer");
  const roleMeteo    = $("roleMeteo");
  const loginUser    = $("loginUser");
  const loginPass    = $("loginPass");
  const loginBtn     = $("loginBtn");
  const loginError   = $("loginError");
  const logoutBtn    = $("logoutBtn");
  const demoFarmer   = $("demoFarmer");
  const demoMeteo    = $("demoMeteo");

  // Role toggle
  let selectedRole = "farmer";
  function selectRole(role) {
    selectedRole = role;
    roleFarmer.classList.toggle("active", role === "farmer");
    roleMeteo.classList.toggle("active",  role === "meteorologist");
  }
  roleFarmer.addEventListener("click", () => selectRole("farmer"));
  roleMeteo.addEventListener("click",  () => selectRole("meteorologist"));

  // Clickable demo chips for instant testing
  if (demoFarmer) {
    demoFarmer.addEventListener("click", () => {
      selectRole("farmer");
      loginUser.value = "farmer";
      loginPass.value = "farmer123";
      loginError.classList.add("hidden");
    });
  }
  if (demoMeteo) {
    demoMeteo.addEventListener("click", () => {
      selectRole("meteorologist");
      loginUser.value = "meteo";
      loginPass.value = "meteo123";
      loginError.classList.add("hidden");
    });
  }

  // Enter key triggers login
  [loginUser, loginPass].forEach(el => {
    el.addEventListener("keydown", e => { if (e.key === "Enter") loginBtn.click(); });
  });

  // LOGIN
  loginBtn.addEventListener("click", async () => {
    const username = loginUser.value.trim();
    const password = loginPass.value;
    loginError.classList.add("hidden");
    loginError.textContent = "";

    if (!username || !password) {
      showLoginError("Please enter both username and password.");
      return;
    }

    loginBtn.disabled = true;
    loginBtn.querySelector(".login-btn__text").textContent = "Signing in…";

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Invalid credentials");

      // Seamless role alignment if user selected different role tab
      if (data.role !== selectedRole) {
        selectRole(data.role);
      }

      // Store session
      SESSION.token    = data.token;
      SESSION.role     = data.role;
      SESSION.name     = data.name;
      SESSION.username = data.username;

      // Transition to app
      loginScreen.classList.add("login-screen--out");
      setTimeout(() => {
        loginScreen.classList.add("hidden");
        appContainer.classList.remove("hidden");
        appContainer.classList.add("app-entering");
        setTimeout(() => appContainer.classList.remove("app-entering"), 600);
        initApp();
      }, 350);

    } catch (err) {
      showLoginError(err.message);
    } finally {
      loginBtn.disabled = false;
      loginBtn.querySelector(".login-btn__text").textContent = "Sign In to Dashboard";
    }
  });

  function showLoginError(msg) {
    loginError.textContent = "⚠ " + msg;
    loginError.classList.remove("hidden");
    loginError.classList.add("shake");
    setTimeout(() => loginError.classList.remove("shake"), 500);
  }

  // LOGOUT
  logoutBtn.addEventListener("click", async () => {
    if (SESSION.token) {
      await fetch("/api/logout", {
        method: "POST",
        headers: { Authorization: "Bearer " + SESSION.token }
      }).catch(() => {});
    }
    SESSION.token = SESSION.role = SESSION.name = SESSION.username = null;
    appContainer.classList.add("hidden");
    loginScreen.classList.remove("hidden", "login-screen--out");
    loginUser.value = "";
    loginPass.value = "";
    $("loginError").classList.add("hidden");
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// ════════════════════════ APP INIT (after login) ════════════════════════
// ─────────────────────────────────────────────────────────────────────────────
// ════════════════════════ APP INIT (after login) ════════════════════════
// ─────────────────────────────────────────────────────────────────────────────
let _listenersWired = false;

function wireEventListenersOnce() {
  if (_listenersWired) return;
  _listenersWired = true;

  // 1. Synced input pairs (range + number)
  wireSyncedPair($("farmAcresRange"), $("farmAcres"), updateFarmSummary);
  wireSyncedPair($("tempRange"), $("tempInput"), null);
  wireSyncedPair($("humRange"),  $("humInput"),  null);
  wireSyncedPair($("rainRange"), $("rainInput"), null);
  wireSyncedPair($("nRange"), $("nInput"), null);
  wireSyncedPair($("pRange"), $("pInput"), null);
  wireSyncedPair($("kRange"), $("kInput"), null);

  if ($("phRange")) {
    $("phRange").addEventListener("input", updatePh);
  }
  if ($("userBudget")) {
    $("userBudget").addEventListener("input", updateFarmSummary);
  }

  // 2. State & district change handlers
  $("stateSelect").addEventListener("change", () => {
    populateDistricts($("stateSelect").value);
    updateLocationBadge();
    loadSoilForDistrict(false);
  });
  $("districtSelect").addEventListener("change", () => {
    updateLocationBadge();
    loadSoilForDistrict(false);
  });

  // 3. Action buttons
  $("predictBtn").addEventListener("click", runPrediction);
  $("techToggle").addEventListener("click", toggleTechPanel);

  const saveBtn = $("saveSoilBtn");
  if (saveBtn) {
    saveBtn.addEventListener("click", saveSoilData);
  }
}

async function initApp() {
  // Set nav role badge + name
  const navBadge = $("navRoleBadge");
  const navName  = $("navUserName");
  if (SESSION.role === "meteorologist") {
    navBadge.textContent = "🔬 Meteorologist";
    navBadge.className = "topnav__role-badge topnav__role-badge--meteo";
  } else {
    navBadge.textContent = "👨‍🌾 Farmer";
    navBadge.className = "topnav__role-badge topnav__role-badge--farmer";
  }
  navName.textContent = SESSION.name || SESSION.username;

  // Show/hide role-specific elements
  applyRoleVisibility();

  // Wire interactive listeners once
  wireEventListenersOnce();

  // 1. Fetch metadata
  try {
    const res = await fetch("/api/metadata");
    const data = await res.json();
    STATE.statesDistricts = data.states_districts || {};
    STATE.presets = data.presets || {};
    STATE.metrics = data.model_metrics || null;
    populateStates();
    populatePresets();
    populateTechMetrics();
  } catch (err) {
    console.error("Failed to load metadata:", err);
  }

  // Init UI fills & summary
  updateAllSliderFills();
  if (SESSION.role === "meteorologist") updatePh();
  updateFarmSummary();
}

// ─────────────────────────────────────────────────────────────────────────────
// ROLE VISIBILITY
// ─────────────────────────────────────────────────────────────────────────────
function applyRoleVisibility() {
  const isMeteo = SESSION.role === "meteorologist";

  document.querySelectorAll(".meteo-only").forEach(el => {
    el.classList.toggle("hidden", !isMeteo);
  });
  document.querySelectorAll(".farmer-only").forEach(el => {
    el.classList.toggle("hidden", isMeteo);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SOIL & CLIMATE DATA — Load for current district
// ─────────────────────────────────────────────────────────────────────────────
async function loadSoilForDistrict(skipFieldPopulation = false) {
  const state    = $("stateSelect").value;
  const district = $("districtSelect").value;
  if (!state || !district) return;

  if (SESSION.role === "farmer") {
    const loadingEl = $("soilLoading");
    const tilesEl   = $("soilTiles");
    if (loadingEl) loadingEl.classList.remove("hidden");
    if (tilesEl)   tilesEl.style.opacity = "0.3";
  }

  try {
    const res = await fetch(`/api/soil-data?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`);
    const json = await res.json();
    STATE.currentSoilData = json.data;

    if (SESSION.role === "farmer") {
      renderSoilTiles(json.data, json.found);
      const sourceEl = $("soilSource");
      if (sourceEl) {
        sourceEl.textContent = json.found
          ? `📌 Data source: District Soil Survey — ${district}, ${state}`
          : `⚠ No survey data for ${district}. Showing regional baseline defaults.`;
      }
      // Populate climate inputs with district baseline
      if (!skipFieldPopulation && json.data) {
        if (json.data.temperature != null) setSliderAndInput($("tempRange"), $("tempInput"), json.data.temperature);
        if (json.data.humidity != null)    setSliderAndInput($("humRange"),  $("humInput"),  json.data.humidity);
        if (json.data.rainfall != null)    setSliderAndInput($("rainRange"), $("rainInput"), json.data.rainfall);
      }
    } else {
      // Meteorologist: populate editable soil + climate parameters
      if (!skipFieldPopulation) {
        populateSoilEditFields(json.data);
      }
    }
  } catch (err) {
    console.error("Failed to load soil data:", err);
  } finally {
    if (SESSION.role === "farmer") {
      const loadingEl = $("soilLoading");
      const tilesEl   = $("soilTiles");
      if (loadingEl) loadingEl.classList.add("hidden");
      if (tilesEl)   tilesEl.style.opacity = "1";
    }
  }
}

function renderSoilTiles(data, found) {
  if (!data) return;
  // N
  const soilN = $("soilN"); const soilNBar = $("soilNBar");
  if (soilN) soilN.textContent = data.n != null ? Number(data.n).toFixed(1) : "—";
  if (soilNBar) soilNBar.style.width = data.n != null ? `${Math.min(100, (data.n / 150) * 100).toFixed(1)}%` : "0%";
  // P
  const soilP = $("soilP"); const soilPBar = $("soilPBar");
  if (soilP) soilP.textContent = data.p != null ? Number(data.p).toFixed(1) : "—";
  if (soilPBar) soilPBar.style.width = data.p != null ? `${Math.min(100, (data.p / 150) * 100).toFixed(1)}%` : "0%";
  // K
  const soilK = $("soilK"); const soilKBar = $("soilKBar");
  if (soilK) soilK.textContent = data.k != null ? Number(data.k).toFixed(1) : "—";
  if (soilKBar) soilKBar.style.width = data.k != null ? `${Math.min(100, (data.k / 210) * 100).toFixed(1)}%` : "0%";
  // pH
  const soilPH = $("soilPH");
  if (soilPH) {
    const ph = data.ph != null ? Number(data.ph) : 7.0;
    soilPH.textContent = ph.toFixed(2);
    let phColor = "#22c55e";
    if (ph < 5.5)      phColor = "#ef4444";
    else if (ph < 6.0) phColor = "#f97316";
    else if (ph < 6.5) phColor = "#eab308";
    else if (ph < 7.5) phColor = "#22c55e";
    else if (ph < 8.5) phColor = "#3b82f6";
    else               phColor = "#8b5cf6";
    soilPH.style.color = phColor;
  }
}

function populateSoilEditFields(data) {
  if (!data) return;
  if (data.n != null) setSliderAndInput($("nRange"), $("nInput"), data.n);
  if (data.p != null) setSliderAndInput($("pRange"), $("pInput"), data.p);
  if (data.k != null) setSliderAndInput($("kRange"), $("kInput"), data.k);
  if (data.ph != null && $("phRange")) {
    $("phRange").value = data.ph;
    updatePh();
  }
  if (data.temperature != null) setSliderAndInput($("tempRange"), $("tempInput"), data.temperature);
  if (data.humidity != null)    setSliderAndInput($("humRange"),  $("humInput"),  data.humidity);
  if (data.rainfall != null)    setSliderAndInput($("rainRange"), $("rainInput"), data.rainfall);
  updateAllSliderFills();
}

// ─────────────────────────────────────────────────────────────────────────────
// SAVE SOIL DATA (meteorologist)
// ─────────────────────────────────────────────────────────────────────────────
async function saveSoilData() {
  const saveBtn    = $("saveSoilBtn");
  const saveStatus = $("saveStatus");
  const state      = $("stateSelect").value;
  const district   = $("districtSelect").value;

  if (!state || !district) {
    showSaveStatus("❌ Please select a state and district first.", "error");
    return;
  }

  const payload = {
    state,
    district,
    n:           numOr($("nInput")?.value, 50),
    p:           numOr($("pInput")?.value, 50),
    k:           numOr($("kInput")?.value, 50),
    ph:          numOr($("phRange")?.value, 6.5),
    temperature: numOr($("tempInput")?.value, 25),
    humidity:    numOr($("humInput")?.value, 70),
    rainfall:    numOr($("rainInput")?.value, 100),
  };

  saveBtn.disabled = true;
  saveBtn.innerHTML = `<div class="spinner spinner--sm"></div> Saving…`;

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
    if (!res.ok) {
      let msg = "Save failed";
      if (typeof json.detail === "string") msg = json.detail;
      else if (Array.isArray(json.detail)) msg = json.detail.map(d => d.msg || JSON.stringify(d)).join("; ");
      throw new Error(msg);
    }
    showSaveStatus(`✅ Soil & climate data updated for ${district}, ${state}`, "success");
    STATE.currentSoilData = json.data;
  } catch (err) {
    showSaveStatus(`❌ ${err.message}`, "error");
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = `
      <svg viewBox="0 0 20 20" fill="currentColor"><path d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L9 12.586l7.293-7.293a1 1 0 011.414 1.414l-8 8z"/></svg>
      Save Soil Data to District Dataset
    `;
  }
}

function showSaveStatus(msg, type) {
  const el = $("saveStatus");
  if (!el) return;
  el.textContent = msg;
  el.className = `save-status save-status--${type}`;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 4500);
}

// ─────────────────────────────────────────────────────────────────────────────
// STATES & DISTRICTS
// ─────────────────────────────────────────────────────────────────────────────
function populateStates() {
  const stateSelect = $("stateSelect");
  const states = Object.keys(STATE.statesDistricts).sort();
  stateSelect.innerHTML = states.map(s =>
    `<option value="${s}"${s === "Punjab" ? " selected" : ""}>${s}</option>`
  ).join("");
  populateDistricts(stateSelect.value);
  updateLocationBadge();
  loadSoilForDistrict(false);
}

function populateDistricts(state) {
  const districtSelect = $("districtSelect");
  const districts = STATE.statesDistricts[state] || [];
  districtSelect.innerHTML = districts.map(d =>
    `<option value="${d}">${d}</option>`
  ).join("") || "<option>No districts</option>";
}

function updateLocationBadge() {
  const s = $("stateSelect").value;
  const d = $("districtSelect").value;
  const badge = $("locationBadgeText");
  if (s && d && badge) {
    badge.textContent = `Selected Region: ${d}, ${s} · Localized cost benchmarks active.`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PRESETS (meteo only — they can set from presets to edit and save)
// ─────────────────────────────────────────────────────────────────────────────
function populatePresets() {
  const presetGrid = $("presetGrid");
  if (!presetGrid) return;
  const presets = STATE.presets;
  if (!Object.keys(presets).length) {
    presetGrid.innerHTML = "<p style='color:#64748b;font-size:0.85rem'>No presets available.</p>";
    return;
  }
  presetGrid.innerHTML = Object.entries(presets).map(([label, data]) =>
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
  btnEl.classList.add("active");
  STATE.activePreset = label;

  $("stateSelect").value = p.state;
  populateDistricts(p.state);
  $("districtSelect").value = p.district;
  updateLocationBadge();

  setSliderAndInput($("farmAcresRange"), $("farmAcres"), p.acres);
  if ($("userBudget")) $("userBudget").value = p.budget;

  if (SESSION.role === "meteorologist") {
    setSliderAndInput($("nRange"), $("nInput"), p.n);
    setSliderAndInput($("pRange"), $("pInput"), p.p);
    setSliderAndInput($("kRange"), $("kInput"), p.k);
    if ($("phRange")) {
      $("phRange").value = p.ph;
      updatePh();
    }
  }

  setSliderAndInput($("tempRange"), $("tempInput"), p.temp);
  setSliderAndInput($("humRange"),  $("humInput"),  p.hum);
  setSliderAndInput($("rainRange"), $("rainInput"), p.rain);

  updateAllSliderFills();
  updateFarmSummary();

  // Load soil survey in background without overwriting preset fields
  loadSoilForDistrict(true);
}

// ─────────────────────────────────────────────────────────────────────────────
// SYNCED INPUTS
// ─────────────────────────────────────────────────────────────────────────────
function wireSyncedPair(rangeEl, numEl, callback) {
  if (!rangeEl || !numEl) return;
  const min = parseFloat(rangeEl.min) || 0;
  const max = parseFloat(rangeEl.max) || 100;

  rangeEl.addEventListener("input", () => {
    numEl.value = rangeEl.value;
    updateSliderFill(rangeEl);
    if (callback) callback();
  });

  numEl.addEventListener("input", () => {
    let v = parseFloat(numEl.value);
    if (!isNaN(v)) {
      v = Math.min(max, Math.max(min, v));
      rangeEl.value = v;
      updateSliderFill(rangeEl);
    }
    if (callback) callback();
  });

  numEl.addEventListener("change", () => {
    let v = parseFloat(numEl.value);
    if (isNaN(v)) v = min;
    v = Math.min(max, Math.max(min, v));
    numEl.value = v;
    rangeEl.value = v;
    updateSliderFill(rangeEl);
    if (callback) callback();
  });
}

function setSliderAndInput(rangeEl, numEl, val) {
  if (!rangeEl || !numEl || val == null) return;
  const numVal = parseFloat(val);
  numEl.value = numVal;
  rangeEl.value = Math.min(parseFloat(rangeEl.max), Math.max(parseFloat(rangeEl.min), numVal));
  updateSliderFill(rangeEl);
}

function updateSliderFill(rangeEl) {
  if (!rangeEl) return;
  const min = parseFloat(rangeEl.min) || 0;
  const max = parseFloat(rangeEl.max) || 100;
  const val = parseFloat(rangeEl.value) || 0;
  const pct = Math.max(0, Math.min(100, ((val - min) / (max - min)) * 100));
  rangeEl.style.setProperty("--pct", `${pct.toFixed(1)}%`);
}

function updateAllSliderFills() {
  [
    $("farmAcresRange"), $("nRange"), $("pRange"), $("kRange"),
    $("tempRange"), $("humRange"), $("rainRange"), $("phRange")
  ].forEach(updateSliderFill);
}

// ─────────────────────────────────────────────────────────────────────────────
// PH DISPLAY
// ─────────────────────────────────────────────────────────────────────────────
function updatePh() {
  const phRange = $("phRange");
  if (!phRange) return;
  const v = parseFloat(phRange.value);
  const phDisplay = $("phDisplay");
  if (phDisplay) phDisplay.textContent = v.toFixed(2);
  updateSliderFill(phRange);

  let tag = "Neutral";
  let tagStyle = "background:#d1fae5;color:#065f46";
  if (v < 5.5)       { tag = "Strongly Acidic";     tagStyle = "background:#fee2e2;color:#991b1b"; }
  else if (v < 6.0)  { tag = "Moderately Acidic";   tagStyle = "background:#fef3c7;color:#92400e"; }
  else if (v < 6.5)  { tag = "Slightly Acidic";     tagStyle = "background:#fef9c3;color:#854d0e"; }
  else if (v < 7.0)  { tag = "Near Neutral";        tagStyle = "background:#d1fae5;color:#065f46"; }
  else if (v < 7.5)  { tag = "Neutral";             tagStyle = "background:#d1fae5;color:#065f46"; }
  else if (v < 8.0)  { tag = "Slightly Alkaline";   tagStyle = "background:#e0e7ff;color:#3730a3"; }
  else if (v < 9.0)  { tag = "Moderately Alkaline"; tagStyle = "background:#ddd6fe;color:#5b21b6"; }
  else               { tag = "Strongly Alkaline";   tagStyle = "background:#f3e8ff;color:#6b21a8"; }

  const phTag = $("phTag");
  if (phTag) {
    phTag.textContent = tag;
    phTag.setAttribute("style", `${tagStyle};padding:.1rem .5rem;border-radius:9999px;font-size:.72rem;font-weight:700;`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// FARM SUMMARY
// ─────────────────────────────────────────────────────────────────────────────
function updateFarmSummary() {
  const sa = $("summaryAcres");
  const sb = $("summaryBudget");
  const fa = $("farmAcres");
  const ub = $("userBudget");
  if (sa && fa) sa.textContent = numOr(fa.value, 2.5).toFixed(2);
  if (sb && ub) sb.textContent = "₹" + formatNum(numOr(ub.value, 60000));
}

// Helper: safe numeric parsing without NaN or 0 falsy bugs
function numOr(val, defaultVal) {
  if (val == null) return defaultVal;
  const num = parseFloat(val);
  return isNaN(num) ? defaultVal : num;
}

// ─────────────────────────────────────────────────────────────────────────────
// PREDICT
// ─────────────────────────────────────────────────────────────────────────────
async function runPrediction() {
  const soil = STATE.currentSoilData || { n: 50, p: 50, k: 50, ph: 6.5 };

  let n, p, k, ph;
  if (SESSION.role === "farmer") {
    n  = numOr(soil.n, 50);
    p  = numOr(soil.p, 50);
    k  = numOr(soil.k, 50);
    ph = numOr(soil.ph, 6.5);
  } else {
    n  = numOr($("nInput")?.value, 50);
    p  = numOr($("pInput")?.value, 50);
    k  = numOr($("kInput")?.value, 50);
    ph = numOr($("phRange")?.value, 6.5);
  }

  const payload = {
    n, p, k, ph,
    temperature: numOr($("tempInput")?.value, 25),
    humidity:    numOr($("humInput")?.value, 70),
    rainfall:    numOr($("rainInput")?.value, 100),
    farm_acres:  numOr($("farmAcres")?.value, 2.5),
    user_budget: numOr($("userBudget")?.value, 60000),
    state:       $("stateSelect").value  || "Punjab",
    district:    $("districtSelect").value || "Ludhiana"
  };

  const loadingOverlay = $("loadingOverlay");
  const resultsSection = $("resultsSection");
  const predictBtn     = $("predictBtn");

  loadingOverlay.classList.remove("hidden");
  resultsSection.classList.add("hidden");
  predictBtn.disabled = true;
  predictBtn.style.opacity = "0.7";

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(SESSION.token ? { "Authorization": "Bearer " + SESSION.token } : {})
      },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      let msg = "Prediction failed";
      if (typeof errData.detail === "string") {
        msg = errData.detail;
      } else if (Array.isArray(errData.detail)) {
        msg = errData.detail.map(d => d.msg || JSON.stringify(d)).join("; ");
      } else if (errData.message) {
        msg = errData.message;
      }
      throw new Error(msg);
    }
    const data = await res.json();
    renderResults(data, payload);
  } catch (err) {
    showError(`Prediction failed: ${err.message}`);
  } finally {
    loadingOverlay.classList.add("hidden");
    predictBtn.disabled = false;
    predictBtn.style.opacity = "";
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// RENDER RESULTS
// ─────────────────────────────────────────────────────────────────────────────
function renderResults(data, inputs) {
  const { recommended_crop_display, confidence_pct, metadata, economics, top_candidates } = data;
  const eco = economics;

  const verifyBanner = $("verifyBanner");
  const recHero      = $("recHero");
  const recCropName  = $("recCropName");
  const ecoCard      = $("ecoCard");
  const altSection   = document.querySelector(".alternatives-section");

  // Ensure sections are visible after any previous error
  if (recHero)    recHero.style.display    = "";
  if (ecoCard)    ecoCard.style.display    = "";
  if (altSection) altSection.style.display = "";

  verifyBanner.innerHTML = `
    <strong>✅ ML Model Execution Successful</strong> &nbsp;·&nbsp;
    Evaluated Features:
    <strong>N: ${inputs.n}</strong> |
    <strong>P: ${inputs.p}</strong> |
    <strong>K: ${inputs.k}</strong> |
    <strong>Temp: ${inputs.temperature}°C</strong> |
    <strong>Humidity: ${inputs.humidity}%</strong> |
    <strong>pH: ${inputs.ph}</strong> |
    <strong>Rainfall: ${inputs.rainfall}mm</strong>
  `;

  recCropName.textContent = `${metadata.emoji || "🌱"} ${recommended_crop_display}`;
  $("recScientific").textContent = `${metadata.scientific || ""} · ${metadata.category || "Agricultural Crop"}`;
  $("recConfidencePill").innerHTML = `🎯 Model Confidence: <strong>${confidence_pct}%</strong> (Softmax)`;
  $("recDesc").textContent = metadata.desc || "Optimal conditions identified for high yield.";

  const circumference = 264;
  const offset = circumference - (confidence_pct / 100) * circumference;
  $("confRingFill").style.strokeDashoffset = offset;
  $("confRingLabel").textContent = `${confidence_pct}%`;

  const regionText = eco.is_prime_state
    ? `Highly Suitable in ${inputs.state}`
    : `Favorable in ${inputs.state}`;
  $("recMetricStrip").innerHTML = `
    <div class="strip-item">
      <div class="strip-label">Water Demand</div>
      <div class="strip-val">${metadata.water || "Moderate"}</div>
    </div>
    <div class="strip-item">
      <div class="strip-label">Growing Season</div>
      <div class="strip-val">${metadata.season || "Standard"}</div>
    </div>
    <div class="strip-item">
      <div class="strip-label">Regional Alignment</div>
      <div class="strip-val">${regionText}</div>
    </div>
  `;

  $("ecoCardSub").textContent =
    `Scale: ${inputs.farm_acres} Acres in ${inputs.district}, ${inputs.state} · Indicative Extension Benchmarks`;

  $("costGrid").innerHTML = `
    <div class="cost-box">
      <div class="cost-title">1. Estimated Seed Cost</div>
      <div class="cost-amount">₹ ${formatNum(eco.total_seed_cost)}</div>
      <div class="cost-sub">${eco.total_seed_qty} kg @ ₹${eco.seed_price_rate}/kg</div>
    </div>
    <div class="cost-box">
      <div class="cost-title">2. Fertilizer &amp; Inputs</div>
      <div class="cost-amount">₹ ${formatNum(eco.total_fertilizer_cost)}</div>
      <div class="cost-sub">NPK, micronutrients &amp; compost</div>
    </div>
    <div class="cost-box">
      <div class="cost-title">3. Cultivation &amp; Labor</div>
      <div class="cost-amount">₹ ${formatNum(eco.total_cultivation_cost)}</div>
      <div class="cost-sub">Land prep, sowing, irrigation &amp; harvest</div>
    </div>
    <div class="cost-box cost-box--highlight">
      <div class="cost-title">Total Estimated Investment</div>
      <div class="cost-amount">₹ ${formatNum(eco.total_estimated_investment)}</div>
      <div class="cost-sub">Full season operational cost</div>
    </div>
  `;

  const budgetBanner = $("budgetBanner");
  if (eco.is_sufficient) {
    budgetBanner.className = "budget-banner budget-banner--surplus";
    budgetBanner.innerHTML = `
      <div>
        <div class="banner-status" style="color:var(--c-emerald-700)">✓ BUDGET STATUS: SUFFICIENT CAPITAL</div>
        <div class="banner-amount" style="color:var(--c-emerald-900)">Remaining Surplus: ₹ ${formatNum(eco.budget_difference)}</div>
        <div class="banner-desc" style="color:var(--c-emerald-700)">
          Your available budget of <strong>₹ ${formatNum(inputs.user_budget)}</strong>
          comfortably covers the estimated expenditure of <strong>₹ ${formatNum(eco.total_estimated_investment)}</strong>.
        </div>
      </div>
      <div class="banner-emoji">🎉</div>
    `;
  } else {
    budgetBanner.className = "budget-banner budget-banner--deficit";
    budgetBanner.innerHTML = `
      <div>
        <div class="banner-status" style="color:var(--c-red-600)">⚠️ BUDGET STATUS: ADDITIONAL CAPITAL REQUIRED</div>
        <div class="banner-amount" style="color:var(--c-red-800)">Shortfall: ₹ ${formatNum(eco.budget_difference)}</div>
        <div class="banner-desc" style="color:#9f1239">
          Your available budget is <strong>₹ ${formatNum(inputs.user_budget)}</strong>.
          An additional <strong>₹ ${formatNum(eco.budget_difference)}</strong> is recommended.
        </div>
      </div>
      <div class="banner-emoji">📉</div>
    `;
  }

  $("altGrid").innerHTML = top_candidates.map((cand, idx) => {
    const isTop = idx === 0;
    const ce = cand.economics || {};
    return `
      <div class="alt-card${isTop ? " alt-card--top" : ""}">
        <div class="alt-card__badge">${isTop ? "🏆 Top Recommendation" : `Alternative Option #${idx + 1}`}</div>
        <div class="alt-card__name">${(cand.metadata?.emoji || "🌱") + " " + cand.crop_display}</div>
        <div class="alt-card__sci"><em>${cand.metadata?.scientific || ""}</em> · ${cand.metadata?.category || ""}</div>
        <div class="alt-confidence">Model Confidence: <strong>${cand.confidence_pct}%</strong></div>
        <div class="progress-bar-wrap">
          <div class="progress-bar" style="width: ${cand.confidence_pct}%"></div>
        </div>
        <hr class="alt-divider" />
        <div class="alt-eco">
          <strong>Est. Seed Cost:</strong> ₹ ${ce.total_seed_cost ? formatNum(ce.total_seed_cost) : "—"}<br/>
          <strong>Est. Total Investment:</strong> ₹ ${ce.total_estimated_investment ? formatNum(ce.total_estimated_investment) : "—"}
        </div>
      </div>
    `;
  }).join("");

  const resultsSection = $("resultsSection");
  resultsSection.classList.remove("hidden");
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ─────────────────────────────────────────────────────────────────────────────
// TECH PANEL
// ─────────────────────────────────────────────────────────────────────────────
function populateTechMetrics() {
  const m = STATE.metrics;
  const grid = $("techMetricsGrid");
  if (!grid) return;
  if (!m) {
    grid.innerHTML = `<p style="color:var(--c-slate-500);font-size:.85rem">Run <code>python src/train_model.py</code> to generate metrics.</p>`;
    return;
  }
  const metrics = [
    { label: "Test Accuracy",        value: `${(m.accuracy * 100).toFixed(2)}%` },
    { label: "Precision (Weighted)", value: `${(m.precision_weighted * 100).toFixed(2)}%` },
    { label: "Recall (Weighted)",    value: `${(m.recall_weighted * 100).toFixed(2)}%` },
    { label: "F1-Score (Weighted)",  value: `${(m.f1_score_weighted * 100).toFixed(2)}%` },
  ];
  grid.innerHTML = metrics.map(m =>
    `<div class="tech-metric">
       <div class="tech-metric__label">${m.label}</div>
       <div class="tech-metric__value">${m.value}</div>
     </div>`
  ).join("");
}

async function loadConfusionMatrix() {
  const cmLoader       = $("cmLoader");
  const confusionMatrix = $("confusionMatrix");
  try {
    const res = await fetch("/api/confusion_matrix");
    if (!res.ok) throw new Error("Not found");
    const { image_base64, mime } = await res.json();
    confusionMatrix.src = `data:${mime};base64,${image_base64}`;
    confusionMatrix.classList.remove("hidden");
    cmLoader.classList.add("hidden");
  } catch {
    cmLoader.innerHTML = `<span style="color:var(--c-slate-400);font-size:.82rem">Confusion matrix unavailable. Run <code>python src/train_model.py</code>.</span>`;
  }
}

function toggleTechPanel() {
  const techBody   = $("techBody");
  const techArrow  = $("techArrow");
  const techToggle = $("techToggle");
  const confusionMatrix = $("confusionMatrix");
  const isOpen = techBody.classList.contains("hidden");
  techBody.classList.toggle("hidden");
  techArrow.classList.toggle("toggle-arrow--open", isOpen);
  techToggle.setAttribute("aria-expanded", String(isOpen));
  if (isOpen && confusionMatrix && !confusionMatrix.src) {
    loadConfusionMatrix();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────────────────────────────────
function formatNum(n) {
  if (n == null || isNaN(n)) return "—";
  return Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function escHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function showError(msg) {
  const resultsSection = $("resultsSection");
  const verifyBanner   = $("verifyBanner");
  const recHero        = $("recHero");
  const ecoCard        = $("ecoCard");
  const altSection     = document.querySelector(".alternatives-section");
  resultsSection.classList.remove("hidden");
  verifyBanner.innerHTML = `<strong style="color:#dc2626">❌ ${escHtml(msg)}</strong>
    <span style="font-size:.82rem;margin-left:.5rem">Please verify inputs or ensure backend server is active.</span>`;
  if (recHero)    recHero.style.display    = "none";
  if (ecoCard)    ecoCard.style.display    = "none";
  if (altSection) altSection.style.display = "none";
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ─────────────────────────────────────────────────────────────────────────────
// BOOTSTRAP
// ─────────────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  setupLoginScreen();
});
