"""
World Demographics — Real-World Agent Population Data
Based on MegaFish 2.0 widget: 8.3 billion people divided into 15 dimensions

Used to make simulated agents demographically representative of the real world.
When the simulation generates background public agents, they are sampled from
these distributions so the simulated crowd matches humanity.
"""

import random
from typing import Dict, List, Tuple, Optional

# ---------------------------------------------------------------------------
# Population weights (in billions) — used for weighted random sampling
# ---------------------------------------------------------------------------

# (name, population_B, color, short_desc, avg_person_desc, personality_distribution)
# personality_distribution = [Survivor, Traditionalist, Caregiver, Socializer, Achiever, Explorer, Analyst, Rebel]

CULTURE_GROUPS = [
    ("Western Liberal",          1.05, "N. America, W. Europe, Australia. Individualist, secular, rights-focused.",
     "Suburban or urban. Has 1.5 kids. Works in services. Worries about cost of living.",
     [4, 10, 18, 20, 22, 14, 8, 4],
     {"region": "North America/Europe/Australia", "religion": "Secular/Christian", "income_bracket": "high",
      "internet_access": "heavy", "median_age": 40, "typical_jobs": ["service worker", "manager", "teacher", "healthcare worker"]}),

    ("East Asian Confucian",      1.55, "China, Japan, Korea, Taiwan. Collectivist, education-obsessed.",
     "Works very long hours. Has 1 child. Urban apartment. Saves aggressively.",
     [6, 28, 15, 14, 24, 6, 6, 1],
     {"region": "East Asia", "religion": "Non-religious/Buddhist", "income_bracket": "upper-middle",
      "internet_access": "heavy", "median_age": 38, "typical_jobs": ["factory worker", "engineer", "office worker", "student"]}),

    ("South Asian",               1.85, "India, Pakistan, Bangladesh. Family-centric, religiously diverse.",
     "Multi-generational household. Has 2–3 kids. Smartphone since 2017.",
     [12, 32, 22, 16, 12, 3, 2, 1],
     {"region": "South Asia", "religion": "Hindu/Muslim", "income_bracket": "lower-middle",
      "internet_access": "basic_mobile", "median_age": 28, "typical_jobs": ["farmer", "garment worker", "service worker", "student"]}),

    ("Islamic / MENA",            1.80, "Arab world, Iran, Turkey, Central Asia. Faith-centered.",
     "Prays daily. Has 3 kids. Median age 26. Youth unemployment is a stressor.",
     [14, 36, 20, 16, 8, 3, 2, 1],
     {"region": "MENA/Central Asia", "religion": "Muslim", "income_bracket": "lower-middle",
      "internet_access": "basic_mobile", "median_age": 26, "typical_jobs": ["informal trader", "government worker", "student", "farmer"]}),

    ("Sub-Saharan African",       1.10, "50+ countries. Community-driven, youngest population on earth.",
     "Age ~19. Has 4–5 siblings. Mobile money but no formal banking.",
     [28, 25, 25, 15, 5, 1, 0, 1],
     {"region": "Sub-Saharan Africa", "religion": "Christian/Muslim", "income_bracket": "low",
      "internet_access": "basic_mobile", "median_age": 19, "typical_jobs": ["subsistence farmer", "informal trader", "student"]}),

    ("Latin American",            0.65, "Mixed heritage. Warm, family-first, Catholic-influenced.",
     "Lives in a city. Catholic (loosely). Has 2–3 kids. Earns ~$8K/yr.",
     [10, 22, 28, 26, 8, 3, 1, 2],
     {"region": "Latin America", "religion": "Catholic/Evangelical", "income_bracket": "lower-middle",
      "internet_access": "regular", "median_age": 31, "typical_jobs": ["service worker", "informal worker", "construction", "retail"]}),

    ("Orthodox / Slavic",         0.26, "Russia, Ukraine, E. Europe. Stoic, communal, historically scarred.",
     "Experienced hardship. Distrusts institutions. Has 1–2 kids.",
     [15, 30, 18, 15, 12, 5, 4, 1],
     {"region": "Eastern Europe/Russia", "religion": "Orthodox Christian", "income_bracket": "upper-middle",
      "internet_access": "regular", "median_age": 40, "typical_jobs": ["industrial worker", "office worker", "engineer", "farmer"]}),

    ("Southeast Asian",           0.70, "Indonesia, Philippines, Vietnam, Thailand. Syncretic faiths, rapid growth.",
     "Motorbike owner. Has 2–3 kids. Manufacturing or services worker.",
     [14, 24, 26, 22, 8, 3, 1, 2],
     {"region": "Southeast Asia", "religion": "Muslim/Catholic/Buddhist", "income_bracket": "lower-middle",
      "internet_access": "regular", "median_age": 29, "typical_jobs": ["factory worker", "farmer", "service worker", "fisherman"]}),
]

