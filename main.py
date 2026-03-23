# ----------------------------------------
# Paddle Coach Agent (Railway-ready)
# ----------------------------------------
import requests
from openai import OpenAI
import os
from datetime import datetime

# ----------------------------------------
# API KEYS (from Railway Variables)
# ----------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------------------
# GET FRESH STRAVA TOKEN AUTOMATICALLY
# ----------------------------------------
def get_strava_access_token():
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "refresh_token": STRAVA_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
    )
    return response.json()["access_token"]

# ----------------------------------------
# MAIN FUNCTION
# ----------------------------------------
def run_paddle_coach():
    # Get a fresh token every time
    STRAVA_ACCESS_TOKEN = get_strava_access_token()

    # ----------------------------------------
    # GET STRAVA DATA
    # ----------------------------------------
    headers = {"Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"}
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities?per_page=50",
        headers=headers,
    )
    activities = response.json()
    print("STRAVA RESPONSE:", activities)

    # ----------------------------------------
    # FORMAT WORKOUTS (last 10 relevant)
    # ----------------------------------------
    workout_summary = ""
    count = 0
    max_workouts = 10

    for act in activities:
        if count >= max_workouts:
            break
        name = act.get("name", "").lower()
        sport = act.get("sport_type", "").lower()

        if "paddle" in name or sport in ["ride", "kayaking", "canoeing"]:
            distance = round(act.get("distance", 0) / 1609.34, 2)
            moving_time = round(act.get("moving_time", 0) / 60, 1)
            raw_date = act.get("start_date_local")
            date = ""
            if raw_date:
                dt = datetime.fromisoformat(raw_date.replace("Z", ""))
                date = dt.strftime("%b %d")
