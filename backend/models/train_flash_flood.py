import pandas as pd
import numpy as np
import pickle
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Load CSV
csv_path = r"D:\Cybercup\backend\db\flash_flood.csv"
df = pd.read_csv(csv_path)

# Features and target
# Assuming target is water_level (simulated for now)
if "water_level_m" not in df.columns:
    # For demo, we simulate water_level as function of rainfall + drainage + flow
    df["water_level_m"] = df["rainfall_mm_hr"] * 0.05 + df["drainage_level_cm"] / 100 * 0.8 + df["flow_rate_lps"] * 0.002

X = df[["rainfall_mm_hr", "drainage_level_cm", "flow_rate_lps"]]
y = df["water_level_m"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train LightGBM model
model = LGBMRegressor(n_estimators=200, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Test MSE: {mse:.4f}")

# Save model
model_path = r"D:\Cybercup\backend\models\lgb_model.pkl"
with open(model_path, "wb") as f:
    pickle.dump(model, f)

print(f"Model saved to {model_path}")
