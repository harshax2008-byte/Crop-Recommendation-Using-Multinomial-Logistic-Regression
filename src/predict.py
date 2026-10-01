"""
Crop Recommendation System - Inference & Prediction Module
Author: College ML Project
Description: Loads the trained pipeline, validates user inputs, and performs
             crop recommendation with confidence scores.
"""

import os
import sys
import joblib
import pandas as pd
from typing import Dict, Any, List, Tuple

# Ensure stdout/stderr handles UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
PIPELINE_PATH = os.path.join(MODELS_DIR, "crop_pipeline.joblib")

# Agronomic valid ranges for 7 input features
FEATURE_RANGES = {
    "N": (0.0, 150.0, "Nitrogen ratio in soil (kg/ha)"),
    "P": (0.0, 150.0, "Phosphorus ratio in soil (kg/ha)"),
    "K": (0.0, 210.0, "Potassium ratio in soil (kg/ha)"),
    "temperature": (0.0, 55.0, "Temperature (°C)"),
    "humidity": (5.0, 100.0, "Relative Humidity (%)"),
    "ph": (3.5, 10.0, "Soil pH value (acidic to alkaline)"),
    "rainfall": (10.0, 350.0, "Rainfall (mm)")
}

# Crop display metadata for presentation / UI
CROP_METADATA = {
    "rice": {"emoji": "🌾", "scientific": "Oryza sativa", "category": "Cereal", "water": "High (>200mm)", "season": "Kharif (Monsoon)", "soil": "Clayey / Heavy Loam", "desc": "Thrives in warm, highly humid waterlogged environments with abundant rainfall."},
    "maize": {"emoji": "🌽", "scientific": "Zea mays", "category": "Cereal / Grain", "water": "Moderate (60-100mm)", "season": "Kharif / Rabi", "soil": "Well-drained Fertile Loam", "desc": "Versatile cereal grain requiring warm temperatures and moderate moisture."},
    "chickpea": {"emoji": "🫘", "scientific": "Cicer arietinum", "category": "Pulse / Legume", "water": "Low (60-90mm)", "season": "Rabi (Winter)", "soil": "Deep Sandy Loam", "desc": "Cool-season legume that enriches soil nitrogen and thrives in low-rainfall areas."},
    "kidneybeans": {"emoji": "🫘", "scientific": "Phaseolus vulgaris", "category": "Pulse / Legume", "water": "Moderate (100-150mm)", "season": "Kharif / Rabi", "soil": "Rich Organic Loam", "desc": "Nutrient-dense legume requiring rich, loose soil and mild temperatures."},
    "pigeonpeas": {"emoji": "🌱", "scientific": "Cajanus cajan", "category": "Pulse / Legume", "water": "Low to Moderate", "season": "Kharif (Monsoon)", "soil": "Deep Loam / Clay Loam", "desc": "Drought-resilient deep-rooting pulse crop that fixes atmospheric nitrogen."},
    "mothbeans": {"emoji": "🌿", "scientific": "Vigna aconitifolia", "category": "Pulse / Legume", "water": "Very Low (30-60mm)", "season": "Kharif", "soil": "Light Sandy Soil", "desc": "Extremely drought-hardy arid legume ideal for dryland farming."},
    "mungbean": {"emoji": "🌱", "scientific": "Vigna radiata", "category": "Pulse / Legume", "water": "Low (40-60mm)", "season": "Summer / Kharif", "soil": "Well-drained Sandy Loam", "desc": "Short-duration crop suited for warm summer conditions and multi-cropping."},
    "blackgram": {"emoji": "🫘", "scientific": "Vigna mungo", "category": "Pulse / Legume", "water": "Low to Moderate", "season": "Kharif / Summer", "soil": "Heavier Loamy Soil", "desc": "High-protein pulse crop that maintains soil fertility through nitrogen fixation."},
    "lentil": {"emoji": "🍲", "scientific": "Lens culinaris", "category": "Pulse / Legume", "water": "Low (40-70mm)", "season": "Rabi (Winter)", "soil": "Clay Loam / Alluvial", "desc": "Cool-climate rabi pulse crop requiring minimal irrigation and balanced nutrients."},
    "pomegranate": {"emoji": "🏮", "scientific": "Punica granatum", "category": "Horticultural Fruit", "water": "Moderate (100-120mm)", "season": "Perennial / Annual", "soil": "Well-drained Gravelly Loam", "desc": "Semi-arid fruit crop with high export value, tolerant of mild salinity."},
    "banana": {"emoji": "🍌", "scientific": "Musa acuminata", "category": "Tropical Fruit", "water": "High (150-200mm)", "season": "Annual / Perennial", "soil": "Rich, Moisture-retentive Loam", "desc": "Heavy feeder requiring high nitrogen, high potassium, and continuous moisture."},
    "mango": {"emoji": "🥭", "scientific": "Mangifera indica", "category": "Tropical Fruit Tree", "water": "Moderate (90-120mm)", "season": "Perennial (Summer Harvest)", "soil": "Deep Well-drained Alluvial", "desc": "The 'King of Fruits' requiring warm, dry weather during flowering and fruit setting."},
    "grapes": {"emoji": "🍇", "scientific": "Vitis vinifera", "category": "Vineyard Fruit", "water": "Moderate (60-80mm)", "season": "Perennial", "soil": "Well-drained Sandy Loam", "desc": "High potassium demand vine crop requiring sunny, dry weather during ripening."},
    "watermelon": {"emoji": "🍉", "scientific": "Citrullus lanatus", "category": "Cucurbit / Fruit", "water": "Moderate (40-60mm)", "season": "Zaid (Summer)", "soil": "Sandy Riverbed Soil", "desc": "Warm-season creeping crop with high water content, requiring full sun and sandy beds."},
    "muskmelon": {"emoji": "🍈", "scientific": "Cucumis melo", "category": "Cucurbit / Fruit", "water": "Moderate (20-40mm)", "season": "Zaid (Summer)", "soil": "Sandy / Loamy", "desc": "Thrives in warm, dry climates with low atmospheric humidity and good sunshine."},
    "apple": {"emoji": "🍎", "scientific": "Malus domestica", "category": "Temperate Fruit", "water": "Moderate (100-130mm)", "season": "Temperate (Cool Climate)", "soil": "Deep, Well-drained Loam", "desc": "Requires chill hours, temperate mountain elevations, and high soil potassium."},
    "orange": {"emoji": "🍊", "scientific": "Citrus sinensis", "category": "Citrus Fruit", "water": "Moderate (100-120mm)", "season": "Subtropical / Tropical", "soil": "Deep Sandy Loam", "desc": "High-value citrus tree requiring well-aerated soil and balanced trace minerals."},
    "papaya": {"emoji": "🥭", "scientific": "Carica papaya", "category": "Tropical Fruit", "water": "Moderate (140-180mm)", "season": "Tropical (Year-round)", "soil": "Rich Organic Loam", "desc": "Fast-growing tropical plant sensitive to waterlogging and frost."},
    "coconut": {"emoji": "🥥", "scientific": "Cocos nucifera", "category": "Plantation Palm", "water": "High (150-250mm)", "season": "Coastal / Perennial", "soil": "Coastal Sandy / Alluvial", "desc": "Thrives in humid tropical coastal zones with plenty of sunshine and saline tolerance."},
    "cotton": {"emoji": "🧶", "scientific": "Gossypium hirsutum", "category": "Commercial Fiber", "water": "Moderate (60-100mm)", "season": "Kharif (Monsoon)", "soil": "Black Cotton Soil (Regur)", "desc": "Important cash crop requiring high nitrogen, warm climate, and deep clayey soils."},
    "jute": {"emoji": "🧵", "scientific": "Corchorus olitorius", "category": "Commercial Bast Fiber", "water": "High (150-200mm)", "season": "Kharif (Monsoon)", "soil": "Alluvial Floodplain Soil", "desc": "Golden fiber crop requiring warm, humid weather and standing water tolerance."},
    "coffee": {"emoji": "☕", "scientific": "Coffea arabica", "category": "Plantation Beverage", "water": "High (150-200mm)", "season": "Perennial (Hill Slopes)", "soil": "Humus-rich Volcanic Loam", "desc": "Shade-loving hill slope crop requiring well-distributed rainfall and cool nights."}
}