COUNTRY_GROUPS = [
    ("India",       1.44, [14, 30, 22, 16, 12, 3, 2, 1],  {"median_age": 28, "religion": "Hindu", "income": "lower-middle"}),
    ("China",       1.41, [8, 26, 14, 16, 24, 6, 5, 1],   {"median_age": 38, "religion": "non-religious", "income": "upper-middle"}),
    ("USA",         0.335,[5, 12, 16, 20, 24, 12, 7, 4],   {"median_age": 38, "religion": "Christian/secular", "income": "high"}),
    ("Indonesia",   0.275,[12, 28, 24, 22, 8, 3, 1, 2],   {"median_age": 29, "religion": "Muslim", "income": "lower-middle"}),
    ("Pakistan",    0.230,[16, 36, 20, 16, 8, 2, 1, 1],   {"median_age": 22, "religion": "Muslim", "income": "lower-middle"}),
    ("Brazil",      0.215,[10, 20, 28, 28, 8, 3, 1, 2],   {"median_age": 33, "religion": "Catholic/Evangelical", "income": "upper-middle"}),
    ("Nigeria",     0.220,[25, 25, 22, 18, 8, 1, 0, 1],   {"median_age": 18, "religion": "Christian/Muslim", "income": "lower-middle"}),
    ("Bangladesh",  0.172,[18, 32, 24, 16, 6, 2, 1, 1],   {"median_age": 27, "religion": "Muslim", "income": "lower-middle"}),
    ("Ethiopia",    0.126,[25, 30, 22, 14, 6, 1, 1, 1],   {"median_age": 20, "religion": "Christian/Muslim", "income": "low"}),
    ("Rest of World",2.41,[14, 25, 20, 18, 12, 6, 3, 2],  {"median_age": 30, "religion": "mixed", "income": "middle"}),
]

INCOME_GROUPS = [
    ("Low income (<$2.15/day)",         0.70, [35, 28, 22, 10, 3, 1, 0, 1]),
    ("Lower-middle ($2.15–$8.85/day)",  2.80, [16, 28, 22, 18, 10, 3, 2, 1]),
    ("Upper-middle ($8.85–$40/day)",    2.90, [8, 20, 18, 20, 20, 8, 5, 1]),
    ("High income (>$40/day)",          1.20, [3, 14, 16, 18, 28, 12, 8, 1]),
    ("Ultra-wealthy (top 0.1%)",        0.003,[0, 8, 8, 14, 40, 16, 12, 2]),
]

INTERNET_GROUPS = [
    ("fully_offline",       2.70, "No internet. Info from radio, elders, neighbors.",   [22, 38, 24, 12, 3, 0, 0, 1]),
    ("basic_mobile",        2.10, "WhatsApp, Facebook, YouTube. Expensive data.",        [15, 30, 22, 20, 8, 3, 1, 1]),
    ("regular",             2.00, "Daily access, social media and entertainment.",       [8, 18, 18, 24, 16, 8, 5, 3]),
    ("heavy_informed",      1.20, "Power user. Reads long-form, global news.",           [3, 8, 12, 18, 26, 18, 12, 3]),
    ("digital_native",      0.30, "Hyper-connected. Remote worker, content creator.",   [1, 3, 8, 18, 26, 26, 14, 4]),
]

EMPLOYMENT_GROUPS = [
    ("Subsistence farmer",          1.30, [25, 38, 20, 12, 4, 0, 0, 1]),
    ("Manual / trade worker",       1.50, [12, 28, 18, 20, 14, 4, 2, 2]),
    ("Service / gig worker",        1.20, [10, 16, 18, 28, 14, 6, 4, 4]),
    ("Professional (white-collar)", 0.80, [2, 14, 14, 16, 32, 12, 8, 2]),
    ("Student",                     1.20, [4, 14, 12, 26, 18, 16, 8, 2]),
    ("Homemaker / caregiver",       0.90, [8, 32, 42, 12, 3, 1, 1, 1]),
    ("Unemployed / informal",       0.50, [30, 20, 18, 18, 8, 2, 1, 3]),
    ("Entrepreneur / self-employed",0.40, [8, 8, 8, 16, 36, 14, 8, 2]),
    ("Retired",                     0.40, [6, 36, 28, 18, 6, 3, 2, 1]),
]

