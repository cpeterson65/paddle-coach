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
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


# ----------------------------------------
# MAIN FUNCTION
# ----------------------------------------
def run_paddle_coach():
    """
    Fetches recent workouts from Strava,
    filters relevant sessions,
    and generates a training recommendation using AI.
    """

    # ----------------------------------------
    # GET STRAVA DATA
    # ----------------------------------------
    headers = {"Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"}

    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities?per_page=50",
        headers=headers,
    )

    activities = response.json()
    print("STRAVA RESPONSE:")
    print(activities)
 
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

        # Include paddles + rides (since you sometimes log as bike)
        if "paddle" in name or sport in ["ride", "kayaking", "canoeing"]:

            # Distance: meters → miles
            distance = round(act.get("distance", 0) / 1609.34, 2)

            # Time: seconds → minutes
            moving_time = round(act.get("moving_time", 0) / 60, 1)

            # Date formatting
            raw_date = act.get("start_date_local")
            date = ""
            if raw_date:
                dt = datetime.fromisoformat(raw_date.replace("Z", ""))
                date = dt.strftime("%b %d")

            # Heart rate data (if available)
            avg_hr = act.get("average_heartrate")
            max_hr = act.get("max_heartrate")

            hr_text = ""
            if avg_hr:
                hr_text += f", avg HR {int(avg_hr)}"
            if max_hr:
                hr_text += f", max HR {int(max_hr)}"

            # Build line
            workout_summary += (
                f"{count + 1}. {date} - {name} - "
                f"{distance} mi, {moving_time} min{hr_text}\n"
            )

            count += 1

    # Debug print (optional but helpful)
    print("\nRAW WORKOUT DATA:\n")
    print(workout_summary)

    # ----------------------------------------
    # AI PROMPT
    # ----------------------------------------
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

    # ----------------------------------------
    # CALL OPENAI
    # ----------------------------------------
    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    result = ai_response.choices[0].message.content

    # ----------------------------------------
    # OUTPUT
    # ----------------------------------------
    print("\n🏄 Paddle Coach:\n")
    print(result)

    return result


# ----------------------------------------
# ENTRY POINT
# ----------------------------------------
if __name__ == "__main__":
    run_paddle_coach()
