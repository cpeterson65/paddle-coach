# 🏄 Paddle Coach

A personal AI coaching assistant for competitive surfski paddlers. Paddle Coach pulls your recent workouts from Strava, analyzes your training load relative to your upcoming race schedule, and delivers a daily coaching briefing via email every evening at 9pm Eastern.

---

## What It Does

Every day at 9pm Eastern, Paddle Coach:

1. Fetches your recent activities from Strava
2. Builds two 14-day training charts (miles and relative effort)
3. Sends a personalized email with:
   - A performance summary based on your recent load and intensity
   - A tomorrow's workout recommendation designed around your race calendar and periodization
   - A stroke tip from elite surfski and K1 coaches, with a clickable source link when available
   - A coach's note based on where you are in your training cycle

You can also view the briefing anytime in your browser at your Railway URL.

---

## Files

| File | What It Does |
|---|---|
| `main.py` | The brain of the app — Strava integration, AI prompt, charts, web page, email sender, scheduler |
| `races.py` | Your race schedule — update this each year |
| `sources.py` | Trusted coaching sources used to generate stroke tips |
| `requirements.txt` | Python packages Railway needs to run the app |
| `README.md` | This file |

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

Races that have already passed are automatically filtered out — no need to delete them. Just update dates each year.

---

## Activity Classification

The app classifies Strava activities automatically:

| Type | Color | How It's Detected |
|---|---|---|
| Paddle | Blue | Sport is `ride`, `kayaking`, or `canoeing`, OR "paddle" in the name |
| Intervals | Purple | "interval", "intervals", "int", "tempo", "threshold", or "fartlek" in the name |
| Race | Orange | "race" or "tnrl" in the activity name |
| Strength | Green | Sport is `weighttraining` or `workout` |
| Rest | — | Everything else (empty bar) |

**Note:** Ride is treated as paddle because Garmin/Strava sometimes defaults kayak sessions to ride.

**For interval detection to work:** Name your interval sessions with "interval", "intervals", or "int" in the title (e.g. "Morning intervals" or "Threshold int session").

---

## Charts

Two bar charts are shown on the web page and in the email:

- **Miles — Last 14 Days:** Shows distance per day by activity type
- **Relative Effort — Last 14 Days:** Shows Strava's suffer score per day, using the same colors and time scale

Both charts use a single letter for the day of the week (M T W T F S S).

---

## Coaching Logic

The AI coaches around your race calendar with these rules:

- Recommends rest if you've been paddling hard multiple days in a row with high effort
- Prescribes a quality session if you've had 2+ consecutive rest days
- Tapers volume (while maintaining some intensity) in the 2 weeks before a race
- Prescribes mostly easy paddling or rest in the week before a race
- Tracks interval sessions and suggests one if it's been 4+ days since your last
- Never criticizes a recent easy/short session — assumes it was intentional recovery
- Reminds you about TNRL on Tuesday evenings between March and July instead of prescribing a workout

---

## TNRL

Tuesday Night Race League runs March through July. On Tuesday evenings the app shows a reminder banner instead of prescribing a workout. TNRL activities logged in Strava (with "tnrl" in the name) appear as Race (orange) in the charts.

---

## Railway Environment Variables

These must be set in your Railway project under **Variables**:

| Variable | What It Is |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `STRAVA_CLIENT_ID` | Your Strava app Client ID (found at strava.com/settings/api) |
| `STRAVA_CLIENT_SECRET` | Your Strava app Client Secret |
| `STRAVA_REFRESH_TOKEN` | Your Strava refresh token |
| `RESEND_API_KEY` | Your Resend API key for sending emails |
| `PORT` | Set to `8080` |

---

## If the Strava Token Breaks

The app automatically refreshes the Strava access token every time it runs. However, the refresh token itself can expire if permissions are revoked. If you see a Strava authorization error:

1. Go to `https://www.strava.com/oauth/authorize?client_id=215490&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all` and click Authorize
2. Copy the `code` value from the URL bar
3. POST to `https://www.strava.com/oauth/token` using Hoppscotch with fields: `client_id`, `client_secret`, `code`, `grant_type=authorization_code`
4. Copy the new `refresh_token` from the response
5. Update `STRAVA_REFRESH_TOKEN` in Railway Variables

---

## Coaching Sources

Stroke tips are drawn from elite surfski and K1 coaches in priority order:

| Coach | Specialty |
|---|---|
| Boyan Zlatarev — Surfski Center Tarifa | Downwind, wave reading, energy efficiency (Chris's personal coach) |
| Oscar Chalupsky | Forward stroke fundamentals, downwind, ocean racing |
| Dawid & Jasper Mocke — Mocke Paddling | Stroke mechanics, catch, drills |
| Ivan Lawler — Ultimate Kayaks | K1 technique, foot drive, leg drive, rotation |
| Greg Barton — Epic Kayaks | Olympic-level stroke fundamentals |
| Sean Rice — PaddleLife | Race tactics, wash riding, performance training |
| K2N Online Paddle School | Kinetic chain, progression-based technique |
| Paddle 2 Fitness — Julian Norton-Smith | Coaching cues, polarized training, catch activation |

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
| Timezone | pytz (Eastern time) |

---

## Future Ideas

- Multi-user support with Strava OAuth login for each paddler
- Garmin Connect integration for paddlers not on Strava
- Personal coaching notes file to inform stroke tips
- Group email for the paddling club
