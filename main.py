import requests
from openai import OpenAI
import os
from datetime import datetime

# --- KEYS ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

def run_paddle_coach():
    headers = {"Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"}

    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities?per_page=50",
        headers=headers,
    )

    activities = response.json()

    workout_summary = ""
    i = 1
    max_paddles = 10

    for act in activities:
        if i > max_paddles:
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
                f"{i}. {date} - {name} - {distance} mi, {moving_time} min{hr_text}\n"
            )

            i += 1

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
1. Tomorrow’s workout (type + duration + intensity)
2. Risk level (low/medium/high)
3. Short reasoning (2–3 sentences)
"""

    ai_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    result = ai_response.choices[0].message.content

    print("\n🏄 Paddle Coach:\n")
    print(result)

    return result


if __name__ == "__main__":
    run_paddle_coach()
\
Give:\
1. Tomorrow\'92s workout (type + duration + intensity)\
2. Risk level (low/medium/high)\
3. Short reasoning (2\'963 sentences)\
"""\
\
    ai_response = client.chat.completions.create(\
        model="gpt-4o-mini",\
        messages=[\{"role": "user", "content": prompt\}],\
    )\
\
    result = ai_response.choices[0].message.content\
\
    print("\\n\uc0\u55356 \u57284  Paddle Coach:\\n")\
    print(result)\
\
    return result\
\
\
if __name__ == "__main__":\
    run_paddle_coach()}
