# ----------------------------------------
# Paddle Coach Agent (Railway-ready)
# ----------------------------------------
import requests
from openai import OpenAI
import os
from datetime import datetime
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import resend

# Import coaching sources and race schedule from separate files
from sources import SURFSKI_SOURCES, PRIMARY_SOURCE_NAMES
from races import UPCOMING_RACES

app = Flask(__name__)

# ----------------------------------------
# API KEYS (from Railway environment variables)
# ----------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
resend.api_key = RESEND_API_KEY

# ----------------------------------------
# FIGURE OUT WHICH RACES ARE STILL UPCOMING
# Automatically filters out races that have already passed
# ----------------------------------------
def get_future_races():
    today = datetime.now()
    future = []
    for race in UPCOMING_RACES:
        try:
            race_date = datetime.strptime(race["date"], "%B %d, %Y")
            if race_date >= today:
                future.append(race)
        except ValueError:
            # If date is approximate (like "October 2026"), always include it
            future.append(race)
    return future

def format_races_for_prompt(races):
    # Turn the race list into a readable string for the AI prompt
    lines = []
    for r in races:
        lines.append(f"- {r['name']} in {r['location']} on {r['date']} ({r['distance']})")
    return "\n".join(lines)

# ----------------------------------------
# GET A FRESH STRAVA TOKEN AUTOMATICALLY
# Strava tokens expire every 6 hours, so we fetch a new one each time
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
# Fetches Strava workouts and generates AI coaching advice
# ----------------------------------------
def run_paddle_coach():
    # Get a fresh Strava token
    STRAVA_ACCESS_TOKEN = get_strava_access_token()

    # Fetch the last 50 activities from Strava
    headers = {"Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"}
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities?per_page=50",
        headers=headers,
    )
    activities = response.json()

    # If Strava returns an error instead of a list, show it gracefully
    if not isinstance(activities, list):
        return "Strava error: " + str(activities), "Could not get workouts from Strava.", ""

    # ----------------------------------------
    # FILTER AND FORMAT WORKOUTS
    # Only include paddle-related activities, up to 10
    # ----------------------------------------
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

        # Include paddles, TNRL races, rides, kayaking, canoeing
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

    # ----------------------------------------
    # TUESDAY TNRL REMINDER
    # No workout needed on Tuesday race nights
    # ----------------------------------------
    if is_tuesday:
        tnrl_note = "<p><strong>🏁 Tonight is TNRL race night — enjoy the race, no additional workout needed!</strong></p>"
    else:
        tnrl_note = ""

    # ----------------------------------------
    # BUILD THE RACE LIST FOR THE PROMPT
    # Only show races that haven't happened yet
    # ----------------------------------------
    future_races = get_future_races()
    race_text = format_races_for_prompt(future_races)

    # ----------------------------------------
    # AI PROMPT
    # This is what gets sent to GPT to generate the coaching advice
    # ----------------------------------------
    prompt = f"""
You are an elite surfski coach. Your athlete is Chris, a competitive surfski paddler training for these upcoming races:
{race_text}

Based on his recent workouts, give him a personalized coaching response with these four sections:

1. PERFORMANCE SUMMARY
One or two sentences summarizing his recent training load, intensity trends, and how well he is tracking toward his upcoming races.

2. TOMORROW'S WORKOUT
Specific workout recommendation (type, duration, intensity/heart rate target). Make sure it fits his race schedule — he needs to peak for Black Belt on April 18.
Remember that on Tuesdays between March 1 and July 1, he has the TNRL race, which is usually 5 miles.

3. STROKE TIP
Give one specific, actionable surfski or K1 paddle stroke tip to work on.
Prioritize concepts and cues from these trusted coaching sources:
Mocke Paddling, Oscar Chalupsky, Ivan Lawler (Ultimate Kayaks),
K2N Online Paddle School, Paddle Monster, and Paddle 2 Fitness.
Be specific and practical — give Chris one thing to focus on, not a list.
At the end of the tip, briefly note the source.

4. COACH'S NOTE
One sentence of encouragement or race strategy advice based on where he is in his training cycle.

Keep each section brief and punchy. Write like a real coach, not a robot. No markdown symbols like ** or ###.

Recent workouts:
{workout_summary}
"""

    # ----------------------------------------
    # CALL OPENAI
    # Send the prompt and get the coaching response
    # ----------------------------------------
    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return workout_summary, ai_response.choices[0].message.content, tnrl_note

# ----------------------------------------
# SEND DAILY EMAIL
# Formats the coaching advice as a nice HTML email and sends it via Resend
# ----------------------------------------
def send_daily_email():
    print("Sending daily coaching email...")
    workout_summary, advice, tnrl_note = run_paddle_coach()

    # Format advice into paragraphs
    paragraphs = ""
    for line in advice.strip().split("\n"):
        if line.strip():
            paragraphs += f"<p>{line.strip()}</p>"

    html_content = f"""
    <div style="font-family: Arial; max-width: 650px; margin: 0 auto; padding: 20px; line-height: 1.6;">
        <h1>🏄 Your Daily Paddle Coach</h1>
        {tnrl_note}
        <h2>Your Recent Workouts</h2>
        <pre style="background:#f4f4f4; padding:15px; border-radius:8px; white-space: pre-wrap;">{workout_summary}</pre>
        <h2>Coach Says</h2>
        <div style="background:#e8f5e9; padding:15px; border-radius:8px;">
            {paragraphs}
        </div>
    </div>
    """

    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": "chris@chrispeterson.com",
        "subject": f"🏄 Paddle Coach — {datetime.now().strftime('%A, %B %d')}",
        "html": html_content,
    })
    print("Email sent!")

# ----------------------------------------
# SCHEDULER
# Runs send_daily_email automatically at 5pm Eastern every day
# ----------------------------------------
scheduler = BackgroundScheduler(timezone="America/New_York")
scheduler.add_job(send_daily_email, "cron", hour=17, minute=0)
scheduler.start()

# ----------------------------------------
# WEB PAGE
# This is what you see when you open the URL in your browser
# ----------------------------------------
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
        <h1>🏄 Paddle Coach</h1>
        {tnrl_note}
        <h2>Your Recent Workouts</h2>
