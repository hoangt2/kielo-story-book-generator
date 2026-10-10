# Level-appropriate story topic suggestions for the UI.
#
# Suggestions are generated fresh by the model on request, so the panel shows
# something different every time. The curated list further down is the fallback
# when the API is unavailable, and doubles as the style reference the model is
# shown so generated ideas keep the same shape.
#
# Each suggestion is a ready-to-use custom topic. The "drills" field explains
# which grammar/vocabulary the topic exercises at that CEFR level, and "pages"
# is the page count that suits it (short, repetitive topics need fewer pages —
# padding an A1 story to 10 pages pushes the model outside the A1 word list).
import json
import os
import random
import threading

import google.generativeai as genai
from dotenv import load_dotenv

from languages import LANGUAGES, SV_LEVEL_HINTS, SV_TOPIC_SUGGESTIONS, normalize_language
from prompts import LEVEL_CONSTRAINTS, SV_LEVEL_CONSTRAINTS

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_NAME = "gemini-3.5-flash"

LEVEL_HINTS = {
    "A1": "A1 allows 3–6 word sentences, present tense and basic cases only. These topics repeat a small set of concrete nouns so the story stays inside that.",
    "A2": "A2 adds simple past tense and everyday cases. These topics follow a clear sequence of events with familiar daily vocabulary.",
    "B1": "B1 allows subordinate clauses and the conditional. These topics need opinions, plans and reasons — not just description.",
    "B2": "B2 handles complex clauses and abstract ideas. These topics carry a disagreement or a shift in perspective.",
    "C1": "C1 uses all cases and registers naturally. These topics lean on nuance, contrast and reflection.",
    "C2": "C2 is native-level prose. These topics invite literary devices, dialect, register play and wordplay.",
}

