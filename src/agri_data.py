"""
AgroSense AI - Regional & Crop Economics Data Layer
Contains Indian State/District geographic structures, agronomic benchmarks,
seed pricing assumptions, and farm investment calculation models.
"""

from typing import Dict, Any, List, Tuple

# -------------------------------------------------------------------------
# INDIAN STATES & DISTRICTS MAPPING
# -------------------------------------------------------------------------
INDIAN_STATES_DISTRICTS: Dict[str, List[str]] = {
    "Andhra Pradesh": [
        "Guntur", "Krishna", "Kurnool", "East Godavari", "West Godavari", 
        "Anantapur", "Chittoor", "Visakhapatnam", "Nellore", "Prakasam"
    ],
    "Assam": [
        "Kamrup", "Nagaon", "Sonitpur", "Jorhat", "Dibrugarh", "Cachar", "Barpeta", "Tinsukia"
    ],
    "Bihar": [
        "Patna", "Nalanda", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga", "Rohtas", "Samastipur"
    ],
    "Gujarat": [
        "Ahmedabad", "Rajkot", "Surat", "Vadodara", "Junagadh", "Kutch", "Bhavnagar", "Mehsana", "Amreli"
    ],
    "Haryana": [
        "Karnal", "Hisar", "Ambala", "Sirsa", "Kurukshetra", "Rohtak", "Sonipat", "Fatehabad"
    ],
    "Himachal Pradesh": [
        "Shimla", "Kullu", "Kangra", "Mandi", "Solan", "Chamba", "Sirmaur", "Una"
    ],
    "Karnataka": [
        "Bengaluru Rural", "Mysuru", "Belagavi", "Dharwad", "Hassan", "Shivamogga", "Ballari", "Tumakuru", "Mandya"
    ],
    "Kerala": [
        "Wayanad", "Idukki", "Palakkad", "Alappuzha", "Kottayam", "Thrissur", "Kozhikode", "Malappuram"
    ],
    "Madhya Pradesh": [
        "Indore", "Bhopal", "Ujjain", "Jabalpur", "Narmadapuram", "Sehore", "Dewas", "Dhar", "Gwalior"
    ],
    "Maharashtra": [
        "Nashik", "Pune", "Nagpur", "Ahmednagar", "Jalgaon", "Kolhapur", "Solapur", "Satara", "Aurangabad", "Amravati"
    ],
    "Odisha": [
        "Cuttack", "Balasore", "Sambalpur", "Puri", "Ganjam", "Bhadrak", "Bargarh", "Khurda"
    ],
    "Punjab": [
        "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Firozpur", "Sangrur", "Hoshiarpur"
    ],
    "Rajasthan": [
        "Jaipur", "Jodhpur", "Kota", "Sri Ganganagar", "Bikaner", "Udaipur", "Alwar", "Nagaur", "Barmer"
    ],
    "Tamil Nadu": [
        "Thanjavur", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli", "Erode", "Tirunelveli", "Dindigul"
    ],
    "Telangana": [
        "Warangal", "Karimnagar", "Nalgonda", "Nizamabad", "Khammam", "Mahabubnagar", "Rangareddy", "Suryapet"
    ],
    "Uttar Pradesh": [
        "Varanasi", "Lucknow", "Kanpur", "Meerut", "Prayagraj", "Bareilly", "Agra", "Gorakhpur", "Aligarh", "Moradabad"
    ],
    "Uttarakhand": [
        "Dehradun", "Haridwar", "Nainital", "Udham Singh Nagar", "Tehri Garhwal", "Pauri Garhwal"
    ],
    "West Bengal": [
        "Purba Bardhaman", "Hooghly", "Murshidabad", "Nadia", "North 24 Parganas", "South 24 Parganas", "Bankura"
    ]
}

