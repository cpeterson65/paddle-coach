# ----------------------------------------
# Paddle Coach Agent (Railway-ready)
# ----------------------------------------
import requests
from openai import OpenAI
import os
from datetime import datetime, timedelta
from flask import Flask
import json
import pytz

# ----------------------------------------
# TIMEZONE HELPER
# Always use Eastern time so dates are correct in both the web
# version and the scheduled 9pm email. Railway servers run in UTC
# which is why the email was showing the wrong day.
# ----------------------------------------
EASTERN = pytz.timezone("America/New_York")

def now_eastern():
    return datetime.now(EASTERN)

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

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------------------
# SOURCE LINKS
# Used to make stroke tip sources clickable when a URL is available.
# If a source name appears in the tip but has no link, it shows as plain text.
# ----------------------------------------
SOURCE_LINKS = {
    "Boyan Zlatarev": "https://www.surfskicenter.com/zen-master-blog",
    "Surfski Center Tarifa": "https://www.surfskicenter.com/zen-master-blog",
    "Mocke Paddling": "https://www.youtube.com/@mockepaddling6232",
    "Oscar Chalupsky": "https://www.coachchalupsky.com",
    "Ivan Lawler": "https://www.youtube.com/playlist?list=PLUU4vHDSO0IpuQSyN3n74kxjwKfpZdk6G",
    "Ultimate Kayaks": "https://www.youtube.com/channel/UC8KuVUSSDZraBFmTwkIyOKA",
    "Greg Barton": "https://www.epickayaks.com/post/technique-series",
    "Epic Kayaks": "https://www.epickayaks.com/post/technique-series",
    "Sean Rice": "http://www.yourpaddlelife.com",
    "PaddleLife": "http://www.yourpaddlelife.com",
    "K2N Online Paddle School": "https://www.youtube.com/@K2NOPS",
    "K2N": "https://www.youtube.com/@K2NOPS",
    "Paddle 2 Fitness": "https://www.youtube.com/@paddle2fitnesscoaching",
    "Julian Norton-Smith": "https://www.youtube.com/@paddle2fitnesscoaching",
    "Paddle Monster": "https://www.youtube.com/paddlemonster",
}

# ----------------------------------------
# FIGURE OUT WHICH RACES ARE STILL UPCOMING
# Automatically filters out races that have already passed
# ----------------------------------------
def get_future_races():
    today = now_eastern().replace(tzinfo=None)
    future = []
    for race in UPCOMING_RACES:
        try:
            race_date = datetime.strptime(race["date"], "%B %d, %Y")
            if race_date >= today:
                future.append(race)
        except ValueError:
            # Approximate dates (e.g. "October 2026") are always included
            future.append(race)
    return future


def format_races_for_prompt(races):
    lines = []
    for r in races:
        lines.append(f"- {r['name']} in {r['location']} on {r['date']} ({r['distance']})")
    return "\n".join(lines)


def get_next_race():
    future = get_future_races()
    return future[0] if future else None


def days_until_race(race):
    # Returns how many days until a race, used for periodization
    try:
        race_date = datetime.strptime(race["date"], "%B %d, %Y")
        return (race_date - now_eastern().replace(tzinfo=None)).days
    except ValueError:
        return 999


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
# Returns: 'paddle', 'race', 'strength', or None (skip it)
# ----------------------------------------
def classify_activity(name, sport):
    name_lower = name.lower()
    sport_lower = sport.lower()

    # Race activities — TNRL or "race" in the name
    if "tnrl" in name_lower or "race" in name_lower:
        return "race"

    # Strength training — Strava logs these as Weight Training or Workout
    if sport_lower in ["weighttraining", "workout"]:
        return "strength"

    # Paddle activities — kayak, ride used as kayak, canoeing
    if "paddle" in name_lower or sport_lower in ["ride", "kayaking", "canoeing"]:
        return "paddle"

    return None


