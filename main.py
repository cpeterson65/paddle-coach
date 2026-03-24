# ----------------------------------------
# Paddle Coach Agent (Railway-ready)
# ----------------------------------------
import requests
from openai import OpenAI
import os
from datetime import datetime, timedelta
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import resend
import json

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
# SOURCE LINKS
# Used to make stroke tip sources clickable
# ----------------------------------------
SOURCE_LINKS = {
    "Mocke Paddling": "https://www.youtube.com/@mockepaddling6232",
    "Oscar Chalupsky": "https://www.youtube.com/results?search_query=Oscar+Chalupsky+surfski+technique",
    "Ivan Lawler": "https://www.youtube.com/playlist?list=PLUU4vHDSO0IpuQSyN3n74kxjwKfpZdk6G",
    "Ultimate Kayaks": "https://www.youtube.com/channel/UC8KuVUSSDZraBFmTwkIyOKA",
    "K2N Online Paddle School": "https://www.youtube.com/@K2NOPS",
    "K2N": "https://www.youtube.com/@K2NOPS",
    "Paddle Monster": "https://www.youtube.com/paddlemonster",
    "Paddle 2 Fitness": "https://www.youtube.com/@paddle2fitnesscoaching",
}

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
            future.append(race)
    return future


def format_races_for_prompt(races):
    lines = []
    for r in races:
        lines.append(f"- {r['name']} in {r['location']} on {r['date']} ({r['distance']})")
    return "\n".join(lines)


def get_next_race():
    future = get_future_races()
    if future:
        return future[0]
    return None


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
# CLASSIFY AN ACTIVITY
# Returns: 'paddle', 'race', 'strength', or None
# ----------------------------------------
def classify_activity(name, sport):
    name_lower = name.lower()
    sport_lower = sport.lower()

    if "tnrl" in name_lower or "race" in name_lower:
        return "race"

    if sport_lower in ["weighttraining", "workout"]:
        return "strength"

    if "paddle" in name_lower or sport_lower in ["ride", "kayaking", "canoeing"]:
        return "paddle"

    return None


# ----------------------------------------
# BUILD 14-DAY CHART DATA
# ----------------------------------------
def build_chart_data(activities):
    today = datetime.now().date()
    day_map = {}
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        day_map[d] = {"paddle": 0, "race": 0, "strength": False, "label": d.strftime("%a")[0]}

    for act in activities:
        raw_date = act.get("start_date_local")
        if not raw_date:
            continue
        act_date = datetime.fromisoformat(raw_date.replace("Z", "")).date()
        if act_date not in day_map:
            continue

        name = act.get("name", "")
        sport = act.get("sport_type", "")
        category = classify_activity(name, sport)

        if category == "strength":
            day_map[act_date]["strength"] = True
        elif category == "race":
            miles = round(act.get("distance", 0) / 1609.34, 2)
            day_map[act_date]["race"] += miles
        elif category == "paddle":
            miles = round(act.get("distance", 0) / 1609.34, 2)
            day_map[act_date]["paddle"] += miles

    return [day_map[d] for d in sorted(day_map.keys())]


# ----------------------------------------
# BUILD WORKOUT SUMMARY TEXT FOR AI
# ----------------------------------------
def build_workout_summary(activities):
    summary = ""
    count = 0
    for act in activities:
        if count >= 10:
            break
        name = act.get("name", "")
        sport = act.get("sport_type", "")
        category = classify_activity(name, sport)
        if category in ["paddle", "race"]:
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
            tag = " [RACE]" if category == "race" else ""
            summary += (
                f"{count + 1}. {date} - {name}{tag} - "
                f"{distance} mi, {moving_time} min{hr_text}\n"
            )
            count += 1
    return summary


# ----------------------------------------
# BUILD TRAINING CONTEXT SUMMARY FOR AI
# ----------------------------------------
def build_training_context(chart_data):
    rest_days = sum(1 for d in chart_data if d["paddle"] == 0 and d["race"] == 0 and not d["strength"])
    strength_days = sum(1 for d in chart_data if d["strength"])
    paddle_days = sum(1 for d in chart_data if d["paddle"] > 0 or d["race"] > 0)
    total_miles = sum(d["paddle"] + d["race"] for d in chart_data)

    last_paddle = None
    for i, d in enumerate(reversed(chart_data)):
        if d["paddle"] > 0 or d["race"] > 0:
            last_paddle = i
            break

    context = f"Last 14 days: {paddle_days} paddle days, {strength_days} strength days, {rest_days} rest days. "
    context += f"Total miles paddled: {round(total_miles, 1)}. "
    if last_paddle is not None:
        context += f"Last paddle was {last_paddle} day(s) ago."
    return context