PERSONALITY_ARCHETYPES = [
    ("The Traditionalist", 1.80, "Bound by cultural/religious/family norms. Stability over change.",
     "Has 3+ kids. Practices religion consistently. Resists outside influence. Moral backbone of community."),
    ("The Caregiver",      1.40, "Nurturing, self-sacrificing, invisible glue of communities.",
     "Probably a mother, nurse, or teacher. Gives more than receives. Known as the heart of the family."),
    ("The Achiever",       1.30, "Driven by goals, status, and upward mobility.",
     "Wakes up early. Has clear personal goals. Success is the identity. Often a firstborn child."),
    ("The Socializer",     1.50, "People-first. Energy from connection. Community builder.",
     "Knows everyone in the neighborhood. Emotionally intelligent. High life satisfaction."),
    ("The Survivor",       1.00, "Daily focus on immediate needs. Resilient, pragmatic, present-tense.",
     "Has experienced serious deprivation. Remarkable resilience. Has 3–5 kids."),
    ("The Explorer",       0.70, "Curious, open to new experience, questions assumptions.",
     "Probably moved cities or countries. Has 0–1 kids. Questions religion and culture."),
    ("The Analyst",        0.55, "Logic-first, independent thinking, data-oriented.",
     "Works in science, engineering, finance. Reads primary sources. Emotionally reserved."),
    ("The Rebel",          0.35, "Challenges norms. Counter-cultural or marginalized.",
     "Artist, activist, or someone born outside the dominant culture. Drives cultural change."),
]

LIFESTAGE_GROUPS = [
    ("Children (0–14)",       1.90, [8, 18, 14, 24, 10, 14, 8, 4]),
    ("Young adults (15–29)",  1.90, [10, 18, 14, 26, 16, 10, 5, 1]),
    ("Middle-aged (30–59)",   3.20, [10, 24, 22, 18, 18, 5, 2, 1]),
    ("Older adults (60+)",    1.30, [6, 32, 28, 18, 8, 4, 3, 1]),
]

CONFLICT_GROUPS = [
    ("Peaceful and stable",       4.50, [5, 18, 18, 22, 20, 10, 6, 1]),
    ("Political unrest / tension",2.00, [14, 22, 18, 20, 12, 7, 5, 2]),
    ("High crime / gang violence",0.80, [25, 20, 22, 18, 8, 3, 1, 3]),
    ("Active conflict zone",      0.35, [42, 18, 22, 12, 4, 1, 0, 1]),
    ("Refugee / displaced",       0.11, [48, 20, 20, 10, 2, 0, 0, 0]),
    ("Post-conflict recovery",    0.54, [22, 24, 24, 18, 8, 2, 1, 1]),
]

RELIGION_GROUPS = [
    ("Christian",               2.40, [12, 22, 24, 18, 14, 5, 3, 2]),
    ("Muslim",                  1.90, [14, 34, 20, 16, 10, 3, 2, 1]),
    ("Hindu",                   1.20, [12, 32, 24, 16, 10, 3, 2, 1]),
    ("Non-religious/Atheist",   1.10, [5, 8, 14, 18, 24, 16, 12, 3]),
    ("Buddhist",                0.50, [6, 20, 20, 18, 16, 12, 6, 2]),
    ("Folk / indigenous",       0.40, [20, 35, 26, 12, 4, 1, 1, 1]),
    ("Other (Jewish/Sikh/etc)", 0.30, [5, 18, 18, 18, 22, 10, 7, 2]),
]

# Personality type names (index matches distributions above)
PERSONALITY_NAMES = [
    "Survivor", "Traditionalist", "Caregiver", "Socializer",
    "Achiever", "Explorer", "Analyst", "Rebel"
]

# MBTI types mapped to personality archetype (for prompt enrichment)
ARCHETYPE_TO_MBTI = {
    "Survivor":       ["ISTP", "ISTJ", "ESTP", "ISFP"],
    "Traditionalist": ["ISFJ", "ISTJ", "ESFJ", "ESTJ"],
    "Caregiver":      ["ENFJ", "ESFJ", "INFJ", "ISFJ"],
    "Socializer":     ["ESFP", "ENFP", "ESTP", "ENFJ"],
    "Achiever":       ["ENTJ", "ESTJ", "INTJ", "ENTP"],
    "Explorer":       ["ENFP", "ENTP", "INFP", "INTP"],
    "Analyst":        ["INTJ", "INTP", "ENTJ", "INFJ"],
    "Rebel":          ["INFP", "ENTP", "ISFP", "ENFP"],
}


def weighted_sample(items: list, weight_idx: int = 1) -> tuple:
    """Sample one item from a list using population weights at weight_idx."""
    weights = [item[weight_idx] for item in items]
    total = sum(weights)
    r = random.random() * total
    cumulative = 0.0
    for item in items:
        cumulative += item[weight_idx]
        if r <= cumulative:
            return item
    return items[-1]


def sample_personality_from_distribution(distribution: List[int]) -> str:
    """Sample a personality archetype name given a distribution list."""
    total = sum(distribution)
    r = random.random() * total
    cumulative = 0
    for i, weight in enumerate(distribution):
        cumulative += weight
        if r <= cumulative:
            return PERSONALITY_NAMES[i]
    return PERSONALITY_NAMES[0]


