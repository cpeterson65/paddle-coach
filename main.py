import requests
from openai import OpenAI
import os
from datetime import datetime
from flask import Flask

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

UPCOMING_RACES = """
- Black Belt, Miami — April 18, 2026 (12 miles)
- Hollywood Jungle Row, Hollywood — April 26, 2026 (5 miles)
- Palm Beach Outrigger Fundraiser, Jupiter — May 23, 2026 (7 miles)
"""

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

def run_paddle_coach():
    STRAVA_ACCESS_TOKEN = get_strava_access_token()

    headers = {"Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"}
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities?per_page=50",
        headers=headers,
    )
    activities = response.json()
    if not isinstance(activities, list):
        return "Strava error: " + str(activities), "Could not get workouts from Strava.", ""

    workout_summary = ""
    count = 0
    max_workouts = 10
    today = datetime.now()
    is_tuesday = today.weekday() == 1

    for act in activities:
        if count >= max_workouts:
            break
        name = act.get("name", "").lower()
        sport = act.get("sport_type", "").lower()
        if "paddle" in name or "tnrl" in name or sport in ["ride", "kayaking", "canoeing"]:
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

    if is_tuesday:
        tnrl_note = "<p><strong>Tonight is TNRL race night — enjoy the race, no additional workout needed!</strong></p>"
    else:
        tnrl_note = ""

    prompt = f"""
You are an elite surfski coach. Your athlete is Chris, a competitive surfski paddler training for these upcoming races:
{UPCOMING_RACES}

Based on his recent workouts, give him a personalized coaching response with these four sections:

1. PERFORMANCE SUMMARY
One or two sentences summarizing his recent training load, intensity trends, and how well he is tracking toward his upcoming races.

2. TOMORROW'S WORKOUT
Specific workout recommendation (type, duration, intensity/heart rate target). Make sure it fits his race schedule — he needs to peak for Black Belt on April 18.

3. STROKE TIP
Give one specific, actionable surfski or K1 paddle stroke tip to work on. Reference techniques from coaches like those at Paddle2Fitness or K2NFitness. Be specific and practical.

4. COACH'S NOTE
One sentence of encouragement or race strategy advice based on where he is in his training cycle.

Keep each section brief and punchy. Write like a real coach, not a robot. No markdown symbols like ** or ###.

Recent workouts:
{workout_summary}
"""

    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return workout_summary, ai_response.choices[0].message.content, tnrl_note

@app.route("/")
def home():
    workout_summary, advice, tnrl_note = run_paddle_coach()
    paragraphs = ""
    for line in advice.strip().split("\n"):
        if line.strip():
            paragraphs += f"<p>{line.strip()}</p>"
    return f"""
    <html>
    <body style="font-family: Arial; max-width: 650px; margin: 40px auto; padding: 20px; line-height: 1.6;">
        <h1>Paddle Coach</h1>
        {tnrl_note}
        <h2>Your Recent Workouts</h2>
        <pre style="background:#f4f4f4; padding:15px; border-radius:8px; white-space: pre-wrap;">{workout_summary}</pre>
        <h2>Coach Says</h2>
        <div style="background:#e8f5e9; padding:15px; border-radius:8px;">
            {paragraphs}
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