TOPIC_SUGGESTIONS = {
    "A1": [
        {
            "topic": "A child walks to daycare and names the colour of everything she sees",
            "setting": "a leafy street in Turku in autumn",
            "drills": "Colours, 'tämä on' + adjective, nominative only",
            "pages": 5,
        },
        {
            "topic": "A grandmother and a child count the animals at a petting farm",
            "setting": "a small city farm in Helsinki",
            "drills": "Numbers 1–10, animal nouns, partitive after numbers",
            "pages": 5,
        },
        {
            "topic": "A family eats breakfast and each person says what they eat",
            "setting": "a Finnish home kitchen in the morning",
            "drills": "Food nouns, 'syön / juon' + partitive",
            "pages": 4,
        },
        {
            "topic": "A weather diary: one page for each kind of weather in the same yard",
            "setting": "the courtyard of an apartment building (kerrostalo)",
            "drills": "Weather verbs: sataa, paistaa, tuulee, on kylmä",
            "pages": 6,
        },
        {
            "topic": "A snowman in a yard melts a little every day until it is gone",
            "setting": "a snowy yard in Espoo in late winter",
            "drills": "One repeated sentence pattern, counting down",
            "pages": 5,
        },
        {
            "topic": "A boy puts on winter clothes one piece at a time before going out",
            "setting": "the hallway (eteinen) of a Finnish home",
            "drills": "Clothing nouns, present tense, sequence of actions",
            "pages": 5,
        },
        {
            "topic": "A new pupil stands up and introduces himself to the class",
            "setting": "a first-grade classroom on the first day of school",
            "drills": "Minä olen…, minä asun…, age and home town",
            "pages": 4,
        },
        {
            "topic": "A child buys one bun and one juice at a café counter",
            "setting": "a small café in Tampere",
            "drills": "Greetings, kiitos, numbers and prices",
            "pages": 4,
        },
        {
            "topic": "Buying apples at the market square: how many, what colour, how much",
            "setting": "Kauppatori market square in Helsinki",
            "drills": "Simple questions, numbers, colours",
            "pages": 5,
        },
        {
            "topic": "A dog searches the whole apartment for his ball. It is not here. It is not there.",
            "setting": "a small apartment on a rainy day",
            "drills": "Simple 'ei ole' negation, repeated with room objects",
            "pages": 5,
        },
        {
            "topic": "A child cannot find one mitten and checks every place in the hallway",
            "setting": "the eteinen of a Finnish home in winter",
            "drills": "Negation plus everyday object nouns",
            "pages": 5,
        },
        {
            "topic": "A small child's first sauna with dad: hot, water, steam, then juice",
            "setting": "a Finnish home sauna on a Saturday evening",
            "drills": "Concrete nouns, 'on kuuma', very short sentences",
            "pages": 4,
        },
    ],
    "A2": [
        {
            "topic": "A girl tells what she did yesterday, hour by hour",
            "setting": "her home and school in Jyväskylä",
            "drills": "Simple past tense, clock times, daily routine verbs",
            "pages": 6,
        },
        {
            "topic": "Two children take the bus to the swimming hall alone for the first time",
            "setting": "a city bus and the uimahalli in Oulu",
            "drills": "Illative and inessive (bussiin, hallissa), tickets, directions",
            "pages": 6,
        },
        {
            "topic": "A boy writes a shopping list and finds every item in the shop",
            "setting": "a K-Market on a Friday afternoon",
            "drills": "Food vocabulary, partitive, prices and quantities",
            "pages": 6,
        },
        {
            "topic": "A family packs the car for the summer cottage and forgets something",
            "setting": "a driveway and the road to a mökki",
            "drills": "Possessions, past tense, simple postpositions",
            "pages": 6,
        },
        {
            "topic": "A child's first day with a new puppy: feeding, walking, sleeping",
            "setting": "a home and a nearby park in Vantaa",
            "drills": "Routine verbs, times of day, adverbs",
            "pages": 6,
        },
        {
            "topic": "Two sisters bake pulla together and something goes wrong",
            "setting": "a home kitchen on a Sunday",
            "drills": "Kitchen nouns, past tense narration, sequence words",
            "pages": 6,
        },
        {
            "topic": "A boy loses his bike key at the sports field and asks people for help",
            "setting": "a football field in Kuopio",
            "drills": "Questions, past tense, place cases",
            "pages": 7,
        },
        {
            "topic": "A letter to a pen pal describing my town, my family and the weather",
            "setting": "a small town in Central Finland",
            "drills": "Descriptive sentences, 'asun' + inessive, family vocabulary",
            "pages": 6,
        },
        {
            "topic": "A day at the amusement park with grandpa: the rides, the queue, the ice cream",
            "setting": "Särkänniemi in Tampere",
            "drills": "Past tense narrative, feeling adjectives",
            "pages": 7,
        },
        {
            "topic": "Waiting for a train that is late, and what everyone does meanwhile",
            "setting": "Tampere railway station",
            "drills": "Clock times, waiting verbs, small talk",
            "pages": 6,
        },
    ],
    "B1": [
        {
            "topic": "A teenager starts a summer job (kesätyö) at an ice cream kiosk",
            "setting": "a kiosk on the Helsinki waterfront",
            "drills": "Work vocabulary, koska/kun clauses, conditional 'haluaisin'",
            "pages": 8,
        },
        {
            "topic": "A family disagrees about where to go on holiday and finds a compromise",
            "setting": "a living room in Lahti",
            "drills": "Opinions, comparatives, conditional mood",
            "pages": 8,
        },
        {
            "topic": "A newcomer's first week at a Finnish language course",
            "setting": "an adult education centre in Espoo",
            "drills": "Classroom vocabulary, describing feelings and plans",
            "pages": 8,
        },
        {
            "topic": "Neighbours organise a talkoot to clean the shared yard",
            "setting": "a kerrostalo yard in spring",
            "drills": "Community vocabulary, passive voice, making plans",
            "pages": 8,
        },
        {
            "topic": "A student moves into their first own apartment",
            "setting": "a small studio in Turku",
            "drills": "Furniture and prices, relative clauses with 'joka'",
            "pages": 8,
        },
        {
            "topic": "A hiking trip goes off plan when the weather turns",
            "setting": "Nuuksio national park",
            "drills": "Nature vocabulary, past and perfect tense, cause clauses",
            "pages": 9,
        },
        {
            "topic": "A young person's first visit to a health centre alone",
            "setting": "a terveysasema waiting room",
            "drills": "Body and symptom vocabulary, polite questions, appointments",
            "pages": 8,
        },
        {
            "topic": "Two friends train together for their first 10 km run",
            "setting": "running paths along the river in Oulu",
            "drills": "Time expressions, comparatives, expressing progress",
            "pages": 8,
        },
    ],
    "B2": [
        {
            "topic": "A journalist interviews an elderly person about the winters of their childhood",
            "setting": "a home in Kajaani",
            "drills": "Past narration, participles, reported speech",
            "pages": 9,
        },
        {
            "topic": "A family debates whether to sell the beloved but expensive summer cottage",
            "setting": "a mökki by a lake in Savo",
            "drills": "Abstract argument vocabulary, conditional and passive",
            "pages": 9,
        },
        {
            "topic": "A new manager has to give difficult feedback for the first time",
            "setting": "an open-plan office in Helsinki",
            "drills": "Workplace register, politeness strategies, complex clauses",
            "pages": 9,
        },
        {
            "topic": "Someone returns to their home town after twenty years abroad",
            "setting": "a small town in Ostrobothnia",
            "drills": "Perfect and pluperfect tense, comparison, change over time",
            "pages": 10,
        },
        {
            "topic": "Volunteers coordinate a search when a hiker does not return",
            "setting": "a forest in Lapland at dusk",
            "drills": "Passive voice, urgency, participial constructions",
            "pages": 9,
        },
        {
            "topic": "A student and a landlord disagree about the deposit",
            "setting": "an apartment handover in Tampere",
            "drills": "Formal register, conditional, argumentation",
            "pages": 9,
        },
        {
            "topic": "A council meeting about closing the village school",
            "setting": "a village hall in North Karelia",
            "drills": "Civic vocabulary, hedging, expressing disagreement politely",
            "pages": 10,
        },
    ],
    "C1": [
        {
            "topic": "A translator struggles with a word that has no equivalent in Finnish",
            "setting": "a home office in Helsinki at night",
            "drills": "Metalinguistic vocabulary, nuanced modality",
            "pages": 10,
        },
        {
            "topic": "Two siblings clear out the family home and remember the same childhood differently",
            "setting": "an old wooden house in Porvoo",
            "drills": "Literary register, participles, temporal constructions",
            "pages": 10,
        },
        {
            "topic": "A researcher defends their doctoral thesis and faces the opponent",
            "setting": "a university hall in Jyväskylä",
            "drills": "Academic register, argumentation, passive voice",
            "pages": 10,
        },
        {
            "topic": "An old logger and a young forest activist meet on the same clear-cut",
            "setting": "a logging site in Kainuu",
            "drills": "Register contrast, idioms, agent participles",
            "pages": 10,
        },
        {
            "topic": "Letters between an evacuee child and the family who took them in",
            "setting": "Karelia and Häme in the 1940s",
            "drills": "Period and epistolary style, indirect emotion",
            "pages": 11,
        },
        {
            "topic": "A night-shift nurse works the last shift before retirement",
            "setting": "a hospital ward in Oulu",
            "drills": "Reflective narration, nuanced emotion vocabulary",
            "pages": 10,
        },
    ],
    "C2": [
        {
            "topic": "A poet returns to the lake that appears in every poem they wrote",
            "setting": "a lakeside in Central Finland at midsummer",
            "drills": "Literary devices, rare cases, rhythmic prose",
            "pages": 11,
        },
        {
            "topic": "A Kalevala-styled retelling of an ordinary morning commute",
            "setting": "the Helsinki metro at rush hour",
            "drills": "Archaic and literary forms, register clash, wordplay",
            "pages": 11,
        },
        {
            "topic": "A Helsinki designer and a Savo carpenter build a house together",
            "setting": "a building site in Savo",
            "drills": "Dialect flavour, proverbs, colloquial register",
            "pages": 11,
        },
        {
            "topic": "An unreliable narrator describes the same summer week three times",
            "setting": "a cottage in the Turku archipelago",
            "drills": "Stylistic variation, discourse particles, emphasis",
            "pages": 12,
        },
        {
            "topic": "The last day of a village shop, told by the shopkeeper",
            "setting": "a village in Kainuu",
            "drills": "Free indirect discourse, emphasis particles, nostalgia",
            "pages": 11,
        },
    ],
}

