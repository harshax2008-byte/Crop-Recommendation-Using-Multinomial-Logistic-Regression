# 🌱 Crop Recommendation System Using Machine Learning

**Multinomial Logistic Regression (MLR) for Precision Agriculture**  
*College Machine Learning Project*

---

## 📌 1. Project Objective & Problem Statement

### Problem Statement
In traditional farming, crop selection relies primarily on intuition, past habits, or general seasonal patterns. However, soil chemical properties (Nitrogen, Phosphorus, Potassium, pH) and dynamic atmospheric factors (temperature, relative humidity, rainfall) vary drastically across micro-regions. Planting an unsuitable crop leads to poor yield, financial loss for farmers, and excessive wastage of fertilizers and groundwater.

### Objective
To build a supervised Machine Learning system that analyzes measurable soil and climate parameters and accurately recommends the most optimal crop to cultivate. The project employs **Multinomial Logistic Regression (MLR)** configured with a **Softmax** multiclass function to ensure high accuracy, transparency, and computational efficiency.

---

## 🌾 2. Dataset Overview

- **Source:** Standard Precision Agriculture / Kaggle Crop Recommendation Dataset.
- **Total Records:** 2,200 samples.
- **Target Classes:** 22 unique crops (100 balanced samples per crop).
- **Crops Included:**
  `Rice`, `Maize`, `Chickpea`, `Kidneybeans`, `Pigeonpeas`, `Mothbeans`, `Mungbean`, `Blackgram`, `Lentil`, `Pomegranate`, `Banana`, `Mango`, `Grapes`, `Watermelon`, `Muskmelon`, `Apple`, `Orange`, `Papaya`, `Coconut`, `Cotton`, `Jute`, `Coffee`.

### Input Features (7 Attributes)

| Feature | Description | Measurement Unit | Typical Agronomic Range |
| :--- | :--- | :--- | :--- |
| **N** | Ratio of Nitrogen in soil | kg/ha | 0 – 140 |
| **P** | Ratio of Phosphorus in soil | kg/ha | 5 – 145 |
| **K** | Ratio of Potassium in soil | kg/ha | 5 – 205 |
| **temperature** | Ambient temperature | °C | 8.8 – 43.7 |
| **humidity** | Relative humidity | % | 14.3 – 99.9 |
| **ph** | Soil pH (Acidity / Alkalinity) | pH scale (0–14) | 3.5 – 9.9 |
| **rainfall** | Precipitation / Rainfall | mm | 20.2 – 298.6 |

---

## 🧠 3. Machine Learning in This Project

In this project, Machine Learning replaces static rule-based tables with a **data-driven model**. The system:
1. Learns the complex mathematical boundaries and relationship patterns between historical soil/climate conditions and crop growth outcomes.
2. Given any new combination of 7 input values, computes the exact probability for each of the 22 crops and recommends the crop with the highest likelihood of thriving.

---

## ⚙️ 4. Why Multinomial Logistic Regression (MLR)?

1. **Multiclass Specialization:** Standard Logistic Regression only handles binary outcomes (0 or 1). Multinomial Logistic Regression (MLR) naturally handles $K > 2$ categories (here $K = 22$) using the **Softmax function**.
2. **Probabilistic Outputs:** Instead of an opaque "black-box" decision, MLR outputs a normalized probability distribution across all crops (e.g., Rice: 94%, Jute: 4%, Maize: 2%), providing transparency to agricultural officers and farmers.
3. **Computational Efficiency & Scalability:** MLR has low memory overhead and executes predictions in under 2 milliseconds, making it ideal for edge devices, low-cost servers, and offline field deployments.
4. **Project Abstract Requirement:** Specifically chosen and required by our academic project abstract.

---

## 🔄 5. Preprocessing & Zero Data Leakage Pipeline

The end-to-end pipeline is structured as follows:

```
Raw CSV Dataset (2,200 rows)
            ↓
Data Cleaning (Check Nulls, Remove Duplicates, Type Validation)
            ↓
Stratified Train-Test Split (80% Train: 1,760 samples | 20% Test: 440 samples)
            ↓
       Pipeline:
   ┌────────────────────────────────────────────────────────┐
   │ 1. StandardScaler (Zero Mean, Unit Variance)           │
   │    z = (x - μ) / σ (Fitted strictly on Train Data)     │
   │ 2. Multinomial Logistic Regression (solver='lbfgs')    │
   │    z_k = W_k · x + b_k  →  P(y=k) = Softmax(z_k)      │
   └────────────────────────────────────────────────────────┘
            ↓
Trained Pipeline Artifact (`models/crop_pipeline.joblib`)
```

- **Why Scaling Matters:** Features have vastly different orders of magnitude (Rainfall reaches ~300, while pH is ~6.5). Scaling prevents larger-scale features from dominating the gradient updates.
- **Preventing Data Leakage:** The `StandardScaler` parameters ($\mu$ and $\sigma$) are learned **strictly** on the training partition (`X_train`) inside a `Pipeline`, ensuring test data remains completely unobserved until final evaluation.

---

## 📊 6. Evaluation Metrics

Evaluated on 440 unseen test samples:

- **Accuracy:** ~95% - 97% overall test classification accuracy.
- **Precision (Weighted):** ~95% - 97% (measures how accurately the model avoids false positives).
- **Recall (Weighted):** ~95% - 97% (measures how effectively the model captures actual crop samples).
- **F1-Score (Weighted):** ~95% - 97% (harmonic mean of precision and recall).
- **Confusion Matrix:** Heatmap visual demonstrating minimal misclassification across 22 classes.

---

## 🚀 7. How to Setup and Run the Project

### Step 1: Install Dependencies
Open terminal or command prompt in the project root:
```bash
pip install -r requirements.txt
```

### Step 2: Train the Model & Generate Artifacts
Run the standalone training script:
```bash
python src/train_model.py
```
*This downloads the dataset (if not present), runs data cleaning, fits the pipeline, outputs evaluation tables, and saves the trained pipeline and confusion matrix plot inside `models/`.*

### Step 3: Run Sample Prediction Test (Optional CLI check)
```bash
python src/predict.py
```

### Step 4: Launch the Interactive Web Application
```bash
streamlit run app.py
```
The browser will automatically open at:
```
http://localhost:8501
```

---

## 📁 8. Project Structure

```
ML-project/
│
├── data/
│   └── crop_recommendation.csv   # 2,200 sample crop dataset
│
├── models/
│   ├── crop_pipeline.joblib      # Serialized trained scaler + MLR pipeline
│   ├── model_metrics.json        # Evaluation scores & classification report
│   └── confusion_matrix.png      # High-resolution confusion matrix heatmap
│
├── src/
│   ├── data_loader.py            # Data acquisition & cleaning
│   ├── preprocessing.py          # Train-test split & scikit-learn Pipeline
│   ├── train_model.py            # Model training, scoring, artifact saving
│   ├── predict.py                # Inference, validation & confidence calculations
│   └── agri_data.py              # Regional states/districts & farm economics benchmarks
│
├── app.py                        # Premium Streamlit interactive web interface
├── requirements.txt              # Required dependencies
├── README.md                     # Project overview and technical documentation
└── .gitignore                    # Git ignore file
```

---

## 👥 Contributors & Academic Acknowledgments
- **Project:** Crop Recommendation Using Machine Learning
- **Algorithm:** Multinomial Logistic Regression (MLR)
- **Domain:** Artificial Intelligence & Precision Agriculture