# -------------------------------------------------------------------------
# REGION → STATE MAPPING (6 geographic regions of India)
# -------------------------------------------------------------------------
INDIAN_REGIONS: Dict[str, List[str]] = {
    "North": ["Haryana", "Himachal Pradesh", "Punjab", "Uttarakhand", "Uttar Pradesh"],
    "South": ["Andhra Pradesh", "Karnataka", "Kerala", "Tamil Nadu", "Telangana"],
    "East": ["Bihar", "Odisha", "West Bengal", "Assam"],
    "West": ["Gujarat", "Maharashtra", "Rajasthan"],
    "Central": ["Madhya Pradesh"],
    "Northeast": ["Assam"]
}

# -------------------------------------------------------------------------
# STATE GEOGRAPHIC COORDINATES (lat, lon, zoom_level)
# Used for globe camera focus
# -------------------------------------------------------------------------
STATE_COORDINATES: Dict[str, Dict[str, Any]] = {
    "Andhra Pradesh":    {"lat": 15.9129, "lon": 79.7400, "zoom": 5.8},
    "Assam":             {"lat": 26.2006, "lon": 92.9376, "zoom": 6.0},
    "Bihar":             {"lat": 25.0961, "lon": 85.3131, "zoom": 6.0},
    "Gujarat":           {"lat": 22.2587, "lon": 71.1924, "zoom": 5.8},
    "Haryana":           {"lat": 29.0588, "lon": 76.0856, "zoom": 6.2},
    "Himachal Pradesh":  {"lat": 31.1048, "lon": 77.1734, "zoom": 6.0},
    "Karnataka":         {"lat": 15.3173, "lon": 75.7139, "zoom": 5.8},
    "Kerala":            {"lat": 10.8505, "lon": 76.2711, "zoom": 6.2},
    "Madhya Pradesh":    {"lat": 22.9734, "lon": 78.6569, "zoom": 5.5},
    "Maharashtra":       {"lat": 19.7515, "lon": 75.7139, "zoom": 5.5},
    "Odisha":            {"lat": 20.9517, "lon": 85.0985, "zoom": 6.0},
    "Punjab":            {"lat": 31.1471, "lon": 75.3412, "zoom": 6.2},
    "Rajasthan":         {"lat": 27.0238, "lon": 74.2179, "zoom": 5.5},
    "Tamil Nadu":        {"lat": 11.1271, "lon": 78.6569, "zoom": 5.8},
    "Telangana":         {"lat": 18.1124, "lon": 79.0193, "zoom": 6.0},
    "Uttar Pradesh":     {"lat": 26.8467, "lon": 80.9462, "zoom": 5.5},
    "Uttarakhand":       {"lat": 30.0668, "lon": 79.0193, "zoom": 6.2},
    "West Bengal":       {"lat": 22.9868, "lon": 87.8550, "zoom": 6.0}
}