DEFAULT_LEVEL = "A1"


TOPIC_SUGGESTIONS_BY_LANGUAGE = {
    "fi": TOPIC_SUGGESTIONS,
    "sv": SV_TOPIC_SUGGESTIONS,
}

LEVEL_HINTS_BY_LANGUAGE = {
    "fi": LEVEL_HINTS,
    "sv": SV_LEVEL_HINTS,
}


def _language(language):
    return normalize_language(language)


def get_topic_suggestions(level=None, language="fi"):
    """Returns the curated suggestion list for a CEFR level (falls back to A1)."""
    curated = TOPIC_SUGGESTIONS_BY_LANGUAGE[_language(language)]
    if level not in curated:
        level = DEFAULT_LEVEL
    return curated[level]


def get_level_hint(level=None, language="fi"):
    """Returns the short explanation of what makes a good topic at this level."""
    hints = LEVEL_HINTS_BY_LANGUAGE[_language(language)]
    if level not in hints:
        level = DEFAULT_LEVEL
    return hints[level]


def get_random_topic_suggestion(level=None, language="fi"):
    """Returns one random suggestion for the given level."""
    return random.choice(get_topic_suggestions(level, language))


# --- AI-generated suggestions -----------------------------------------------

# Ideas already served this session, per (language, level), so a refresh brings
# new ones instead of circling the same handful.
_recent_topics = {}
_RECENT_MEMORY = 24

