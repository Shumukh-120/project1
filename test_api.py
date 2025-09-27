
import requests

url = "http://127.0.0.1:8000/predict"

data = {
    "data": {
        "Air_Temperature_K": 298.0,
        "Process_Temperature_K": 303.0,
        "Rotation_Speed_RPM": 1500,
        "Torque_Nm": 40,
        "Tool_Wear_min": 200,
        "Machine_Type_M": 1
    }
}

try:
    response = requests.post(url, json=data)
    print("Prediction result:")
    print(response.json())
except Exception as e:
    print(" An error occurred while connecting to the API ❌ ", e)