from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import requests
import os
from dotenv import load_dotenv

# ── Local DB modules ────────────────────────────────────────────────────────
from auth_db import register_user, verify_user
from data_db import log_prediction, get_user_predictions

load_dotenv()

app = FastAPI(title="KisanConnect AI-Based Crop Recommendation System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load ML model ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, 'saved_models', 'crop_model.pkl')
try:
    model = joblib.load(model_path)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Warning: Model not found at {model_path}. Please train the model first.")
    model = None

# ── Pydantic schemas ─────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CropPredictionRequest(BaseModel):
    N: float
    P: float
    K: float
    ph: float
    location: str
    username: str = "anonymous"   # passed from frontend after login

# ── Weather helper ───────────────────────────────────────────────────────────
WEATHER_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY', 'YOUR_DUMMY_KEY')

def fetch_weather_data(location: str):
    if WEATHER_API_KEY == 'YOUR_DUMMY_KEY':
        return {"temperature": 25.0, "humidity": 70.0, "rainfall": 100.0}
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={location}&appid={WEATHER_API_KEY}&units=metric"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return {"temperature": 25.0, "humidity": 70.0, "rainfall": 100.0}
    data = response.json()
    temp = data['main']['temp']
    humidity = data['main']['humidity']
    rainfall = 100.0
    if 'rain' in data and '1h' in data['rain']:
        rainfall = data['rain']['1h'] * 24 * 30
    return {"temperature": temp, "humidity": humidity, "rainfall": rainfall}

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "Welcome to KisanConnect API"}


@app.post("/register")
def register(req: RegisterRequest):
    """Register a new user. Credentials are stored in users.db."""
    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    result = register_user(req.username.strip(), req.email.strip(), req.password)
    if not result["success"]:
        raise HTTPException(status_code=409, detail=result["error"])
    return {"message": "Registration successful. You can now log in."}


@app.post("/login")
def login(req: LoginRequest):
    """Verify credentials against users.db and return success."""
    result = verify_user(req.username.strip(), req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return {"message": "Login successful.", "username": result["username"]}


@app.post("/predict")
def predict_crop(request: CropPredictionRequest):
    """Run ML prediction and log the result to predictions.db."""
    if model is None:
        raise HTTPException(status_code=500, detail="ML Model not loaded.")

    weather = fetch_weather_data(request.location)

    features = np.array([[
        request.N, request.P, request.K,
        weather['temperature'], weather['humidity'],
        request.ph, weather['rainfall']
    ]])

    probabilities = model.predict_proba(features)[0]
    classes = model.classes_
    top_indices = np.argsort(probabilities)[::-1][:3]
    top_crops = [
        {"crop": str(classes[i]).capitalize(), "confidence": round(float(probabilities[i]) * 100, 2)}
        for i in top_indices
    ]

    is_suitable = True
    alert_message = ""
    if request.ph < 4.0 or request.ph > 9.0:
        is_suitable = False
        alert_message = (
            f"Warning: Extreme soil pH ({request.ph}). "
            "Most crops require a pH between 5.5 and 7.5. Consider soil amendment."
        )
    elif top_crops[0]['confidence'] < 30.0:
        is_suitable = False
        alert_message = (
            "Warning: Low suitability for known crops based on these exact conditions. "
            "The confidence is very low. You may need to alter your soil composition."
        )

    # ── Persist to predictions.db ────────────────────────────────────────────
    log_prediction(
        username=request.username,
        inputs={"N": request.N, "P": request.P, "K": request.K,
                "ph": request.ph, "location": request.location},
        weather=weather,
        top_crops=top_crops,
        is_suitable=is_suitable,
        alert_message=alert_message,
    )

    return {
        "is_suitable": is_suitable,
        "alert_message": alert_message,
        "top_crops": top_crops,
        "weather_data_used": weather,
    }


@app.get("/history/{username}")
def prediction_history(username: str):
    """Return all past predictions for a given user from predictions.db."""
    records = get_user_predictions(username)
    return {"username": username, "history": records}
