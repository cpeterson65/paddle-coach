# 🏄 Paddle Coach

A personal AI training assistant for surfski paddlers, built in Python and hosted on Railway, that connects to Strava, analyzes workouts, and delivers daily coaching advice via a browser-based briefing.

---

## What It Does

Open the app in any browser to get a fresh daily briefing that includes:

1. Two 14-day training charts (miles and relative effort)
2. A performance summary based on your recent load and intensity
3. A next workout recommendation with a 3-session forward preview, planned around your race calendar
4. A stroke tip from elite surfski and K1 coaches, with a clickable source link when available

---

## Files

| File | What It Does |
|---|---|
| `main.py` | The brain of the app — Strava integration, AI prompt, charts, web page |
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

## Athlete Profile

The AI is calibrated to the following athlete profile, defined in the prompt inside `main.py`:

- **Age:** Born 1967
- **Sex:** Male
- **Location:** South Florida
- **Heart rate zones:**
  - Z2 Endurance: 121–149 bpm (easy, long sessions)
  - Z4 Threshold: 165–178 bpm (tempo and interval work)
  - Z5 Max: 179+ bpm (race pace only, not to exceed in training)

To update these, edit the athlete description at the top of the prompt in `main.py`.

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

Two bar charts show the last 14 days using a single letter for day of week (M T W T F S S):

- **Miles — Last 14 Days:** Distance per day by activity type
- **Relative Effort — Last 14 Days:** Strava's suffer score per day, using the same colors and time scale

---

## Coaching Logic

The AI plans workouts around your race calendar with these rules:

- Recommends rest if you've been paddling hard multiple days in a row with high effort
- Prescribes a quality session if you've had 2+ consecutive rest days
- Tapers volume (while maintaining some intensity) in the 2 weeks before a race
- Prescribes mostly easy paddling or rest in the week before a race
- Tracks interval sessions and suggests one if it's been 4+ days since your last
- Never criticizes a recent easy/short session — assumes it was intentional recovery
- Uses your actual HR zones when prescribing intensity targets
- Shows the next 7 days as a calendar so race days are never confused with training days
- Reminds you about TNRL on Tuesday evenings between March and July

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

Stroke tips are drawn from elite surfski and K1 coaches, rotated equally:

| Coach | Specialty |
|---|---|
| Boyan Zlatarev — Surfski Center Tarifa | Downwind, wave reading, energy efficiency (Chris's personal coach) |
| Dawid & Jasper Mocke — Mocke Paddling | Stroke mechanics, catch, drills |
| Ivan Lawler — Ultimate Kayaks | K1 technique, foot drive, leg drive, rotation |
| Greg Barton — Epic Kayaks | Olympic-level stroke fundamentals |
| Sean Rice — PaddleLife | Race tactics, wash riding, performance training |
| K2N Online Paddle School | Kinetic chain, progression-based technique |
| Paddle 2 Fitness — Julian Norton-Smith | Coaching cues, polarized training, catch activation |
| Oscar Chalupsky | Forward stroke fundamentals, downwind, ocean racing |

To add or adjust sources, edit `sources.py`.

---

## Tech Stack

| Component | Service |
|---|---|
| Hosting | Railway |
| AI | OpenAI GPT-4o-mini |
| Fitness Data | Strava API |
| Web Framework | Flask (Python) |
| Timezone | pytz (Eastern time) |

---

## Future Ideas

- Multi-user support with Strava OAuth login for each paddler
- Garmin Connect integration for paddlers not on Strava
- Personal coaching notes file to inform stroke tips
- Group email or SMS for the paddling club
- React front end for the multi-user version
