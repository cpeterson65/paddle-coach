# ----------------------------------------
# Surfski & K1 Coaching Sources
# ----------------------------------------
# These sources are used by the AI coach to generate stroke tips.
# Focus: surfski, K1 kayak, downwind paddling, ocean racing.
# Excluded: SUP-only, OC-only, surf (wave riding) sources.
#
# priority: 1 = primary/elite, 2 = strong secondary, 3 = community/supporting
# type: youtube, website, blog, facebook, instagram, forum, podcast
# tags: topics this source covers well
# notes_for_agent: how the AI should use this source
# ----------------------------------------

SURFSKI_SOURCES = [

    # ----------------------------------------
    # TIER 1: ELITE COACHES — Your personal coaches and world champions
    # ----------------------------------------

    {
        "name": "Boyan Zlatarev / Surfski Center Tarifa",
        "type": "blog",
        "platform": "Web",
        "url": "https://www.surfskicenter.com/zen-master-blog",
        "account_name": "Surfski Center Tarifa",
        "priority": 1,
        "tags": ["downwind", "wave_reading", "ocean_racing", "technique", "catch", "flow_state", "hypermiling"],
        "notes_for_agent": (
            "Chris's personal coach. Boyan is Oscar Chalupsky's protege and widely considered "
            "the world's foremost downwind specialist. His philosophy centers on 'hypermiling' — "
            "wringing every drop of free energy from the ocean rather than brute force paddling. "
            "Prioritize his cues for downwind technique, wave reading, and energy efficiency. "
            "He emphasizes flow, timing, and positioning over raw power."
        ),
    },
    {
        "name": "Boyan Zlatarev / Surfski Center Tarifa",
        "type": "facebook",
        "platform": "Facebook",
        "url": "https://www.facebook.com/boyan.zlatarev",
        "account_name": "Boyan Zlatarev",
        "priority": 1,
        "tags": ["downwind", "wave_reading", "drills", "ocean_racing"],
        "notes_for_agent": (
            "Boyan's personal Facebook page. Contains technique posts, drills, and coaching cues "
            "for downwind paddling. Use as a supporting source alongside his blog."
        ),
    },
    {
        "name": "Oscar Chalupsky / Coach Chalupsky",
        "type": "website",
        "platform": "Web",
        "url": "https://www.coachchalupsky.com",
        "account_name": "Coach Chalupsky",
        "priority": 1,
        "tags": ["surfski", "downwind", "ocean_racing", "forward_stroke", "fundamentals", "feather_angle"],
        "notes_for_agent": (
            "12x Molokai World Champion with 25+ years of coaching. The godfather of modern surfski. "
            "Known for: zero or low feather angle, low elbow catch, spearing the blade before power, "
            "using the ocean's energy rather than fighting it. His fundamentals are the gold standard "
            "for surfski stroke mechanics."
        ),
    },
    {
        "name": "Oscar Chalupsky",
        "type": "youtube_search",
        "platform": "YouTube",
        "url": "https://www.youtube.com/results?search_query=Oscar+Chalupsky+surfski+technique",
        "account_name": "Oscar Chalupsky (various channels)",
        "priority": 1,
        "tags": ["surfski", "downwind", "forward_stroke", "ocean_racing", "clinic"],
        "notes_for_agent": (
            "Search-based source because Oscar's coaching content is spread across multiple channels "
            "and clinic uploads. Best for forward stroke fundamentals, downwind technique, and "
            "clinic-style coaching cues."
        ),
    },
    {
        "name": "Mocke Paddling (Dawid & Jasper Mocke)",
        "type": "youtube",
        "platform": "YouTube",
        "url": "https://www.youtube.com/@mockepaddling6232",
        "account_name": "@mockepaddling6232",
        "priority": 1,
        "tags": ["surfski", "technique", "leg_drive", "rotation", "downwind", "catch", "drills"],
        "notes_for_agent": (
            "World Champion brothers who founded the Surfski School in 2002. High-value source for "
            "stroke mechanics, common mistake corrections, and concise coaching cues. "
            "Famous for 'nose in the hole' downwind technique and emphasis on clean catch mechanics."
        ),
    },
    {
        "name": "Mocke Paddling",
        "type": "website",
        "platform": "Web",
        "url": "https://mockepaddling.com",
        "account_name": "Mocke Paddling",
        "priority": 1,
        "tags": ["surfski", "structured_training", "technique", "drills", "courses"],
        "notes_for_agent": (
            "Companion site to the YouTube channel. Good for structured learning content "
            "and their Masters of Surfski online course material."
        ),
    },
    {
        "name": "Ivan Lawler / Ultimate Kayaks",
        "type": "youtube",
        "platform": "YouTube",
        "url": "https://www.youtube.com/channel/UC8KuVUSSDZraBFmTwkIyOKA",
        "account_name": "Ultimate Kayaks",
        "priority": 1,
        "tags": ["k1", "sprint", "rotation", "catch", "foot_drive", "leg_drive", "exit", "technique"],
        "notes_for_agent": (
            "Multiple World Champion K1 paddler. Mechanically precise wing-paddle coaching. "
            "Best source for K1-applicable technique that translates directly to surfski: "
            "foot drive, leg drive, rotation sequencing, and stroke exit timing."
        ),
    },
    {
        "name": "Ivan Lawler Kayak Technique Series",
        "type": "youtube_playlist",
        "platform": "YouTube",
        "url": "https://www.youtube.com/playlist?list=PLUU4vHDSO0IpuQSyN3n74kxjwKfpZdk6G",
        "account_name": "Ultimate Kayaks",
        "priority": 1,
        "tags": ["k1", "technique_series", "foot_drive", "leg_drive", "rotation", "trunk", "exit", "top_arm"],
        "notes_for_agent": (
            "A 6-part series breaking down each phase of the stroke day by day. "
            "Ideal for extracting specific stroke-phase coaching points."
        ),
    },
    {
        "name": "Greg Barton / Epic Kayaks Technique",
        "type": "website",
        "platform": "Web",
        "url": "https://www.epickayaks.com/post/technique-series",
        "account_name": "Epic Kayaks",
        "priority": 1,
        "tags": ["k1", "surfski", "forward_stroke", "catch", "rotation", "leg_drive", "fundamentals"],
        "notes_for_agent": (
            "Two-time Olympic gold medalist and founder of Epic Kayaks. Greg Barton's technique "
            "series with Clint Robinson covers setup, posture, leg drive, core rotation, paddle "
            "shape, and personal tips. Famous cue: 'stab fish' at the catch — snap the blade in "
            "with the top hand before applying power. Excellent for flatwater stroke fundamentals."
        ),
    },
    {
        "name": "Sean Rice / PaddleLife",
        "type": "website",
        "platform": "Web",
        "url": "http://www.yourpaddlelife.com",
        "account_name": "PaddleLife",
        "priority": 1,
        "tags": ["surfski", "ocean_racing", "downwind", "wash_riding", "race_tactics", "training"],
        "notes_for_agent": (
            "2013 ICF Surfski World Champion and 2017 Molokai Champion. Expert on wash riding, "
            "race tactics, and performance training. Key tips: minimum 3 sessions/week to improve, "
            "interval training every session except long paddles, prioritize downwind whenever "
            "possible. Good source for race strategy and competitive training advice."
        ),
    },
    {
        "name": "K2N Online Paddle School",
        "type": "website",
        "platform": "Web",
        "url": "https://www.k2nonlinepaddleschool.com/",
        "account_name": "K2N Online Paddle School",
        "priority": 1,
        "tags": ["surfski", "k1", "technique", "kinetic_chain", "progression_model", "posture", "directional_force"],
        "notes_for_agent": (
            "One of the best structured coaching systems for surfski and K1. Strong for "
            "progression-based learning, movement layering, and kinetic chain concepts. "
            "Excellent for understanding how power transfers from feet through core to paddle."
        ),
    },
    {
        "name": "K2N Online Paddle School",
        "type": "youtube",
        "platform": "YouTube",
        "url": "https://www.youtube.com/@K2NOPS",
        "account_name": "@K2NOPS",
        "priority": 1,
        "tags": ["surfski", "k1", "technique", "posture", "directional_force", "drills"],
        "notes_for_agent": (
            "Short, explicit coaching tips and progression-aware technique content. "
            "Good for single-concept cues that are easy to apply on the water."
        ),
    },
    {
        "name": "Paddle 2 Fitness / Julian Norton-Smith",
        "type": "podcast",
        "platform": "Podcast",
        "url": "https://paddle2fitness.com",
        "account_name": "Paddle 2 Fitness",
        "priority": 1,
        "tags": ["surfski", "technique", "rotation", "catch", "leg_drive", "MAF_training", "80_20_training"],
        "notes_for_agent": (
            "20+ years of surfski coaching. Julian Norton-Smith breaks down technique into "
            "memorable cues and analogies. Known for polarized training (80/20 MAF method). "
            "Good source for: catch activation, leg drive timing ('squeeze and hold not squeeze "
            "and pop'), push arm mechanics, and training intensity distribution."
        ),
    },
    {
        "name": "Paddle 2 Fitness Coaching",
        "type": "youtube",
        "platform": "YouTube",
        "url": "https://www.youtube.com/@paddle2fitnesscoaching",
        "account_name": "@paddle2fitnesscoaching",
        "priority": 1,
        "tags": ["surfski", "kayak", "drills", "rotation", "coaching_cues", "downwind"],
        "notes_for_agent": (
            "Video companion to the podcast. Good for drill demonstrations, "
            "practical movement instruction, and memorable coaching phrases."
        ),
    },

    # ----------------------------------------
    # TIER 2: STRONG SECONDARY SOURCES
    # ----------------------------------------

    {
        "name": "Paddle Monster",
        "type": "website",
        "platform": "Web",
        "url": "https://paddlemonster.com",
        "account_name": "Paddle Monster",
        "priority": 3,
        "tags": ["training", "intervals", "technique", "performance", "periodization"],
        "notes_for_agent": (
            "Use sparingly — content is too broad across disciplines. Only reference if no better surfski-specific source applies."
            "Use for training structure, interval design, and performance periodization."
        ),
    },
    {
        "name": "Paddle Monster",
        "type": "youtube",
        "platform": "YouTube",
        "url": "https://www.youtube.com/paddlemonster",
        "account_name": "Paddle Monster",
        "priority": 3,
        "tags": ["surfski", "training", "drills", "performance"],
        "notes_for_agent": (
            "Use sparingly — content is too broad across disciplines. Only reference if no better surfski-specific source applies."
            "Note: also covers SUP and OC — filter for surfski/K1 content only."
        ),
    },
    {
        "name": "SurfSki.TV",
        "type": "website",
        "platform": "Web",
        "url": "https://www.surfski.tv/",
        "account_name": "Surfski.TV",
        "priority": 2,
        "tags": ["surfski", "tips", "downwind", "race_footage", "media"],
        "notes_for_agent": (
            "Broad surfski technique content, interviews, and curated ocean-racing material. "
            "Good for general surfski tips and race footage analysis."
        ),
    },
    {
        "name": "SurfskiTV",
        "type": "youtube",
        "platform": "YouTube",
        "url": "https://www.youtube.com/@Surfski-TV",
        "account_name": "@Surfski-TV",
        "priority": 2,
        "tags": ["surfski", "tips", "kinetic_chain", "leg_drive", "setup", "downwind"],
        "notes_for_agent": (
            "Modular single-topic paddling tips. Easy to extract focused coaching cues."
        ),
    },
    {
        "name": "Planet Canoe / ICF",
        "type": "youtube",
        "platform": "YouTube",
        "url": "https://www.youtube.com/PlanetCanoe",
        "account_name": "Planet Canoe",
        "priority": 2,
        "tags": ["k1", "icf", "elite", "stroke_model", "sprint", "technique"],
        "notes_for_agent": (
            "Official ICF canoe sprint channel. Good for elite K1 stroke model footage "
            "and technique-adjacent content. Use to observe world-class K1 mechanics "
            "that apply to surfski flat-water paddling."
        ),
    },
    {
        "name": "TC Surfski / Peak Paddle Performance Podcast",
        "type": "website",
        "platform": "Web",
        "url": "https://tcsurfski.com",
        "account_name": "TC Surfski",
        "priority": 2,
        "tags": ["surfski", "downwind", "technique", "training", "coaching_interviews", "podcast"],
        "notes_for_agent": (
            "Excellent community resource with deep coaching interviews (Oscar Chalupsky, "
            "Boyan Zlatarev, Greg Barton, Ivan Lawler and more). Good for synthesizing "
            "coaching philosophy and technique concepts from multiple elite sources."
        ),
    },

    # ----------------------------------------
    # TIER 3: COMMUNITY & SUPPORTING SOURCES
    # ----------------------------------------

    {
        "name": "Surfski.info Forum",
        "type": "forum",
        "platform": "Web",
        "url": "https://surfski.info/forum",
        "account_name": "Surfski.info",
        "priority": 3,
        "tags": ["community", "technique", "gear", "real_world_feedback", "discussion"],
        "notes_for_agent": (
            "Low-trust community source. Use only for common pain points, field heuristics, "
            "and real-world paddler feedback. Never cite as a primary technical source. "
            "Good for understanding what intermediate-advanced paddlers struggle with."
        ),
    },
    {
        "name": "r/Surfski",
        "type": "reddit",
        "platform": "Reddit",
        "url": "https://www.reddit.com/r/Surfski/",
        "account_name": "r/Surfski",
        "priority": 3,
        "tags": ["community", "discussion", "gear", "real_world_feedback"],
        "notes_for_agent": (
            "Very low trust. Use only as a last resort for community sentiment. "
            "Never cite as a coaching source."
        ),
    },
]