# ----------------------------------------
# MAKE STROKE TIP SOURCE CLICKABLE
# ----------------------------------------
def linkify_source(tip_text, for_email=False):
    for source_name, url in SOURCE_LINKS.items():
        if source_name.lower() in tip_text.lower():
            if for_email:
                linked = '<a href="' + url + '" style="color:#0066cc;">' + source_name + '</a>'
            else:
                linked = '<a href="' + url + '" target="_blank" style="color:#0066cc; text-decoration:none; border-bottom:1px solid #0066cc;">' + source_name + '</a>'
            tip_text = tip_text.replace(source_name, linked)
            break
    return tip_text


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

    if not isinstance(activities, list):
        return None, "", "Strava error: " + str(activities), ""

    chart_data = build_chart_data(activities)
    workout_summary = build_workout_summary(activities)
    training_context = build_training_context(chart_data)

    today = datetime.now()
    is_tuesday = today.weekday() == 1
    tnrl_note = "Tonight is TNRL race night - enjoy the race, no additional workout needed!" if is_tuesday else ""

    future_races = get_future_races()
    race_text = format_races_for_prompt(future_races)
    next_race = get_next_race()
    next_race_text = (next_race["name"] + " on " + next_race["date"] + " (" + next_race["distance"] + ")") if next_race else "no upcoming races"

    prompt = (
        "You are an elite surfski coach writing a daily coaching briefing for Chris, "
        "a competitive surfski paddler in South Florida.\n\n"
        "UPCOMING RACES:\n" + race_text
        + "\n\nNEXT RACE: " + next_race_text
        + "\n\nRECENT TRAINING CONTEXT:\n" + training_context
        + "\n\nRECENT WORKOUTS (last 10 paddles):\n" + workout_summary
        + "\n\nWrite a coaching briefing with exactly these four sections. "
        "No markdown symbols like ** or ###. Write like a real coach, not a robot.\n\n"
        "1. PERFORMANCE SUMMARY\n"
        "Two sentences max. Assess his recent load and intensity. "
        "Tell him honestly how his training is tracking toward his next race.\n\n"
        "2. TOMORROW'S WORKOUT\n"
        "Design a specific session that fits his periodization toward the next race. "
        "Consider his rest days, strength days, and recent paddle intensity. "
        "Give him type, duration, and a specific heart rate target or effort level. "
        "If tomorrow is Tuesday between March and July, remind him about TNRL instead.\n\n"
        "3. STROKE TIP\n"
        "One specific, actionable technique cue - not a list. "
        "Draw from: Mocke Paddling, Oscar Chalupsky, Ivan Lawler, K2N Online Paddle School, "
        "Paddle Monster, or Paddle 2 Fitness. "
        "End with: (Source: [exact source name])\n\n"
        "4. COACH'S NOTE\n"
        "One sentence. Motivational or tactical. Make it feel personal to where Chris is right now.\n"
    )

    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return chart_data, workout_summary, ai_response.choices[0].message.content, tnrl_note


# ----------------------------------------
# PARSE AI ADVICE INTO SECTIONS
# ----------------------------------------
def parse_sections(advice):
    sections = {"PERFORMANCE SUMMARY": "", "TOMORROW'S WORKOUT": "", "STROKE TIP": "", "COACH'S NOTE": ""}
    current_section = None
    for line in advice.strip().split("\n"):
        stripped = line.strip()
        matched = False
        for key in sections:
            if key in stripped.upper():
                current_section = key
                matched = True
                break
        if not matched and current_section and stripped:
            sections[current_section] += stripped + " "
    return sections