# ----------------------------------------
# DETECT INTERVAL SESSIONS
# Returns True if the activity name suggests intervals.
# Chris will name sessions with "interval", "intervals", or "int"
# ----------------------------------------
def is_interval_session(name):
    name_lower = name.lower()
    keywords = ["interval", "intervals", " int ", "int-", "tempo", "threshold", "fartlek"]
    return any(k in name_lower for k in keywords)


# ----------------------------------------
# BUILD 14-DAY CHART DATA
# Includes miles (paddle/race) and suffer score (relative effort) per day
# ----------------------------------------
def build_chart_data(activities):
    today = now_eastern().date()
    day_map = {}
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        day_map[d] = {
            "paddle": 0,
            "race": 0,
            "interval": 0,
            "strength": False,
            "suffer_score": 0,
            "label": d.strftime("%a")[0],  # Single letter day: M T W T F S S
        }

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

        # Add suffer score (Strava's relative effort) for any paddle/race activity
        suffer = act.get("suffer_score") or 0

        if category == "strength":
            day_map[act_date]["strength"] = True
        elif category == "race":
            miles = round(act.get("distance", 0) / 1609.34, 2)
            day_map[act_date]["race"] += miles
            day_map[act_date]["suffer_score"] += suffer
        elif category == "paddle":
            miles = round(act.get("distance", 0) / 1609.34, 2)
            if is_interval_session(name):
                day_map[act_date]["interval"] += miles
            else:
                day_map[act_date]["paddle"] += miles
            day_map[act_date]["suffer_score"] += suffer

    return [day_map[d] for d in sorted(day_map.keys())]


# ----------------------------------------
# BUILD WORKOUT SUMMARY TEXT FOR AI
# Last 10 paddle/race activities formatted as text
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
            suffer = act.get("suffer_score")
            hr_text = ""
            if avg_hr:
                hr_text += f", avg HR {int(avg_hr)}"
            if max_hr:
                hr_text += f", max HR {int(max_hr)}"
            if suffer:
                hr_text += f", effort {int(suffer)}"
            # Tag races and interval sessions so the AI can see them clearly
            if category == "race":
                tag = " [RACE]"
            elif is_interval_session(name):
                tag = " [INTERVALS]"
            else:
                tag = ""
            summary += (
                f"{count + 1}. {date} - {name}{tag} - "
                f"{distance} mi, {moving_time} min{hr_text}\n"
            )
            count += 1
    return summary


# ----------------------------------------
# BUILD TRAINING CONTEXT SUMMARY FOR AI
# Gives the AI a clear picture of recent load, rest, and race timing
# ----------------------------------------
def build_training_context(chart_data):
    rest_days = sum(1 for d in chart_data if d["paddle"] == 0 and d["race"] == 0 and not d["strength"])
    strength_days = sum(1 for d in chart_data if d["strength"])
    paddle_days = sum(1 for d in chart_data if d["paddle"] > 0 or d["race"] > 0)
    total_miles = sum(d["paddle"] + d["race"] for d in chart_data)
    total_effort = sum(d["suffer_score"] for d in chart_data)

    # Find how many days ago the last paddle was
    last_paddle = None
    for i, d in enumerate(reversed(chart_data)):
        if d["paddle"] > 0 or d["race"] > 0:
            last_paddle = i
            break

    # Find consecutive rest days leading up to today
    consecutive_rest = 0
    for d in reversed(chart_data):
        if d["paddle"] == 0 and d["race"] == 0 and not d["strength"]:
            consecutive_rest += 1
        else:
            break

    context = f"Last 14 days: {paddle_days} paddle days, {strength_days} strength days, {rest_days} rest days. "
    context += f"Total miles: {round(total_miles, 1)}. Total relative effort: {int(total_effort)}. "
    if last_paddle is not None:
        context += f"Last paddle was {last_paddle} day(s) ago. "
    if consecutive_rest >= 2:
        context += f"Chris has had {consecutive_rest} consecutive rest days — body is likely recovered and ready for a quality session. "
    elif consecutive_rest == 0:
        context += "Chris paddled today or yesterday — consider recovery needs. "

    # IMPORTANT: prevent consistency contradiction
    # If the most recent session was short or low effort, assume it was intentional recovery
    # Do not flag it as inconsistency or poor performance
    context += (
        "IMPORTANT COACHING RULE: If the most recent session was short, easy, or low effort, "
        "assume it was intentional recovery — do not criticize it or describe it as inconsistent. "
        "Only flag inconsistency if there is a clear multi-day pattern of missed sessions without explanation. "
    )

    return context


