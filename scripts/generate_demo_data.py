import numpy as np
import pandas as pd
import os

def generate_datasets():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data")
    os.makedirs(output_dir, exist_ok=True)
    np.random.seed(42)
    n_samples = 1200

    print("=" * 60)
    print("Generating Presentation & Live Demo Datasets for Enterprise AI Platform")
    print("=" * 60)

    # 1. BASELINE TRAINING DATASET (Customer Churn)
    tenure = np.random.exponential(scale=20, size=n_samples).clip(1, 72).astype(int)
    monthly_charges = np.random.normal(loc=65, scale=25, size=n_samples).clip(18, 120).round(2)
    total_charges = (tenure * monthly_charges * np.random.uniform(0.95, 1.05, size=n_samples)).round(2)
    contract = np.random.choice(["Month-to-Month", "One-Year", "Two-Year"], size=n_samples, p=[0.55, 0.25, 0.20])
    internet_service = np.random.choice(["Fiber Optic", "DSL", "No"], size=n_samples, p=[0.45, 0.35, 0.20])
    payment_method = np.random.choice(["Electronic Check", "Mailed Check", "Bank Transfer", "Credit Card"], size=n_samples)
    senior_citizen = np.random.choice([0, 1], size=n_samples, p=[0.84, 0.16])

    # Realistic churn interactions
    churn_logit = (-1.5 
                   + 0.03 * monthly_charges 
                   - 0.05 * tenure 
                   + 0.8 * (contract == "Month-to-Month") 
                   + 0.5 * (internet_service == "Fiber Optic")
                   + 0.3 * senior_citizen)
    churn_prob = 1 / (1 + np.exp(-churn_logit))
    churn = (np.random.uniform(0, 1, size=n_samples) < churn_prob).astype(int)

    df_baseline = pd.DataFrame({
        "customer_id": [f"CUST-{10000+i}" for i in range(n_samples)],
        "tenure": tenure,
        "monthly_charges": monthly_charges,
        "total_charges": total_charges,
        "contract": contract,
        "internet_service": internet_service,
        "payment_method": payment_method,
        "senior_citizen": senior_citizen,
        "churn": churn
    })
    baseline_path = os.path.join(output_dir, "customer_churn_baseline.csv")
    df_baseline.to_csv(baseline_path, index=False)
    print(f"✓ 1. Baseline Training Dataset created: {baseline_path} (1,200 rows, 9 columns)")

    # 2. DRIFTED PRODUCTION DATASET (Simulates Macroeconomic Inflation & Shift)
    n_drift = 600
    drift_tenure = np.random.exponential(scale=10, size=n_drift).clip(1, 36).astype(int)
    drift_charges = np.random.normal(loc=95, scale=20, size=n_drift).clip(45, 150).round(2)
    drift_total = (drift_tenure * drift_charges).round(2)
    drift_contract = np.random.choice(["Month-to-Month", "One-Year", "Two-Year"], size=n_drift, p=[0.80, 0.15, 0.05])
    drift_internet = np.random.choice(["Fiber Optic", "DSL", "No"], size=n_drift, p=[0.70, 0.20, 0.10])
    drift_payment = np.random.choice(["Electronic Check", "Mailed Check", "Bank Transfer", "Credit Card"], size=n_drift)
    drift_senior = np.random.choice([0, 1], size=n_drift, p=[0.70, 0.30])

    df_drifted = pd.DataFrame({
        "customer_id": [f"DRIFT-{20000+i}" for i in range(n_drift)],
        "tenure": drift_tenure,
        "monthly_charges": drift_charges,
        "total_charges": drift_total,
        "contract": drift_contract,
        "internet_service": drift_internet,
        "payment_method": drift_payment,
        "senior_citizen": drift_senior,
    })
    drifted_path = os.path.join(output_dir, "customer_churn_drifted.csv")
    df_drifted.to_csv(drifted_path, index=False)
    print(f"✓ 2. Drifted Production Dataset created: {drifted_path} (600 rows - shifted distributions for PSI/K-S demo)")

    # 3. BATCH INFERENCE TEST DATASET (Unlabelled Customers)
    df_batch = df_drifted.head(100).copy()
    batch_path = os.path.join(output_dir, "customer_churn_batch_test.csv")
    df_batch.to_csv(batch_path, index=False)
    print(f"✓ 3. Batch Inference Test Dataset created: {batch_path} (100 rows)")
    print("=" * 60)
    print("Ready for presentation demo! Refer to PRESENTATION_DEMO_GUIDE.md for the step-by-step presentation script.")

if __name__ == "__main__":
    generate_datasets()