# ----------------------------------------
# HELPER CONFIG FOR THE AGENT
# ----------------------------------------

PRIMARY_SOURCE_NAMES = {
    "Boyan Zlatarev / Surfski Center Tarifa",
    "Oscar Chalupsky / Coach Chalupsky",
    "Mocke Paddling (Dawid & Jasper Mocke)",
    "Ivan Lawler / Ultimate Kayaks",
    "Greg Barton / Epic Kayaks Technique",
    "Sean Rice / PaddleLife",
    "K2N Online Paddle School",
}

# These source types should be treated with lower trust
LOW_TRUST_SOURCE_TYPES = {"reddit", "facebook", "forum"}

# Sources that are SUP or OC primary — do NOT use for Chris's stroke tips
EXCLUDED_FOCUS = {"sup_only", "oc_only"}

SOURCE_PRIORITY_WEIGHTS = {
    1: 1.0,
    2: 0.7,
    3: 0.3,
}


def score_source(source: dict) -> float:
    """
    Weights sources by priority and trust level.
    Higher score = more reliable for coaching tips.
    """
    base = SOURCE_PRIORITY_WEIGHTS.get(source["priority"], 0.5)

    if source["type"] in LOW_TRUST_SOURCE_TYPES:
        base *= 0.6

    if source["name"] in PRIMARY_SOURCE_NAMES:
        base *= 1.2

    return round(base, 3)
