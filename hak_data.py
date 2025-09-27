import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from fastapi import FastAPI
from pydantic import BaseModel
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import uvicorn

# -------------------------------
# مسارات الملفات
# -------------------------------
folder_path = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(folder_path, "ai4i2020.csv")
cleaned_file = os.path.join(folder_path, "ai4i2020_cleaned.csv")
model_file = os.path.join(folder_path, "predictive_maintenance_model.pkl")
onnx_file = os.path.join(folder_path, "predictive_maintenance_model.onnx")

# -------------------------------
# تدريب النموذج إذا غير موجود
# -------------------------------
if not os.path.exists(model_file):
    print("Model not found. Training in progress.❌")
    df = pd.read_csv(csv_file)

    numeric_cols = ['Air temperature [K]', 'Process temperature [K]',
                    'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    df.rename(columns={
        "Type": "Machine_Type",
        "Air temperature [K]": "Air_Temperature_K",
        "Process temperature [K]": "Process_Temperature_K",
        "Rotational speed [rpm]": "Rotation_Speed_RPM",
        "Torque [Nm]": "Torque_Nm",
        "Tool wear [min]": "Tool_Wear_min",
        "Machine failure": "Failure"
    }, inplace=True)

    df['Temp_Diff'] = df['Process_Temperature_K'] - df['Air_Temperature_K']
    df['Tool_Wear_rate'] = df['Tool_Wear_min'] / (df['Rotation_Speed_RPM'] + 1e-3)

    df = pd.get_dummies(df, columns=['Machine_Type'])
    df.to_csv(cleaned_file, index=False)

    X = df.drop(columns=['Failure', 'UDI', 'Product ID'], errors='ignore')
    y = df['Failure']
    X = X.astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    joblib.dump(rf_model, model_file)

    initial_type = [('float_input', FloatTensorType([None, X_train.shape[1]]))]
    onnx_model = convert_sklearn(rf_model, initial_types=initial_type)
    with open(onnx_file, "wb") as f:
        f.write(onnx_model.SerializeToString())

    print(f"✅   The model has been trained and saved.   {model_file}")

else:
    print("✅ The form is currently loading....")

model = joblib.load(model_file)

# -------------------------------
# FastAPI
# -------------------------------
app = FastAPI(title="Predictive Maintenance API")

class SensorData(BaseModel):
    data: dict

df_sample = pd.read_csv(cleaned_file, nrows=1)
existing_columns = df_sample.drop(columns=['Failure', 'UDI', 'Product ID'], errors='ignore').columns.tolist()

@app.post("/predict")
def predict_failure(sensor: SensorData):
    try:
        df_input = pd.DataFrame([sensor.data])
        for col in existing_columns:
            if col not in df_input.columns:
                df_input[col] = 0

        if 'Process_Temperature_K' in df_input.columns and 'Air_Temperature_K' in df_input.columns:
            df_input['Temp_Diff'] = df_input['Process_Temperature_K'] - df_input['Air_Temperature_K']
        if 'Tool_Wear_min' in df_input.columns and 'Rotation_Speed_RPM' in df_input.columns:
            df_input['Tool_Wear_rate'] = df_input['Tool_Wear_min'] / (df_input['Rotation_Speed_RPM'] + 1e-3)

        if 'Machine_Type' in df_input.columns:
            df_input = pd.get_dummies(df_input, columns=['Machine_Type'])
            for col in existing_columns:
                if col not in df_input.columns:
                    df_input[col] = 0

        df_input = df_input[existing_columns]

        pred = model.predict(df_input)[0]
        prob = model.predict_proba(df_input)[0][1]

        if prob > 0.7:
            result = "⚠️ Cell membrane replacement within a day"
        elif prob > 0.4:
            result = "⚠️ Cell monitoring within 3 days "
        else:
            result = "✅ No glitch expected"
        return {"prediction": result, "failure_probability": float(prob)}

    except Exception as e:
        return {"error": str(e)}

# -------------------------------
# تشغيل السيرفر
# -------------------------------
if __name__ == "_main_":
    print("Server is running on: http://127.0.0.1:8000/docs")
    print("Press CTRL+C to stop the server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    