_pipeline_cache = None


def load_crop_pipeline():
    """
    Loads and caches the trained scikit-learn pipeline.
    """
    global _pipeline_cache
    if _pipeline_cache is None:
        if not os.path.exists(PIPELINE_PATH):
            raise FileNotFoundError(
                f"Trained model pipeline not found at {PIPELINE_PATH}. "
                "Please run 'python src/train_model.py' first."
            )
        _pipeline_cache = joblib.load(PIPELINE_PATH)
    return _pipeline_cache


def validate_input_values(input_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates user input:
      - Ensures all 7 required features are provided.
      - Checks that all values are convertible to float.
      - Checks if values are within realistic agricultural limits.

    Returns:
        (is_valid: bool, warnings_or_errors: List[str])
    """
    issues = []

    for feature, (min_val, max_val, desc) in FEATURE_RANGES.items():
        if feature not in input_dict:
            issues.append(f"Missing required feature: '{feature}' ({desc})")
            continue

        raw_val = input_dict[feature]
        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            issues.append(f"Feature '{feature}' must be a valid number, got: '{raw_val}'")
            continue

        if val < min_val or val > max_val:
            issues.append(
                f"'{feature}' value {val} is outside standard agronomic range "
                f"[{min_val} to {max_val}]. Prediction will proceed, but accuracy may decrease."
            )

    is_valid = not any("Missing" in err or "must be a valid number" in err for err in issues)
    return is_valid, issues


def predict_crop(
    n: float,
    p: float,
    k: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    top_n: int = 3
) -> Dict[str, Any]:
    """
    Executes crop recommendation using the trained Multinomial Logistic Regression pipeline.

    Parameters:
        n (float): Nitrogen content in soil (kg/ha)
        p (float): Phosphorus content in soil (kg/ha)
        k (float): Potassium content in soil (kg/ha)
        temperature (float): Temperature (°C)
        humidity (float): Relative humidity (%)
        ph (float): Soil pH (0-14)
        rainfall (float): Rainfall (mm)
        top_n (int): Number of top candidate crops to return

    Returns:
        dict: Recommended crop, probability confidence, top-N alternatives, and agronomic info.
    """
    pipeline = load_crop_pipeline()

    # Format into DataFrame with exact feature names
    input_data = {
        "N": [float(n)],
        "P": [float(p)],
        "K": [float(k)],
        "temperature": [float(temperature)],
        "humidity": [float(humidity)],
        "ph": [float(ph)],
        "rainfall": [float(rainfall)]
    }
    input_df = pd.DataFrame(input_data)

    print(f"[ML INFERENCE] Input Features -> N={float(n)}, P={float(p)}, K={float(k)}, "
          f"Temp={float(temperature)}°C, Hum={float(humidity)}%, pH={float(ph)}, Rain={float(rainfall)}mm")

    # 1. Direct class prediction
    predicted_crop = pipeline.predict(input_df)[0]

    # 2. Probability distribution via Softmax
    probabilities = pipeline.predict_proba(input_df)[0]
    classes = pipeline.classes_

    # Rank classes by probability descending
    sorted_indices = probabilities.argsort()[::-1]
    top_predictions = []

    for idx in sorted_indices[:top_n]:
        crop_name = classes[idx]
        prob = float(probabilities[idx])
        top_predictions.append({
            "crop": crop_name,
            "crop_display": crop_name.capitalize(),
            "confidence_pct": round(prob * 100, 2),
            "metadata": CROP_METADATA.get(crop_name.lower(), {})
        })

    print(f"[ML INFERENCE] Output -> Predicted Crop: {predicted_crop.capitalize()} (Confidence: {top_predictions[0]['confidence_pct']}%)")

    primary_meta = CROP_METADATA.get(predicted_crop.lower(), {
        "category": "Crop", "water": "Standard", "season": "All-season", "soil": "Standard Soil"
    })

    return {
        "recommended_crop": predicted_crop,
        "recommended_crop_display": predicted_crop.capitalize(),
        "confidence_pct": top_predictions[0]["confidence_pct"],
        "top_candidates": top_predictions,
        "metadata": primary_meta,
        "input_features": {
            "Nitrogen (N)": n,
            "Phosphorus (P)": p,
            "Potassium (K)": k,
            "Temperature (°C)": temperature,
            "Humidity (%)": humidity,
            "Soil pH": ph,
            "Rainfall (mm)": rainfall
        }
    }


if __name__ == "__main__":
    print("--- Running Sample Prediction Self-Check ---")
    # Example: Typical conditions for Rice (High N, High Humidity, High Rainfall)
    sample_input = {
        "n": 90,
        "p": 42,
        "k": 43,
        "temperature": 20.87,
        "humidity": 82.00,
        "ph": 6.50,
        "rainfall": 202.93
    }
    try:
        result = predict_crop(**sample_input)
        print("\nInput Parameters:", sample_input)
        print(f"\nRecommended Crop: {result['recommended_crop_display']}")
        print(f"Confidence Score: {result['confidence_pct']}%")
        print("Top 3 Candidates:")
        for cand in result["top_candidates"]:
            print(f"  - {cand['crop_display']}: {cand['confidence_pct']}%")
    except Exception as e:
        print(f"Prediction error (model might need to be trained first): {e}")