# -------------------------------------------------------------------------
# CROP DATASET PROFILES — observed ranges from crop_recommendation.csv
# Used for "Why This Crop?" explanation feature
# Values derived from actual dataset statistics
# -------------------------------------------------------------------------
CROP_DATASET_PROFILES: Dict[str, Dict[str, Any]] = {
    "rice":        {"N": (60,130), "P": (30,70),  "K": (30,55),  "temperature": (20,28), "humidity": (75,95), "ph": (5.5,7.0), "rainfall": (150,260)},
    "maize":       {"N": (50,110), "P": (50,80),  "K": (15,30),  "temperature": (18,28), "humidity": (55,80), "ph": (5.5,7.5), "rainfall": (50,130)},
    "chickpea":    {"N": (30,55),  "P": (55,80),  "K": (65,100), "temperature": (14,25), "humidity": (10,30), "ph": (6.5,8.5), "rainfall": (55,105)},
    "kidneybeans": {"N": (15,25),  "P": (55,75),  "K": (15,25),  "temperature": (16,25), "humidity": (15,25), "ph": (5.5,7.0), "rainfall": (85,125)},
    "pigeonpeas":  {"N": (15,25),  "P": (65,80),  "K": (15,25),  "temperature": (27,36), "humidity": (40,65), "ph": (5.0,7.0), "rainfall": (120,165)},
    "mothbeans":   {"N": (15,25),  "P": (35,50),  "K": (25,40),  "temperature": (27,35), "humidity": (40,65), "ph": (3.5,7.0), "rainfall": (30,60)},
    "mungbean":    {"N": (15,25),  "P": (55,75),  "K": (15,25),  "temperature": (26,36), "humidity": (80,95), "ph": (5.5,7.5), "rainfall": (40,80)},
    "blackgram":   {"N": (30,45),  "P": (55,75),  "K": (15,25),  "temperature": (26,36), "humidity": (60,90), "ph": (5.5,7.5), "rainfall": (55,115)},
    "lentil":      {"N": (15,25),  "P": (55,75),  "K": (15,25),  "temperature": (14,26), "humidity": (50,75), "ph": (6.0,7.5), "rainfall": (30,60)},
    "pomegranate": {"N": (15,25),  "P": (15,25),  "K": (30,45),  "temperature": (20,30), "humidity": (85,95), "ph": (5.5,8.0), "rainfall": (100,150)},
    "banana":      {"N": (90,115), "P": (55,80),  "K": (45,65),  "temperature": (24,32), "humidity": (75,95), "ph": (5.5,7.0), "rainfall": (90,175)},
    "mango":       {"N": (15,25),  "P": (15,25),  "K": (25,45),  "temperature": (28,38), "humidity": (45,75), "ph": (4.5,7.0), "rainfall": (85,125)},
    "grapes":      {"N": (15,25),  "P": (15,25),  "K": (25,45),  "temperature": (8,22),  "humidity": (80,95), "ph": (5.5,7.0), "rainfall": (55,80)},
    "watermelon":  {"N": (95,115), "P": (15,25),  "K": (45,60),  "temperature": (24,32), "humidity": (80,95), "ph": (5.5,7.5), "rainfall": (40,65)},
    "muskmelon":   {"N": (95,115), "P": (15,25),  "K": (45,60),  "temperature": (26,34), "humidity": (88,98), "ph": (5.5,7.5), "rainfall": (20,55)},
    "apple":       {"N": (0,25),   "P": (110,155),"K": (195,210),"temperature": (20,26), "humidity": (88,98), "ph": (5.5,6.5), "rainfall": (98,130)},
    "orange":      {"N": (15,25),  "P": (15,25),  "K": (5,15),   "temperature": (10,22), "humidity": (88,98), "ph": (6.0,7.5), "rainfall": (100,140)},
    "papaya":      {"N": (40,60),  "P": (15,25),  "K": (35,50),  "temperature": (32,40), "humidity": (90,97), "ph": (6.0,7.5), "rainfall": (135,180)},
    "coconut":     {"N": (15,25),  "P": (15,25),  "K": (25,45),  "temperature": (25,35), "humidity": (85,97), "ph": (5.5,7.5), "rainfall": (130,200)},
    "cotton":      {"N": (105,135),"P": (40,50),  "K": (15,25),  "temperature": (22,32), "humidity": (70,88), "ph": (6.0,7.5), "rainfall": (70,115)},
    "jute":        {"N": (60,90),  "P": (45,60),  "K": (40,55),  "temperature": (24,30), "humidity": (70,90), "ph": (6.0,8.0), "rainfall": (155,250)},
    "coffee":      {"N": (95,115), "P": (25,35),  "K": (28,40),  "temperature": (24,30), "humidity": (55,70), "ph": (6.0,7.5), "rainfall": (140,180)},
}

