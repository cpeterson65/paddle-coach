# ----------------------------------------
# Paddle Coach Agent (Railway-ready)
# ----------------------------------------
import requests
from openai import OpenAI
import os
from datetime import datetime
from flask import Flask

app = Flask(__name__)

# ----------------------------------------
# API KEYS (from Railway Variables)
# ----------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

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
    STRAVA_ACCESS_TOKEN = get_strava_access_token()

    headers = {"Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"}
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities?per_page=50",
        headers=headers,
    )
    activities = response.json()

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
            avg_hr = act.get("average_heartrate")
            max_hr = act.get("max_heartrate")
            hr_text = ""
            if avg_hr:
                hr_text += f", avg HR {int(avg_hr)}"
            if max_hr:
                hr_text += f", max HR {int(max_hr)}"
            workout_summary += (
                f"{count + 1}. {date} - {name} - "
                f"{distance} mi, {moving_time} min{hr_text}\n"
            )
            count += 1

    prompt = f"""
You are an elite surfski coach.
Your job is to decide what I should do NEXT.
Use:
- Timing between workouts
- Heart rate (intensity)
- Volume trends
Workouts:
{workout_summary}
Give:
1. Tomorrow's workout (type + duration + intensity)
2. Risk level (low/medium/high)
3. Short reasoning (2-3 sentences)
"""

    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return workout_summary, ai_response.choices[0].message.content

# ----------------------------------------
# WEB PAGE
# ----------------------------------------
@app.route("/")
def home():
    workout_summary, advice = run_paddle_coach()
    return f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: 40px auto; padding: 20px;">
        <h1>🏄 Paddle Coach</h1>
        <h2>Your Recent Workouts</h2>
        <pre style="background:#f4f4f4; padding:15px; border-radius:8px;">{workout_summary}</pre>
        <h2>Coach Says</h2>
        <pre style="background:#e8f5e9; padding:15px; border-radius:8px;">{advice}</pre>
    </body>
    </html>
    """

# ----------------------------------------
# ENTRY POINT
# ----------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