# ----------------------------------------
# BUILD HTML PAGE (web or email)
# ----------------------------------------
def build_html_page(chart_data, advice, tnrl_note, is_email=False):
    sections = parse_sections(advice)
    sections["STROKE TIP"] = linkify_source(sections["STROKE TIP"].strip(), for_email=is_email)

    tnrl_html = ""
    if tnrl_note:
        if is_email:
            tnrl_html = '<div style="background:#fff3cd; border-radius:12px; padding:14px 18px; font-size:14px; font-weight:500; color:#856404; margin-bottom:20px;">' + tnrl_note + '</div>'
        else:
            tnrl_html = '<div class="tnrl-banner">' + tnrl_note + '</div>'

    if is_email:
        total_miles = sum(d["paddle"] + d["race"] for d in chart_data) if chart_data else 0
        paddle_days = sum(1 for d in chart_data if d["paddle"] > 0 or d["race"] > 0) if chart_data else 0

        return (
            "<!DOCTYPE html><html><head>"
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            "</head><body style=\"margin:0;padding:0;background:#ffffff;font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;\">"
            '<div style="max-width:600px;margin:0 auto;padding:32px 24px;">'
            '<div style="margin-bottom:24px;">'
            '<div style="font-size:12px;font-weight:600;letter-spacing:0.1em;color:#6e6e73;text-transform:uppercase;">Daily Briefing</div>'
            '<div style="font-size:28px;font-weight:700;color:#1d1d1f;margin-top:4px;">Paddle Coach</div>'
            '<div style="font-size:14px;color:#6e6e73;margin-top:2px;">' + datetime.now().strftime("%A, %B %d, %Y") + "</div>"
            "</div>"
            + tnrl_html
            + '<div style="display:flex;gap:16px;margin-bottom:24px;">'
            '<div style="flex:1;background:#f5f5f7;border-radius:12px;padding:16px;text-align:center;">'
            '<div style="font-size:28px;font-weight:600;color:#1d1d1f;">' + str(round(total_miles, 1)) + '</div>'
            '<div style="font-size:11px;color:#6e6e73;margin-top:4px;text-transform:uppercase;letter-spacing:0.05em;">Miles / 14 Days</div>'
            "</div>"
            '<div style="flex:1;background:#f5f5f7;border-radius:12px;padding:16px;text-align:center;">'
            '<div style="font-size:28px;font-weight:600;color:#1d1d1f;">' + str(paddle_days) + '</div>'
            '<div style="font-size:11px;color:#6e6e73;margin-top:4px;text-transform:uppercase;letter-spacing:0.05em;">Paddle Days</div>'
            "</div></div>"
            '<div style="border-top:1px solid #e5e5ea;padding-top:20px;margin-bottom:20px;">'
            '<div style="font-size:11px;font-weight:600;letter-spacing:0.1em;color:#6e6e73;text-transform:uppercase;margin-bottom:8px;">Performance Summary</div>'
            '<div style="font-size:15px;color:#1d1d1f;line-height:1.65;">' + sections["PERFORMANCE SUMMARY"] + "</div></div>"
            '<div style="border-top:1px solid #e5e5ea;padding-top:20px;margin-bottom:20px;">'
            '<div style="font-size:11px;font-weight:600;letter-spacing:0.1em;color:#6e6e73;text-transform:uppercase;margin-bottom:8px;">Tomorrow\'s Workout</div>'
            '<div style="font-size:15px;color:#1d1d1f;line-height:1.65;">' + sections["TOMORROW'S WORKOUT"] + "</div></div>"
            '<div style="border-top:1px solid #e5e5ea;padding-top:20px;margin-bottom:20px;">'
            '<div style="font-size:11px;font-weight:600;letter-spacing:0.1em;color:#6e6e73;text-transform:uppercase;margin-bottom:8px;">Stroke Tip</div>'
            '<div style="font-size:15px;color:#1d1d1f;line-height:1.65;">' + sections["STROKE TIP"] + "</div></div>"
            '<div style="border-top:1px solid #e5e5ea;padding-top:20px;margin-bottom:32px;">'
            '<div style="font-size:11px;font-weight:600;letter-spacing:0.1em;color:#6e6e73;text-transform:uppercase;margin-bottom:8px;">Coach\'s Note</div>'
            '<div style="font-size:15px;color:#1d1d1f;line-height:1.65;font-style:italic;">' + sections["COACH'S NOTE"] + "</div></div>"
            '<div style="font-size:12px;color:#aeaeb2;text-align:center;border-top:1px solid #e5e5ea;padding-top:20px;">'
            "Paddle Coach &bull; Your AI surfski training assistant</div>"
            "</div></body></html>"
        )

    # Web version with Chart.js
    labels = json.dumps([d["label"] for d in chart_data])
    paddle_data = json.dumps([round(d["paddle"], 2) for d in chart_data])
    race_data = json.dumps([round(d["race"], 2) for d in chart_data])
    strength_data = json.dumps([3 if d["strength"] else 0 for d in chart_data])

    return (
        "<!DOCTYPE html><html lang='en'><head>"
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Paddle Coach</title>"
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>'
        "<style>"
        "* { box-sizing: border-box; margin: 0; padding: 0; }"
        "body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; background: #f5f5f7; color: #1d1d1f; min-height: 100vh; }"
        ".container { max-width: 680px; margin: 0 auto; padding: 40px 20px 60px; }"
        ".header { margin-bottom: 28px; }"
        ".header-label { font-size: 12px; font-weight: 600; letter-spacing: 0.1em; color: #6e6e73; text-transform: uppercase; }"
        ".header-title { font-size: 34px; font-weight: 700; color: #1d1d1f; margin-top: 4px; letter-spacing: -0.5px; }"
        ".header-date { font-size: 15px; color: #6e6e73; margin-top: 4px; }"
        ".tnrl-banner { background: #fff3cd; border-radius: 12px; padding: 14px 18px; font-size: 14px; font-weight: 500; color: #856404; margin-bottom: 16px; }"
        ".card { background: #ffffff; border-radius: 16px; padding: 22px 24px; margin-bottom: 14px; }"
        ".card-label { font-size: 11px; font-weight: 600; letter-spacing: 0.1em; color: #6e6e73; text-transform: uppercase; margin-bottom: 10px; }"
        ".card-content { font-size: 15px; line-height: 1.65; color: #1d1d1f; }"
        ".card-content.italic { font-style: italic; }"
        ".chart-wrap { position: relative; height: 130px; }"
        ".legend { display: flex; gap: 16px; margin-top: 12px; flex-wrap: wrap; }"
        ".legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6e6e73; }"
        ".legend-dot { width: 10px; height: 10px; border-radius: 2px; }"
        "@media (max-width: 480px) { .header-title { font-size: 26px; } .container { padding: 24px 16px 40px; } }"
        "</style></head><body>"
        '<div class="container">'
        '<div class="header">'
        '<div class="header-label">Daily Briefing</div>'
        '<div class="header-title">Paddle Coach</div>'
        '<div class="header-date">' + datetime.now().strftime("%A, %B %d, %Y") + "</div>"
        "</div>"
        + tnrl_html
        + '<div class="card">'
        '<div class="card-label">Last 14 Days</div>'
        '<div class="chart-wrap"><canvas id="trainingChart"></canvas></div>'
        '<div class="legend">'
        '<div class="legend-item"><div class="legend-dot" style="background:#3a7bd5;"></div>Paddle</div>'
        '<div class="legend-item"><div class="legend-dot" style="background:#ff6b35;"></div>Race</div>'
        '<div class="legend-item"><div class="legend-dot" style="background:#34c759;"></div>Strength</div>'
        "</div></div>"
        '<div class="card"><div class="card-label">Performance Summary</div>'
        '<div class="card-content">' + sections["PERFORMANCE SUMMARY"] + "</div></div>"
        '<div class="card"><div class="card-label">Tomorrow\'s Workout</div>'
        '<div class="card-content">' + sections["TOMORROW'S WORKOUT"] + "</div></div>"
        '<div class="card"><div class="card-label">Stroke Tip</div>'
        '<div class="card-content">' + sections["STROKE TIP"] + "</div></div>"
        '<div class="card"><div class="card-label">Coach\'s Note</div>'
        '<div class="card-content italic">' + sections["COACH'S NOTE"] + "</div></div>"
        "</div>"
        "<script>"
        'const ctx = document.getElementById("trainingChart").getContext("2d");'
        "new Chart(ctx, {"
        'type: "bar",'
        "data: {"
        "labels: " + labels + ","
        "datasets: ["
        '{ label: "Paddle", data: ' + paddle_data + ', backgroundColor: "#3a7bd5", borderRadius: 4, stack: "stack" },'
'{ label: "Race", data: ' + race_data + ', backgroundColor: "#ff6b35", borderRadius: 4, stack: "stack" },'
'{ label: "Strength", data: ' + strength_data + ', backgroundColor: "#34c759", borderRadius: 4, stack: "stack" }'
        "]},"
        "options: {"
        "responsive: true, maintainAspectRatio: false,"
        "plugins: { legend: { display: false }, tooltip: { callbacks: { label: function(c) {"
        'if (c.dataset.label === "Strength") return "Strength training";'
        'return c.dataset.label + ": " + c.raw + " mi";'
        "}}}},"
        "scales: {"
        'x: { grid: { display: false }, ticks: { font: { size: 10 }, color: "#6e6e73" }, offset: true },'
        'y: { grid: { color: "#f0f0f0" }, ticks: { font: { size: 10 }, color: "#6e6e73" }, beginAtZero: true }'
        "}}}); </script></body></html>"
    )


# ----------------------------------------
# SEND DAILY EMAIL AT 9PM EASTERN
# ----------------------------------------
def send_daily_email():
    print("Sending daily coaching email...")
    chart_data, workout_summary, advice, tnrl_note = run_paddle_coach()
    html_content = build_html_page(chart_data, advice, tnrl_note, is_email=True)
    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": "chris@chrispeterson.com",
        "subject": "Paddle Coach - " + datetime.now().strftime("%A, %B %d"),
        "html": html_content,
    })
    print("Email sent!")


# ----------------------------------------
# SCHEDULER - 9pm Eastern daily
# ----------------------------------------
scheduler = BackgroundScheduler(timezone="America/New_York")
scheduler.add_job(send_daily_email, "cron", hour=21, minute=0)
scheduler.start()


# ----------------------------------------
# WEB ROUTE
# ----------------------------------------
@app.route("/")
def home():
    chart_data, workout_summary, advice, tnrl_note = run_paddle_coach()
    return build_html_page(chart_data, advice, tnrl_note, is_email=False)


# ----------------------------------------
# ENTRY POINT
# ----------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