# -------------------------------------------------------------------------
# CROP ECONOMICS & AGRONOMIC BENCHMARKS (PER ACRE)
# Indicative agricultural extension guidelines based on standard ICAR/State Agri Dept benchmarks.
# -------------------------------------------------------------------------
CROP_ECONOMICS: Dict[str, Dict[str, Any]] = {
    "rice": {
        "seed_rate_per_acre": 20.0,       # kg/acre
        "seed_price_per_kg": 45.0,        # INR/kg (Certified high-yielding variety)
        "fertilizer_per_acre": 4200.0,    # INR/acre (Urea, DAP, Potash, Zinc)
        "cultivation_per_acre": 11500.0,  # INR/acre (Puddling, transplanting, weeding, irrigation, harvesting)
        "avg_yield_quintal_acre": 22.0,   # Quintals/acre
        "maturity_days": "115 - 135 days",
        "key_states": ["West Bengal", "Punjab", "Uttar Pradesh", "Andhra Pradesh", "Tamil Nadu", "Odisha", "Bihar", "Assam"]
    },
    "maize": {
        "seed_rate_per_acre": 8.0,        # kg/acre (Hybrid seed)
        "seed_price_per_kg": 180.0,       # INR/kg
        "fertilizer_per_acre": 3800.0,
        "cultivation_per_acre": 8200.0,
        "avg_yield_quintal_acre": 25.0,
        "maturity_days": "90 - 110 days",
        "key_states": ["Karnataka", "Madhya Pradesh", "Bihar", "Tamil Nadu", "Telangana", "Maharashtra", "Rajasthan"]
    },
    "chickpea": {
        "seed_rate_per_acre": 30.0,       # kg/acre
        "seed_price_per_kg": 85.0,
        "fertilizer_per_acre": 2200.0,
        "cultivation_per_acre": 5500.0,
        "avg_yield_quintal_acre": 8.5,
        "maturity_days": "95 - 115 days",
        "key_states": ["Madhya Pradesh", "Maharashtra", "Rajasthan", "Karnataka", "Uttar Pradesh", "Gujarat"]
    },
    "kidneybeans": {
        "seed_rate_per_acre": 35.0,
        "seed_price_per_kg": 120.0,
        "fertilizer_per_acre": 2800.0,
        "cultivation_per_acre": 6200.0,
        "avg_yield_quintal_acre": 6.5,
        "maturity_days": "100 - 120 days",
        "key_states": ["Himachal Pradesh", "Uttarakhand", "Karnataka", "Maharashtra"]
    },
    "pigeonpeas": {
        "seed_rate_per_acre": 6.0,
        "seed_price_per_kg": 110.0,
        "fertilizer_per_acre": 2400.0,
        "cultivation_per_acre": 6000.0,
        "avg_yield_quintal_acre": 7.0,
        "maturity_days": "150 - 180 days",
        "key_states": ["Maharashtra", "Madhya Pradesh", "Karnataka", "Uttar Pradesh", "Gujarat", "Telangana"]
    },
    "mothbeans": {
        "seed_rate_per_acre": 5.0,
        "seed_price_per_kg": 90.0,
        "fertilizer_per_acre": 1200.0,
        "cultivation_per_acre": 3500.0,
        "avg_yield_quintal_acre": 4.5,
        "maturity_days": "75 - 90 days",
        "key_states": ["Rajasthan", "Gujarat", "Haryana", "Punjab"]
    },
    "mungbean": {
        "seed_rate_per_acre": 8.0,
        "seed_price_per_kg": 115.0,
        "fertilizer_per_acre": 1800.0,
        "cultivation_per_acre": 4200.0,
        "avg_yield_quintal_acre": 5.5,
        "maturity_days": "65 - 75 days",
        "key_states": ["Rajasthan", "Madhya Pradesh", "Maharashtra", "Karnataka", "Bihar", "Andhra Pradesh"]
    },
    "blackgram": {
        "seed_rate_per_acre": 9.0,
        "seed_price_per_kg": 105.0,
        "fertilizer_per_acre": 1900.0,
        "cultivation_per_acre": 4400.0,
        "avg_yield_quintal_acre": 5.0,
        "maturity_days": "75 - 85 days",
        "key_states": ["Madhya Pradesh", "Uttar Pradesh", "Andhra Pradesh", "Tamil Nadu", "Maharashtra"]
    },
    "lentil": {
        "seed_rate_per_acre": 15.0,
        "seed_price_per_kg": 95.0,
        "fertilizer_per_acre": 1800.0,
        "cultivation_per_acre": 4200.0,
        "avg_yield_quintal_acre": 6.0,
        "maturity_days": "110 - 130 days",
        "key_states": ["Uttar Pradesh", "Madhya Pradesh", "Bihar", "West Bengal", "Rajasthan"]
    },
    "pomegranate": {
        "seed_rate_per_acre": 300.0,      # plants/acre (Saplings)
        "seed_price_per_kg": 65.0,        # INR/sapling
        "fertilizer_per_acre": 12000.0,
        "cultivation_per_acre": 24000.0,
        "avg_yield_quintal_acre": 45.0,
        "maturity_days": "Perennial (18 mo first harvest)",
        "key_states": ["Maharashtra", "Gujarat", "Karnataka", "Andhra Pradesh", "Rajasthan"]
    },
    "banana": {
        "seed_rate_per_acre": 1000.0,     # suckers or tissue culture plantlets/acre
        "seed_price_per_kg": 16.0,        # INR/plantlet
        "fertilizer_per_acre": 16000.0,
        "cultivation_per_acre": 28000.0,
        "avg_yield_quintal_acre": 240.0,
        "maturity_days": "11 - 13 months",
        "key_states": ["Tamil Nadu", "Gujarat", "Maharashtra", "Andhra Pradesh", "Kerala", "Karnataka"]
    },
    "mango": {
        "seed_rate_per_acre": 70.0,       # grafted saplings/acre
        "seed_price_per_kg": 120.0,       # INR/grafted sapling
        "fertilizer_per_acre": 8000.0,
        "cultivation_per_acre": 14000.0,
        "avg_yield_quintal_acre": 35.0,
        "maturity_days": "Perennial (3-4 yrs first harvest)",
        "key_states": ["Uttar Pradesh", "Andhra Pradesh", "Karnataka", "Bihar", "Gujarat", "Maharashtra"]
    },
    "grapes": {
        "seed_rate_per_acre": 900.0,      # rooted rootstocks/acre
        "seed_price_per_kg": 35.0,        # INR/rootstock
        "fertilizer_per_acre": 22000.0,
        "cultivation_per_acre": 42000.0,
        "avg_yield_quintal_acre": 90.0,
        "maturity_days": "Perennial (Biannual pruning)",
        "key_states": ["Maharashtra", "Karnataka", "Tamil Nadu", "Andhra Pradesh"]
    },
    "watermelon": {
        "seed_rate_per_acre": 1.5,        # kg/acre
        "seed_price_per_kg": 1400.0,      # INR/kg (hybrid)
        "fertilizer_per_acre": 4500.0,
        "cultivation_per_acre": 9500.0,
        "avg_yield_quintal_acre": 120.0,
        "maturity_days": "80 - 95 days",
        "key_states": ["Uttar Pradesh", "Karnataka", "Punjab", "Andhra Pradesh", "Tamil Nadu", "Gujarat"]
    },
    "muskmelon": {
        "seed_rate_per_acre": 1.2,
        "seed_price_per_kg": 1600.0,
        "fertilizer_per_acre": 4200.0,
        "cultivation_per_acre": 8800.0,
        "avg_yield_quintal_acre": 80.0,
        "maturity_days": "75 - 90 days",
        "key_states": ["Punjab", "Uttar Pradesh", "Haryana", "Rajasthan", "Madhya Pradesh"]
    },
    "apple": {
        "seed_rate_per_acre": 200.0,      # grafted clonal trees/acre
        "seed_price_per_kg": 220.0,       # INR/tree
        "fertilizer_per_acre": 14000.0,
        "cultivation_per_acre": 26000.0,
        "avg_yield_quintal_acre": 40.0,
        "maturity_days": "Temperate Perennial",
        "key_states": ["Himachal Pradesh", "Uttarakhand"]
    },
    "orange": {
        "seed_rate_per_acre": 180.0,      # budded plants/acre
        "seed_price_per_kg": 85.0,
        "fertilizer_per_acre": 11000.0,
        "cultivation_per_acre": 19000.0,
        "avg_yield_quintal_acre": 50.0,
        "maturity_days": "Perennial (3-4 yrs)",
        "key_states": ["Maharashtra", "Madhya Pradesh", "Punjab", "Rajasthan", "Assam"]
    },
    "papaya": {
        "seed_rate_per_acre": 1000.0,     # seedlings/acre
        "seed_price_per_kg": 12.0,        # INR/seedling
        "fertilizer_per_acre": 11000.0,
        "cultivation_per_acre": 17000.0,
        "avg_yield_quintal_acre": 220.0,
        "maturity_days": "9 - 11 months",
        "key_states": ["Gujarat", "Andhra Pradesh", "Karnataka", "Madhya Pradesh", "Maharashtra"]
    },
    "coconut": {
        "seed_rate_per_acre": 70.0,       # selected seed palms/acre
        "seed_price_per_kg": 140.0,       # INR/palm seedling
        "fertilizer_per_acre": 7500.0,
        "cultivation_per_acre": 12000.0,
        "avg_yield_quintal_acre": 5500.0, # nuts/acre
        "maturity_days": "Perennial (5-6 yrs bearing)",
        "key_states": ["Kerala", "Tamil Nadu", "Karnataka", "Andhra Pradesh", "Odisha", "West Bengal"]
    },
    "cotton": {
        "seed_rate_per_acre": 1.8,        # kg/acre (Bt Hybrid 450g packets)
        "seed_price_per_kg": 1850.0,      # INR/kg
        "fertilizer_per_acre": 5200.0,
        "cultivation_per_acre": 12800.0,  # Manual picking intensive
        "avg_yield_quintal_acre": 9.0,
        "maturity_days": "150 - 170 days",
        "key_states": ["Gujarat", "Maharashtra", "Telangana", "Andhra Pradesh", "Rajasthan", "Karnataka", "Haryana", "Punjab"]
    },
    "jute": {
        "seed_rate_per_acre": 3.5,        # kg/acre
        "seed_price_per_kg": 140.0,
        "fertilizer_per_acre": 2800.0,
        "cultivation_per_acre": 9200.0,   # Retting and fiber extraction
        "avg_yield_quintal_acre": 11.0,
        "maturity_days": "120 - 135 days",
        "key_states": ["West Bengal", "Bihar", "Assam", "Odisha", "Uttar Pradesh"]
    },
    "coffee": {
        "seed_rate_per_acre": 450.0,      # Arabica/Robusta seedlings/acre
        "seed_price_per_kg": 35.0,        # INR/seedling
        "fertilizer_per_acre": 13500.0,
        "cultivation_per_acre": 24500.0,  # Shade lopping, picking, processing
        "avg_yield_quintal_acre": 6.5,
        "maturity_days": "Perennial (3 yrs first crop)",
        "key_states": ["Karnataka", "Kerala", "Tamil Nadu", "Andhra Pradesh", "Odisha"]
    }
}