SUGGESTION_PROMPT = """You invent story topics for an illustrated {name} language-learning book generator.

Propose {count} DIFFERENT story topics suitable for a {level} learner.

The CEFR constraints the story will have to obey:
{constraints}

A good topic at this level is one the writer can tell WITHIN those constraints. At the
lowest levels that means a small cast, concrete objects, and a situation that repeats a
single sentence pattern; at higher levels it means the topic needs opinions, conflict,
or nuance to be told at all.

Rules:
- {culture_rule}
- Everyday human situations, not fairy tales, not mysteries, not adventures with treasure.
- Each topic is ONE sentence, written in English, concrete enough to illustrate.
- Vary them: different seasons, ages, indoor/outdoor, alone/with others, human/animal.
- `setting` is a specific place, phrased like "a small café in Tampere".
- `drills` names the grammar or vocabulary that topic exercises, in under 10 words.
- `pages` is how many pages the topic can sustain at this level, between {min_pages} and {max_pages}.

{avoid_clause}
Return ONLY a JSON array, no markdown fence:
[{{"topic": "...", "setting": "...", "drills": "...", "pages": 5}}]
"""

# A1 sentences are so short that a long story runs out of permitted vocabulary,
# while a C2 story needs room to develop.
_PAGE_BOUNDS = {
    "A1": (4, 6),
    "A2": (5, 8),
    "B1": (7, 10),
    "B2": (8, 12),
    "C1": (9, 14),
    "C2": (10, 16),
}


def _page_bounds(level):
    return _PAGE_BOUNDS.get(level, _PAGE_BOUNDS[DEFAULT_LEVEL])