# ----------------------------------------
# MAKE STROKE TIP SOURCE CLICKABLE
# If the source has a known URL, wraps it in a link.
# If no URL is found, displays the source name as plain text — no link required.
# ----------------------------------------
def linkify_source(tip_text, for_email=False):
    for source_name, url in SOURCE_LINKS.items():
        if source_name.lower() in tip_text.lower():
            if for_email:
                linked = '<a href="' + url + '" style="color:#0066cc;">' + source_name + '</a>'
            else:
                linked = '<a href="' + url + '" target="_blank" style="color:#0066cc; text-decoration:none; border-bottom:1px solid #0066cc;">' + source_name + '</a>'
            # Case-insensitive replace
            import re
            tip_text = re.sub(re.escape(source_name), linked, tip_text, flags=re.IGNORECASE, count=1)
            return tip_text
    # No matching link found — return tip as-is, source credit shown as plain text
    return tip_text


# ----------------------------------------
# MAIN FUNCTION
# Fetches Strava data and generates AI coaching advice
# ----------------------------------------
def run_paddle_coach():
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
        return None, "", "Strava error: " + str(activities), ""

    chart_data = build_chart_data(activities)
    workout_summary = build_workout_summary(activities)
    training_context = build_training_context(chart_data)

    today = now_eastern()
    is_tuesday = today.weekday() == 1
    tomorrow_is_tuesday = (today.weekday() + 1) % 7 == 1
    tnrl_note = "Tonight is TNRL race night - enjoy the race, no additional workout needed!" if is_tuesday else ""

    future_races = get_future_races()
    race_text = format_races_for_prompt(future_races)
    next_race = get_next_race()
    next_race_text = (
        next_race["name"] + " on " + next_race["date"] + " (" + next_race["distance"] + ")"
        + " — " + str(days_until_race(next_race)) + " days away"
    ) if next_race else "no upcoming races"

    # ----------------------------------------
    # AI PROMPT
    # Updated with: rest day suggestions, smarter periodization,
    # broader source list, and source-optional stroke tips
    # ----------------------------------------
    prompt = (
        "You are an elite surfski coach writing a daily coaching briefing for Chris, "
        "a competitive surfski paddler in South Florida.\n\n"
        "UPCOMING RACES:\n" + race_text
        + "\n\nNEXT RACE: " + next_race_text
        + "\n\nRECENT TRAINING CONTEXT:\n" + training_context
        + "\n\nRECENT WORKOUTS (last 10 paddles, most recent first):\n" + workout_summary
        + "\n\nWrite a coaching briefing with exactly these four sections. "
        "No markdown symbols like ** or ###. Write like a real coach, not a robot.\n\n"

        "1. PERFORMANCE SUMMARY\n"
        "Two sentences max. Assess his recent load, intensity, and relative effort trends. "
        "Tell him honestly how his training is tracking toward his next race.\n\n"

        "2. NEXT WORKOUT\n"
        "Design the next session that fits his periodization toward the next race. "
        "Rules:\n"
        "- If he has had 2 or more consecutive rest days, the body is recovered — prescribe a quality session.\n"
        "- If he has paddled hard multiple days in a row with high effort scores, prescribe recovery or rest.\n"
        "- Vary session types across the week: mix long endurance, intervals, and easy recovery paddles.\n"
        "- Interval sessions are shown as [INTERVALS] in the workout list — use these to gauge how recently he has done high-intensity work.\n"
        "- If he has not done an interval session in 4 or more days and is not in taper, consider prescribing one.\n"
        "- In the 2 weeks before a race, taper: reduce volume, maintain some intensity.\n"
        "- In the week before a race, prescribe mostly easy paddling or rest.\n"
        "- On race day itself, just a brief warm-up paddle.\n"
        "- If tomorrow is a Tuesday between March 1 and July 1, remind him about TNRL instead of prescribing a workout.\n"
        "- If a rest day is genuinely the right call, say so clearly and explain why.\n"
        "- Do NOT criticize a recent easy or short session — assume it was intentional recovery.\n"
        "Give type, duration, and a specific heart rate target or effort level.\n"
        "Then on a new line, add one natural sentence previewing the following 3 sessions in simple terms "
        "(session types only, e.g. After this, plan for an interval session, a long easy paddle, and a rest day.).\n\n"

        "3. STROKE TIP\n"
        "One specific, actionable technique cue for surfski or K1 paddling — not a list. "
        "Draw from these trusted coaches — rotate between them and do not over-rely on any single source: "
        "Boyan Zlatarev (Surfski Center Tarifa), Mocke Paddling (Dawid & Jasper Mocke), "
        "Ivan Lawler, Greg Barton, Sean Rice (PaddleLife), K2N Online Paddle School, "
        "Paddle 2 Fitness (Julian Norton-Smith), Oscar Chalupsky. "
        "Treat all of these coaches as equally weighted — vary your selections across days. "
        "The tip must be applicable to surfski or K1 — not SUP-only or OC-only technique. "
        "Downwind technique, wave reading, and ocean racing tips are all valid. "
        "End with: (Source: [exact coach or source name]) — even if no video link is available, always credit the source.\n"
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
    sections = {"PERFORMANCE SUMMARY": "", "NEXT WORKOUT": "", "STROKE TIP": ""}
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
# BUILD CHART JS SCRIPT
# Shared between web and email versions
# ----------------------------------------
def build_chart_script(chart_data, canvas_id, chart_type="miles"):
    labels = json.dumps([d["label"] for d in chart_data])

    if chart_type == "miles":
        paddle_data = json.dumps([round(d["paddle"], 2) for d in chart_data])
        interval_data = json.dumps([round(d["interval"], 2) for d in chart_data])
        race_data = json.dumps([round(d["race"], 2) for d in chart_data])
        strength_data = json.dumps([3 if d["strength"] else 0 for d in chart_data])
        y_label = "Miles"
        tooltip_cb = (
            'if (c.dataset.label === "Strength") return "Strength training";'
            'return c.dataset.label + ": " + c.raw + " mi";'
        )
        datasets = (
            '{ label: "Paddle", data: ' + paddle_data + ', backgroundColor: "#3a7bd5", borderRadius: 4, stack: "stack" },'
            '{ label: "Intervals", data: ' + interval_data + ', backgroundColor: "#9b59b6", borderRadius: 4, stack: "stack" },'
            '{ label: "Race", data: ' + race_data + ', backgroundColor: "#ff6b35", borderRadius: 4, stack: "stack" },'
            '{ label: "Strength", data: ' + strength_data + ', backgroundColor: "#34c759", borderRadius: 4, stack: "stack" }'
        )
    else:
        # Effort / suffer score chart — same colors, different metric
        paddle_effort = json.dumps([int(d["suffer_score"]) if d["paddle"] > 0 else 0 for d in chart_data])
        race_effort = json.dumps([int(d["suffer_score"]) if d["race"] > 0 else 0 for d in chart_data])
        strength_data = json.dumps([20 if d["strength"] else 0 for d in chart_data])
        tooltip_cb = (
            'if (c.dataset.label === "Strength") return "Strength training";'
            'return c.dataset.label + " effort: " + c.raw;'
        )
        datasets = (
            '{ label: "Paddle", data: ' + paddle_effort + ', backgroundColor: "#3a7bd5", borderRadius: 4, stack: "stack" },'
            '{ label: "Race", data: ' + race_effort + ', backgroundColor: "#ff6b35", borderRadius: 4, stack: "stack" },'
            '{ label: "Strength", data: ' + strength_data + ', backgroundColor: "#34c759", borderRadius: 4, stack: "stack" }'
        )

    return (
        'const ctx' + canvas_id + ' = document.getElementById("' + canvas_id + '").getContext("2d");'
        'new Chart(ctx' + canvas_id + ', {'
        'type: "bar",'
        'data: { labels: ' + labels + ', datasets: [' + datasets + '] },'
        'options: {'
        'responsive: true, maintainAspectRatio: false,'
        'plugins: { legend: { display: false }, tooltip: { callbacks: { label: function(c) {' + tooltip_cb + '} } } },'
        'scales: {'
        'x: { grid: { display: false }, ticks: { font: { size: 10 }, color: "#6e6e73" }, offset: true },'
        'y: { grid: { color: "#f0f0f0" }, ticks: { font: { size: 10 }, color: "#6e6e73" }, beginAtZero: true }'
        '} } });'
    )


# ----------------------------------------
# BUILD EMAIL CHART AS INLINE SVG TABLE
# Email clients don't support Chart.js, so we render a simple
# inline SVG bar chart that works in any email client
# ----------------------------------------
def build_email_chart_svg(chart_data, chart_type="miles"):
    width = 560
    height = 100
    bar_area_height = 75
    n = len(chart_data)
    bar_width = int(width / n * 0.6)
    bar_gap = int(width / n)

    if chart_type == "miles":
        values_paddle = [d["paddle"] for d in chart_data]
        values_interval = [d["interval"] for d in chart_data]
        values_race = [d["race"] for d in chart_data]
        values_strength = [3 if d["strength"] else 0 for d in chart_data]
        unit = "mi"
    else:
        values_paddle = [d["suffer_score"] if d["paddle"] > 0 else 0 for d in chart_data]
        values_race = [d["suffer_score"] if d["race"] > 0 else 0 for d in chart_data]
        values_strength = [20 if d["strength"] else 0 for d in chart_data]
        unit = "effort"

    values_interval = locals().get('values_interval', [0]*14)
    all_vals = [p + iv + r + s for p, iv, r, s in zip(values_paddle, values_interval, values_race, values_strength)]
    max_val = max(all_vals) if max(all_vals) > 0 else 1

    bars = ""
    labels_svg = ""
    for i, d in enumerate(chart_data):
        x = int(i * bar_gap + bar_gap / 2 - bar_width / 2)
        label = d["label"]

        # Stacked: paddle + race + strength
        p = values_paddle[i]
        iv = values_interval[i] if 'values_interval' in dir() else 0
        r = values_race[i]
        s = values_strength[i]

        def bar_h(v):
            return max(2, int(v / max_val * bar_area_height)) if v > 0 else 0

        ph = bar_h(p)
        ivh = bar_h(iv)
        rh = bar_h(r)
        sh = bar_h(s)

        # Draw from bottom up: strength, race, intervals, paddle
        y_bottom = bar_area_height
        if sh > 0:
            bars += f'<rect x="{x}" y="{y_bottom - sh}" width="{bar_width}" height="{sh}" fill="#34c759" rx="2"/>'
            y_bottom -= sh
        if rh > 0:
            bars += f'<rect x="{x}" y="{y_bottom - rh}" width="{bar_width}" height="{rh}" fill="#ff6b35" rx="2"/>'
            y_bottom -= rh
        if ivh > 0:
            bars += f'<rect x="{x}" y="{y_bottom - ivh}" width="{bar_width}" height="{ivh}" fill="#9b59b6" rx="2"/>'
            y_bottom -= ivh
        if ph > 0:
            bars += f'<rect x="{x}" y="{y_bottom - ph}" width="{bar_width}" height="{ph}" fill="#3a7bd5" rx="2"/>'

        label_x = int(i * bar_gap + bar_gap / 2)
        labels_svg += f'<text x="{label_x}" y="{bar_area_height + 14}" text-anchor="middle" font-size="9" fill="#6e6e73" font-family="Arial,sans-serif">{label}</text>'

    svg = (
        f'<svg width="100%" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        + bars + labels_svg
        + '</svg>'
    )
    return svg


# ----------------------------------------
# BUILD HTML PAGE (web or email)
# ----------------------------------------
def build_html_page(chart_data, advice, tnrl_note):
    sections = parse_sections(advice)
    sections["STROKE TIP"] = linkify_source(sections["STROKE TIP"].strip())

    tnrl_html = ""
    if tnrl_note:
        tnrl_html = '<div class="tnrl-banner">' + tnrl_note + '</div>'

    # ----------------------------------------
    # WEB VERSION
    # Uses Chart.js for interactive charts
    # ----------------------------------------
    chart_script_miles = build_chart_script(chart_data, "trainingChart", "miles")
    chart_script_effort = build_chart_script(chart_data, "effortChart", "effort")

    return (
        "<!DOCTYPE html><html lang='en'><head>"
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
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
        ".chart-wrap { position: relative; height: 120px; }"
        ".legend { display: flex; gap: 16px; margin-top: 10px; flex-wrap: wrap; }"
        ".legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6e6e73; }"
        ".legend-dot { width: 10px; height: 10px; border-radius: 2px; }"
        "@media (max-width: 480px) { .header-title { font-size: 26px; } .container { padding: 24px 16px 40px; } }"
        "</style></head><body>"
        '<div class="container">'

        '<div class="header">'
        '<div class="header-label">Daily Briefing</div>'
        '<div class="header-title">Paddle Coach</div>'
        '<div class="header-date">' + now_eastern().strftime("%A, %B %d, %Y") + '</div>'
        '</div>'

        + tnrl_html

        # Miles chart
        + '<div class="card">'
        '<div class="card-label">Miles — Last 14 Days</div>'
        '<div class="chart-wrap"><canvas id="trainingChart"></canvas></div>'
        '<div class="legend">'
        '<div class="legend-item"><div class="legend-dot" style="background:#3a7bd5;"></div>Paddle</div>'
        '<div class="legend-item"><div class="legend-dot" style="background:#9b59b6;"></div>Intervals</div>'
        '<div class="legend-item"><div class="legend-dot" style="background:#ff6b35;"></div>Race</div>'
        '<div class="legend-item"><div class="legend-dot" style="background:#34c759;"></div>Strength</div>'
        '</div></div>'

        # Effort chart
        + '<div class="card">'
        '<div class="card-label">Relative Effort — Last 14 Days</div>'
        '<div class="chart-wrap"><canvas id="effortChart"></canvas></div>'
        '<div class="legend">'
        '<div class="legend-item"><div class="legend-dot" style="background:#3a7bd5;"></div>Paddle</div>'
        '<div class="legend-item"><div class="legend-dot" style="background:#9b59b6;"></div>Intervals</div>'
        '<div class="legend-item"><div class="legend-dot" style="background:#ff6b35;"></div>Race</div>'
        '<div class="legend-item"><div class="legend-dot" style="background:#34c759;"></div>Strength</div>'
        '</div></div>'

        '<div class="card"><div class="card-label">Performance Summary</div>'
        '<div class="card-content">' + sections["PERFORMANCE SUMMARY"] + '</div></div>'

        '<div class="card"><div class="card-label">Next Workout</div>'
        '<div class="card-content">' + sections["NEXT WORKOUT"] + '</div></div>'

        '<div class="card"><div class="card-label">Stroke Tip</div>'
        '<div class="card-content">' + sections["STROKE TIP"] + '</div></div>'


        '</div>'
        '<script>'
        + chart_script_miles
        + chart_script_effort
        + '</script></body></html>'
    )




# ----------------------------------------
# WEB ROUTE
# ----------------------------------------
@app.route("/")
def home():
    chart_data, workout_summary, advice, tnrl_note = run_paddle_coach()
    return build_html_page(chart_data, advice, tnrl_note)


# ----------------------------------------
# ENTRY POINT
# Starts the web server when Railway runs the app
# ----------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