def calculate_farm_economics(
    crop_name: str,
    farm_size_acres: float,
    user_budget_inr: float,
    selected_state: str = None,
    farming_method: str = "regular"
) -> Dict[str, Any]:
    """
    Computes indicative seed costs, fertilizer inputs, cultivation expenses,
    and budget surplus/deficit based on realistic ICAR/State agricultural extension models.

    Parameters:
        crop_name (str): The predicted crop name in lowercase.
        farm_size_acres (float): Size of farmland in acres.
        user_budget_inr (float): Total capital farmer is willing to invest.
        selected_state (str): The state selected by the farmer.

    Returns:
        dict: Detailed economic and financial profile.
    """
    crop_key = crop_name.lower().strip()
    data = CROP_ECONOMICS.get(crop_key, {
        "seed_rate_per_acre": 10.0,
        "seed_price_per_kg": 100.0,
        "fertilizer_per_acre": 3500.0,
        "cultivation_per_acre": 8000.0,
        "avg_yield_quintal_acre": 12.0,
        "maturity_days": "90 - 120 days",
        "key_states": []
    })

    # Organic farming multipliers: lower yield, higher seed/fertilizer cost, premium price
    is_organic = farming_method.lower() == "organic"
    organic_cost_factor = 1.35   # 35% higher input cost
    organic_yield_factor = 0.85  # 15% lower yield
    organic_price_premium = 1.40 # 40% higher market price

    # Calculations
    seed_qty = round(data["seed_rate_per_acre"] * farm_size_acres, 1)
    seed_price_rate = data["seed_price_per_kg"] * (organic_cost_factor if is_organic else 1.0)
    total_seed_cost = round(seed_qty * seed_price_rate, 2)

    total_fertilizer_cost = round(data["fertilizer_per_acre"] * farm_size_acres * (organic_cost_factor if is_organic else 1.0), 2)
    total_cultivation_cost = round(data["cultivation_per_acre"] * farm_size_acres, 2)

    total_estimated_investment = round(
        total_seed_cost + total_fertilizer_cost + total_cultivation_cost, 2
    )

    budget_diff = round(user_budget_inr - total_estimated_investment, 2)
    is_sufficient = budget_diff >= 0

    # Regional alignment check
    is_prime_state = False
    if selected_state:
        st_clean = selected_state.strip().lower()
        if any(ks.strip().lower() == st_clean for ks in data.get("key_states", [])):
            is_prime_state = True

    # Yield and revenue estimates
    effective_yield_per_acre = data["avg_yield_quintal_acre"] * (organic_yield_factor if is_organic else 1.0)
    total_yield_quintals = round(effective_yield_per_acre * farm_size_acres, 1)
    # Approximate MSP/market price per quintal (rough estimate for common crops)
    APPROX_PRICE_PER_QUINTAL = {
        "rice": 2183, "maize": 1870, "chickpea": 5440, "kidneybeans": 6000,
        "pigeonpeas": 6600, "mothbeans": 5600, "mungbean": 7275, "blackgram": 6950,
        "lentil": 6000, "pomegranate": 15000, "banana": 2000, "mango": 8000,
        "grapes": 10000, "watermelon": 1500, "muskmelon": 2500, "apple": 18000,
        "orange": 4500, "papaya": 1800, "coconut": 2800, "cotton": 6620,
        "jute": 4500, "coffee": 18000
    }
    price_per_quintal = APPROX_PRICE_PER_QUINTAL.get(crop_key, 3000)
    if is_organic:
        price_per_quintal = round(price_per_quintal * organic_price_premium)
    estimated_revenue = round(total_yield_quintals * price_per_quintal, 2)
    estimated_profit = round(estimated_revenue - total_estimated_investment, 2)

    return {
        "crop": crop_key,
        "farm_size_acres": farm_size_acres,
        "user_budget": user_budget_inr,
        "farming_method": farming_method,
        "is_organic": is_organic,
        "seed_rate_per_acre": data["seed_rate_per_acre"],
        "seed_price_rate": round(seed_price_rate, 2),
        "total_seed_qty": seed_qty,
        "total_seed_cost": total_seed_cost,
        "total_fertilizer_cost": total_fertilizer_cost,
        "total_cultivation_cost": total_cultivation_cost,
        "total_estimated_investment": total_estimated_investment,
        "budget_difference": abs(budget_diff),
        "is_sufficient": is_sufficient,
        "budget_status": "SURPLUS" if is_sufficient else "DEFICIT",
        "avg_yield_quintal_acre": data["avg_yield_quintal_acre"],
        "avg_yield_quintal_acre": round(effective_yield_per_acre, 2),
        "total_expected_yield_quintals": total_yield_quintals,
        "price_per_quintal": price_per_quintal,
        "estimated_revenue": estimated_revenue,
        "estimated_profit": estimated_profit,
        "maturity_days": data["maturity_days"],
        "is_prime_state": is_prime_state,
        "prime_states_list": data.get("key_states", [])
    }
