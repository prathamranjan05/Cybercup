from flask import Flask, jsonify, render_template, send_from_directory, request
import pandas as pd
import numpy as np
import pickle
import os
from flask_cors import CORS
import logging
from datetime import datetime
import requests  # For Fast2SMS

# ----- FLASK APP INIT -----
app = Flask(
    __name__,
    template_folder="../CyberCupWebpadge",
    static_folder="../CyberCupWebpadge"
)
CORS(app)

# ----- LOGGING -----
logging.basicConfig(level=logging.INFO)

# ----- STATIC FILE ROUTES -----
@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory("../CyberCupWebpadge/images", filename)

@app.route('/map/<path:filename>')
def map_files(filename):
    return send_from_directory("../CyberCupWebpadge/map", filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory("../CyberCupWebpadge/js", filename)

# ----- MODEL & DATA -----
model_path = r"D:\Cybercup\backend\models\lgb_model.pkl"
sensor_csv = r"D:\Cybercup\backend\db\flash_flood.csv"

# Load trained model
with open(model_path, "rb") as f:
    model = pickle.load(f)

# Load sensor CSV
sensors_df = pd.read_csv(sensor_csv)
feature_columns = ["rainfall_mm_hr", "drainage_level_cm", "flow_rate_lps"]

# Predefined sensor locations
unit_locations = {
    "DRAIN_A01": (19.0760, 72.8777),
    "DRAIN_B02": (19.2183, 72.9781),
    "DRAIN_C03": (19.0760, 72.9080),
    "DELHI_01": (28.6139, 77.2090),
    "DELHI_02": (28.7041, 77.1025),
    "BLR_01": (12.9716, 77.5946),
    "BLR_02": (12.9352, 77.6245),
    "KOL_01": (22.5726, 88.3639),
    "KOL_02": (22.5600, 88.4000),
    "CHN_01": (13.0827, 80.2707),
    "CHN_02": (13.0674, 80.2376),
}

# Fast2SMS configuration
FAST2SMS_API_KEY = "z2CBWVbPPkCQp0H9V75WneHuW9cCAkw0bloCms025OTc7cMNoODleJY2BmUs"
ALERT_PHONE = "919868881285"

last_alert_status = {}

def send_fast2sms_alert(message, phone):
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "route": "v3",
        "sender_id": "FLOODS",
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": phone
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        logging.info(f"Fast2SMS response: {response.status_code} {response.text}")
        return response.status_code, response.text
    except Exception as e:
        logging.error(f"Error sending SMS via Fast2SMS: {e}")
        return None, str(e)

# ----- CONTROL STRATEGIES MODULE -----
def control_strategies(water_level, rainfall, location):
    suggestions = []

    if water_level > 1.8:
        suggestions.append(f"Activate pumps at {location}.")
        suggestions.append(f"Open diversion channels near {location}.")
        suggestions.append(f"Reroute traffic away from {location} via safe routes.")
    elif water_level > 1.2:
        suggestions.append(f"Prepare pumps at {location}.")
        suggestions.append(f"Consider opening diversion channels near {location}.")
        suggestions.append(f"Monitor traffic and prepare rerouting if needed.")
    elif water_level > 0.9:
        suggestions.append(f"Monitor water levels at {location}.")
    else:
        suggestions.append(f"No immediate action required at {location}.")

    return suggestions

# ----- ROUTES -----
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard.html")
def dashboard():
    return render_template("dashboard.html")

@app.route("/manifest.json")
def manifest():
    return send_from_directory("../CyberCupWebpadge", "manifest.json")

@app.route("/sw.js")
def service_worker():
    return send_from_directory("../CyberCupWebpadge", "sw.js")

@app.route("/api/waterlogged")
def waterlogged():
    sensors = []
    try:
        latest_data = sensors_df.sort_values("TIMESTAMP").groupby("UNIT_ID").tail(1)
        for _, row in latest_data.iterrows():
            try:
                features_df = pd.DataFrame([{
                    "rainfall_mm_hr": row["rainfall_mm_hr"],
                    "drainage_level_cm": row["drainage_level_cm"] / 100.0,
                    "flow_rate_lps": row["flow_rate_lps"]
                }])
                predicted_level = model.predict(features_df)[0]

                status = "danger" if predicted_level > 1.8 else "warning" if predicted_level > 0.9 else "safe"
                last_alert_status.setdefault(row["UNIT_ID"], status)

                lat, lon = unit_locations.get(row["UNIT_ID"], (19.0760, 72.8777))
                sensors.append({
                    "id": row["UNIT_ID"],
                    "lat": lat,
                    "lon": lon,
                    "water_level": round(predicted_level, 2),
                    "status": status,
                    "timestamp": row["TIMESTAMP"]
                })
            except Exception as e:
                logging.error(f"Error processing UNIT_ID {row.get('UNIT_ID', 'unknown')}: {e}")
                continue

        # Demo sensors
        demo_units = ["DELHI_01", "BLR_01", "KOL_01", "CHN_01"]
        for unit in demo_units:
            lat, lon = unit_locations[unit]
            water_level = float(np.random.uniform(0, 2.5))
            status = "safe" if water_level <= 0.9 else "warning" if water_level <= 1.8 else "danger"
            sensors.append({
                "id": unit,
                "lat": lat,
                "lon": lon,
                "water_level": round(water_level, 2),
                "status": status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    except Exception as e:
        logging.error(f"Error generating waterlogged data: {e}")

    return jsonify(sensors)

@app.route("/api/control_strategies/<unit_id>")
def get_control_strategies(unit_id):
    try:
        matched = sensors_df[sensors_df["UNIT_ID"] == unit_id].sort_values("TIMESTAMP").tail(1)
        if matched.empty:
            return jsonify({"unit_id": unit_id, "strategies": ["No data available"]})

        row = matched.iloc[0]
        features_df = pd.DataFrame([{
            "rainfall_mm_hr": row["rainfall_mm_hr"],
            "drainage_level_cm": row["drainage_level_cm"] / 100.0,
            "flow_rate_lps": row["flow_rate_lps"]
        }])
        predicted_level = model.predict(features_df)[0]

        strategies = control_strategies(predicted_level, row["rainfall_mm_hr"], unit_id)
        return jsonify({"unit_id": unit_id, "strategies": strategies})
    except Exception as e:
        logging.error(f"Error generating control strategies for {unit_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/send_alert/<unit_id>", methods=["POST"])
def send_alert(unit_id):
    try:
        matched = sensors_df[sensors_df["UNIT_ID"] == unit_id].sort_values("TIMESTAMP").tail(1)
        if matched.empty:
            message = f"⚠️ ALERT: High flood risk reported at {unit_id} (no historical row found). Please check the dashboard."
            status_code, resp_text = send_fast2sms_alert(message, ALERT_PHONE)
            return jsonify({"sent": False if status_code is None else True, "detail": resp_text}), 200

        row = matched.iloc[0]
        features_df = pd.DataFrame([{
            "rainfall_mm_hr": row["rainfall_mm_hr"],
            "drainage_level_cm": row["drainage_level_cm"] / 100.0,
            "flow_rate_lps": row["flow_rate_lps"]
        }])
        predicted_level = model.predict(features_df)[0]

        msg = (
            f"⚠️ FLOOD ALERT: {unit_id}\n"
            f"Water level (predicted): {predicted_level:.2f} m\n"
            f"Rainfall: {row['rainfall_mm_hr']} mm/hr\n"
            f"Flow rate: {row['flow_rate_lps']} lps\n"
            f"Time: {row['TIMESTAMP']}"
        )

        status_code, resp_text = send_fast2sms_alert(msg, ALERT_PHONE)
        if status_code is None:
            return jsonify({"sent": False, "error": resp_text}), 500

        logging.info(f"Alert sent for {unit_id} via Fast2SMS. resp: {status_code}")
        return jsonify({"sent": True, "status_code": status_code, "response": resp_text}), 200
    except Exception as e:
        logging.error(f"Error in send_alert for {unit_id}: {e}")
        return jsonify({"sent": False, "error": str(e)}), 500

# ----- RUN APP -----
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