def build_realistic_agent_background() -> Dict:
    """
    Build a demographically realistic background for a synthetic public agent.
    Samples from all dimensions weighted by real-world population.

    Returns a dict with demographic attributes ready to inject into persona prompts.
    """
    # Sample culture
    culture = weighted_sample(CULTURE_GROUPS)
    culture_name = culture[0]
    culture_desc = culture[1]  # population (used as weight)
    culture_personality_dist = culture[5]["typical_jobs"]
    culture_meta = culture[5]

    # Sample country (weighted)
    country_entry = weighted_sample(COUNTRY_GROUPS, weight_idx=1)
    country = country_entry[0]
    country_personality_dist = country_entry[2]

    # Sample income level
    income_entry = weighted_sample(INCOME_GROUPS, weight_idx=1)
    income_label = income_entry[0]

    # Sample internet access
    internet_entry = weighted_sample(INTERNET_GROUPS, weight_idx=1)
    internet_access = internet_entry[0]
    internet_desc = internet_entry[2]

    # Sample employment
    employment_entry = weighted_sample(EMPLOYMENT_GROUPS, weight_idx=1)
    employment = employment_entry[0]
    emp_personality_dist = employment_entry[2]

    # Sample life stage for age
    lifestage_entry = weighted_sample(LIFESTAGE_GROUPS, weight_idx=1)
    lifestage = lifestage_entry[0]
    if lifestage == "Children (0–14)":
        age = random.randint(10, 14)
    elif lifestage == "Young adults (15–29)":
        age = random.randint(15, 29)
    elif lifestage == "Middle-aged (30–59)":
        age = random.randint(30, 59)
    else:
        age = random.randint(60, 80)

    # Sample conflict context
    conflict_entry = weighted_sample(CONFLICT_GROUPS, weight_idx=1)
    conflict = conflict_entry[0]

    # Sample religion
    religion_entry = weighted_sample(RELIGION_GROUPS, weight_idx=1)
    religion = religion_entry[0]

    # Derive personality from average of culture + country distributions
    combined_dist = [
        (country_personality_dist[i] + emp_personality_dist[i]) // 2
        for i in range(8)
    ]
    personality_type = sample_personality_from_distribution(combined_dist)
    mbti = random.choice(ARCHETYPE_TO_MBTI.get(personality_type, ["ISFJ"]))

    gender = random.choice(["male", "female"])

    # Build typical job list for this culture
    typical_jobs = culture_meta.get("typical_jobs", ["worker"])
    job = random.choice(typical_jobs) if typical_jobs else employment

    return {
        "country": country,
        "culture": culture_name,
        "income_level": income_label,
        "internet_access": internet_access,
        "internet_desc": internet_desc,
        "employment": employment,
        "job": job,
        "age": age,
        "lifestage": lifestage,
        "religion": religion,
        "conflict_context": conflict,
        "personality_archetype": personality_type,
        "mbti": mbti,
        "gender": gender,
        "typical_personality_desc": next(
            (p[3] for p in PERSONALITY_ARCHETYPES if p[0] == f"The {personality_type}"), ""
        ),
    }


def get_demographic_context_for_prompt(background: Dict) -> str:
    """
    Format a demographic background dict into a concise prompt snippet
    to guide the LLM when generating a realistic persona.
    """
    return (
        f"This is a real-world representative agent. "
        f"Country: {background['country']}. "
        f"Culture: {background['culture']}. "
        f"Age: {background['age']} ({background['lifestage']}). "
        f"Gender: {background['gender']}. "
        f"Religion: {background['religion']}. "
        f"Income: {background['income_level']}. "
        f"Employment: {background['employment']} (works as: {background['job']}). "
        f"Internet access: {background['internet_access']} — {background['internet_desc']}. "
        f"Life context: {background['conflict_context']}. "
        f"Personality archetype: {background['personality_archetype']} — {background['typical_personality_desc']}. "
        f"MBTI: {background['mbti']}."
    )


def get_country_population_weights() -> List[Tuple[str, float]]:
    """Return (country_name, population_B) tuples for weighted sampling."""
    return [(c[0], c[1]) for c in COUNTRY_GROUPS]


def get_global_stats() -> Dict:
    """Summary statistics about the global agent population."""
    total_culture = sum(c[1] for c in CULTURE_GROUPS)
    return {
        "total_agents_billion": 8.3,
        "dimensions": 15,
        "culture_groups": len(CULTURE_GROUPS),
        "country_groups": len(COUNTRY_GROUPS),
        "personality_archetypes": len(PERSONALITY_ARCHETYPES),
        "largest_culture": max(CULTURE_GROUPS, key=lambda x: x[1])[0],
        "largest_country": max(COUNTRY_GROUPS, key=lambda x: x[1])[0],
    }
