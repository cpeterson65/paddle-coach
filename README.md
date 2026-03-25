# 🏄 Paddle Coach

A personal AI coaching assistant for competitive surfski paddlers. Paddle Coach pulls your recent workouts from Strava, analyzes your training load relative to your upcoming race schedule, and delivers a daily coaching briefing via email every evening at 9pm Eastern.

---

## What It Does

Every day at 9pm, Paddle Coach:

1. Fetches your recent activities from Strava
2. Builds a 14-day training chart (miles and relative effort)
3. Sends a personalized email with:
   - A performance summary based on your recent load and intensity
   - A tomorrow's workout recommendation designed around your race calendar
   - A stroke tip from elite surfski and K1 coaches
   - A coach's note based on where you are in your training cycle

You can also view the briefing anytime in your browser at your Railway URL.

---

## Files

| File | What It Does |
|---|---|
| `main.py` | The brain of the app — Strava integration, AI prompt, web page, email sender, scheduler |
| `races.py` | Your race schedule — update this each year |
| `sources.py` | Trusted coaching sources used to generate stroke tips |
| `requirements.txt` | Python packages Railway needs to run the app |

---

## How to Update Your Race Schedule

Open `races.py` and edit the list. Each race looks like this:

```python
{
    "name": "Black Belt",
    "location": "Miami, FL",
    "date": "April 18, 2026",
    "distance": "12 miles",
},
```

Races that have already passed are automatically filtered out — no need to delete them.

---

## Railway Environment Variables

These must be set in your Railway project under **Variables**:

| Variable | What It Is |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `STRAVA_CLIENT_ID` | Your Strava app Client ID (found at strava.com/settings/api) |
| `STRAVA_CLIENT_SECRET` | Your Strava app Client Secret |
| `STRAVA_REFRESH_TOKEN` | Your Strava refresh token (never expires, used to get fresh access tokens) |
| `RESEND_API_KEY` | Your Resend API key for sending emails |
| `PORT` | Set to `8080` |

---

## If the Strava Token Breaks

Strava access tokens expire every 6 hours but the app handles this automatically using the refresh token. If you ever see a Strava authorization error, it likely means the refresh token itself has expired or lost its permissions. To fix it:

1. Go to [strava.com/settings/api](https://www.strava.com/settings/api)
2. Re-authorize the app using the OAuth flow to get a new refresh token
3. Update `STRAVA_REFRESH_TOKEN` in Railway Variables

---

## Activity Classification

The app classifies Strava activities as follows:

| Activity Type | How It's Detected |
|---|---|
| Paddle | Sport type is `ride`, `kayaking`, or `canoeing`, OR "paddle" is in the name |
| Race | "race" or "tnrl" is in the activity name |
| Strength | Sport type is `weighttraining` or `workout` |
| Rest | Anything else (not shown in charts) |

**Note:** Bike/ride is treated as a paddle activity because the default Strava sport sometimes logs kayak sessions as a ride.

---

## TNRL

Tuesday Night Race League runs March through July. On Tuesday evenings the app shows a reminder banner instead of prescribing a workout. TNRL activities logged in Strava are shown as Race (orange) in the charts.

---

## Coaching Sources

Stroke tips are drawn from elite surfski and K1 coaches including:

- **Boyan Zlatarev** — Surfski Center Tarifa (Chris's personal coach)
- **Oscar Chalupsky** — 12x Molokai World Champion
- **Dawid & Jasper Mocke** — Mocke Paddling
- **Ivan Lawler** — Multiple K1 World Champion
- **Greg Barton** — Two-time Olympic gold medalist, Epic Kayaks founder
- **Sean Rice** — ICF Surfski World Champion, PaddleLife
- **K2N Online Paddle School**
- **Paddle 2 Fitness** — Julian Norton-Smith

To add or adjust sources, edit `sources.py`.

---

## Tech Stack

| Component | Service |
|---|---|
| Hosting | Railway |
| AI | OpenAI GPT-4o-mini |
| Fitness Data | Strava API |
| Email | Resend |
| Web Framework | Flask (Python) |
| Scheduler | APScheduler |

---

## Future Ideas

- Multi-user support with Strava OAuth login for each paddler
- Personal coaching notes uploaded as a text file to inform stroke tips
- Garmin Connect integration for paddlers not on Strava