def _clean(suggestion, level):
    """Validates one generated suggestion, or returns None if it is unusable."""
    if not isinstance(suggestion, dict):
        return None

    topic = str(suggestion.get("topic", "")).strip()
    setting = str(suggestion.get("setting", "")).strip()
    drills = str(suggestion.get("drills", "")).strip()
    if not topic or not setting:
        return None

    low, high = _page_bounds(level)
    try:
        pages = int(suggestion.get("pages", low))
    except (TypeError, ValueError):
        pages = low

    return {
        "topic": topic,
        "setting": setting,
        "drills": drills or "Level-appropriate everyday language",
        "pages": max(3, min(20, max(low, min(high, pages)))),
    }


def _recent_story_topics():
    """Topics the user has already turned into books, so we stop offering them."""
    try:
        from history_manager import get_used_themes
        return [theme.get("activity", "") for theme in get_used_themes() if theme.get("activity")]
    except Exception:
        return []


def generate_topic_suggestions(level=None, count=6, avoid=None, language="fi"):
    """
    Asks the model for fresh topic ideas for a level.

    Returns [] on any failure — callers fall back to the curated list rather
    than showing an empty panel.
    """
    language = _language(language)
    if level not in TOPIC_SUGGESTIONS_BY_LANGUAGE[language]:
        level = DEFAULT_LEVEL

    seen = list(avoid or []) + _recent_topics.get((language, level), []) + _recent_story_topics()
    avoid_clause = ""
    if seen:
        listed = "\n".join(f"- {topic}" for topic in seen[-_RECENT_MEMORY:])
        avoid_clause = (
            "Do NOT repeat or lightly reword any of these, which the user has already been shown:\n"
            f"{listed}\n\n"
        )

    constraints = SV_LEVEL_CONSTRAINTS if language == "sv" else LEVEL_CONSTRAINTS
    low, high = _page_bounds(level)
    prompt = SUGGESTION_PROMPT.format(
        name=LANGUAGES[language]["adjective"],
        culture_rule=LANGUAGES[language]["culture_rule"],
        count=count,
        level=level,
        constraints=constraints.get(level, constraints[DEFAULT_LEVEL]).strip(),
        min_pages=low,
        max_pages=high,
        avoid_clause=avoid_clause,
    )

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        text = model.generate_content(prompt).text
        text = text.replace("```json", "").replace("```", "").strip()
        raw = json.loads(text)
    except Exception as exc:  # network, quota, malformed JSON — all non-fatal
        print(f"Topic suggestion generation failed ({exc}); using curated list.")
        return []

    if not isinstance(raw, list):
        return []

    suggestions = [s for s in (_clean(item, level) for item in raw) if s]
    if not suggestions:
        return []

    remembered = _recent_topics.setdefault((language, level), [])
    remembered.extend(s["topic"] for s in suggestions)
    del remembered[:-_RECENT_MEMORY]

    return suggestions


# The model is only ever called because someone asked for ideas — opening the
# panel or pressing "New ideas". Generated batches are kept per level for the
# life of the process, so reopening the panel costs nothing.
_cache = {}
_cache_lock = threading.Lock()


def _curated_sample(level, count, language="fi"):
    curated = list(get_topic_suggestions(level, language))
    random.shuffle(curated)
    return curated[:count]


def get_suggestions(level=None, count=6, refresh=False, allow_generate=True, language="fi"):
    """
    Returns suggestions for a level plus where they came from ("ai"/"curated").

    Serves the cached batch when there is one. Calls the model only when asked
    to: `refresh` always regenerates, and a cold level generates once unless
    `allow_generate` is False, in which case the curated list stands in.
    """
    language = _language(language)
    if level not in TOPIC_SUGGESTIONS_BY_LANGUAGE[language]:
        level = DEFAULT_LEVEL
    key = (language, level)

    if not refresh:
        with _cache_lock:
            cached = _cache.get(key)
        if cached:
            return cached[:count], "ai"

    if not allow_generate:
        return _curated_sample(level, count, language), "curated"

    generated = generate_topic_suggestions(level, count=count, language=language)
    if generated:
        with _cache_lock:
            _cache[key] = generated
        return generated, "ai"

    return _curated_sample(level, count, language), "curated"
