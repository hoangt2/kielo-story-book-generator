# Prompts for Finnish Story Generator
import random

from cinematography import CAMERA_STYLE_GUIDE, build_shot_plan, format_shot_plan

# Theme categories for UI selection
THEME_CATEGORIES = {
    "random": "🎲 Random (Any Theme)",
    "winter": "❄️ Winter",
    "spring": "🌸 Spring", 
    "summer": "☀️ Summer",
    "autumn": "🍂 Autumn",
    "everyday": "🏠 Everyday Life",
    "special": "✨ Special Occasions",
}

# Diverse story themes with categories
STORY_THEMES = [
    # Winter themes
    {"category": "winter", "season": "Winter", "setting": "a ski resort in Lapland", "activity": "learning to ski or snowboard", "mood": "adventurous"},
    {"category": "winter", "season": "Winter", "setting": "a cozy cabin (mökki) by a frozen lake", "activity": "ice fishing and making hot cocoa", "mood": "peaceful"},
    {"category": "winter", "season": "Winter", "setting": "Helsinki during Christmas markets", "activity": "shopping for gifts and drinking glögi", "mood": "festive"},
    {"category": "winter", "season": "Winter", "setting": "a school during winter break", "activity": "building a snow fort or ice skating", "mood": "playful"},
    {"category": "winter", "season": "Winter", "setting": "the Northern Lights viewing area in Rovaniemi", "activity": "waiting to see aurora borealis", "mood": "magical"},
    {"category": "winter", "season": "Winter", "setting": "a Finnish home on Independence Day (December 6th)", "activity": "lighting candles and watching the presidential ball on TV", "mood": "patriotic"},
    {"category": "winter", "season": "Winter", "setting": "a cross-country ski trail in a snowy forest", "activity": "skiing with friends or family", "mood": "invigorating"},
    {"category": "winter", "season": "Winter", "setting": "a cozy library during a snowstorm", "activity": "reading books and drinking tea", "mood": "cozy"},
    
    # Spring themes
    {"category": "spring", "season": "Spring", "setting": "a park during Vappu (May Day) celebration", "activity": "having a picnic and watching students celebrate", "mood": "joyful"},
    {"category": "spring", "season": "Spring", "setting": "a Finnish school", "activity": "preparing for graduation or exams", "mood": "hopeful"},
    {"category": "spring", "season": "Spring", "setting": "a garden or allotment", "activity": "planting vegetables and flowers", "mood": "refreshing"},
    {"category": "spring", "season": "Spring", "setting": "a nature trail in a national park", "activity": "bird watching as birds return from migration", "mood": "curious"},
    {"category": "spring", "season": "Spring", "setting": "a Finnish town during Easter", "activity": "children dressed as witches going door-to-door (virpominen)", "mood": "playful"},
    {"category": "spring", "season": "Spring", "setting": "a lakeside during ice melting season", "activity": "watching ice break up and birds return", "mood": "hopeful"},
    {"category": "spring", "season": "Spring", "setting": "a city during spring cleaning", "activity": "cleaning and organizing the home", "mood": "productive"},
    
    # Summer themes
    {"category": "summer", "season": "Summer", "setting": "a summer cottage (kesämökki)", "activity": "swimming, sauna, and grilling makkara", "mood": "relaxing"},
    {"category": "summer", "season": "Summer", "setting": "a music festival like Ruisrock or Flow", "activity": "enjoying live music and meeting new friends", "mood": "exciting"},
    {"category": "summer", "season": "Summer", "setting": "an island in the Finnish archipelago", "activity": "kayaking and exploring nature", "mood": "adventurous"},
    {"category": "summer", "season": "Summer", "setting": "a Finnish baseball (pesäpallo) game", "activity": "cheering for the local team", "mood": "energetic"},
    {"category": "summer", "season": "Summer", "setting": "midnight sun in Lapland", "activity": "hiking at midnight when the sun doesn't set", "mood": "surreal"},
    {"category": "summer", "season": "Summer", "setting": "a Midsummer (Juhannus) celebration", "activity": "dancing around the bonfire and enjoying sauna", "mood": "festive"},
    {"category": "summer", "season": "Summer", "setting": "a Finnish beach (uimaranta)", "activity": "swimming and having a picnic", "mood": "carefree"},
    {"category": "summer", "season": "Summer", "setting": "a forest looking for berries", "activity": "picking wild blueberries or lingonberries", "mood": "peaceful"},
    {"category": "summer", "season": "Summer", "setting": "a harbor watching boats", "activity": "learning about sailing or fishing", "mood": "curious"},
    
    # Autumn themes  
    {"category": "autumn", "season": "Autumn", "setting": "a forest during ruska (fall foliage)", "activity": "picking mushrooms and berries", "mood": "peaceful"},
    {"category": "autumn", "season": "Autumn", "setting": "a library or bookstore", "activity": "discovering a new favorite book", "mood": "cozy"},
    {"category": "autumn", "season": "Autumn", "setting": "a Finnish school on the first day", "activity": "meeting new classmates", "mood": "nervous but exciting"},
    {"category": "autumn", "season": "Autumn", "setting": "a farm during harvest time", "activity": "helping with apple picking", "mood": "hardworking"},
    {"category": "autumn", "season": "Autumn", "setting": "a café during a rainy day", "activity": "drinking coffee and people-watching", "mood": "reflective"},
    {"category": "autumn", "season": "Autumn", "setting": "a Halloween party in Finland", "activity": "carving pumpkins and wearing costumes", "mood": "spooky fun"},
    {"category": "autumn", "season": "Autumn", "setting": "a nature reserve during bird migration", "activity": "watching cranes fly south", "mood": "contemplative"},
    {"category": "autumn", "season": "Autumn", "setting": "a Finnish home preparing for winter", "activity": "putting up winter tires or storing summer things", "mood": "practical"},
    
    # Everyday life themes
    {"category": "everyday", "season": "any season", "setting": "a Finnish sauna", "activity": "experiencing traditional sauna rituals", "mood": "relaxing"},
    {"category": "everyday", "season": "any season", "setting": "a hospital or clinic", "activity": "visiting a doctor or visiting a friend", "mood": "caring"},
    {"category": "everyday", "season": "any season", "setting": "a train traveling across Finland (VR)", "activity": "a journey from south to north", "mood": "contemplative"},
    {"category": "everyday", "season": "any season", "setting": "a workplace or office", "activity": "the first day at a new job", "mood": "nervous"},
    {"category": "everyday", "season": "any season", "setting": "a Finnish home kitchen", "activity": "cooking a traditional Finnish meal together", "mood": "warm"},
    {"category": "everyday", "season": "any season", "setting": "a museum like Ateneum or Kiasma", "activity": "learning about Finnish art", "mood": "curious"},
    {"category": "everyday", "season": "any season", "setting": "a supermarket (K-Market or S-Market)", "activity": "doing weekly grocery shopping", "mood": "everyday"},
    {"category": "everyday", "season": "any season", "setting": "a gym or sports center", "activity": "trying a new sport or exercise class", "mood": "energetic"},
    {"category": "everyday", "season": "any season", "setting": "a public swimming hall (uimahalli)", "activity": "swimming laps and relaxing in the sauna", "mood": "refreshing"},
    {"category": "everyday", "season": "any season", "setting": "an apartment building (kerrostalo)", "activity": "meeting neighbors or dealing with a maintenance issue", "mood": "community"},
    {"category": "everyday", "season": "any season", "setting": "a Finnish bus or tram", "activity": "commuting to work or school", "mood": "routine"},
    {"category": "everyday", "season": "any season", "setting": "a post office or package pickup point", "activity": "sending or receiving a package", "mood": "practical"},
    {"category": "everyday", "season": "any season", "setting": "a Finnish bank or KELA office", "activity": "handling paperwork or asking for help", "mood": "bureaucratic"},
    {"category": "everyday", "season": "any season", "setting": "a hairdresser or barber shop", "activity": "getting a new haircut", "mood": "social"},
    
    # Special occasions and character-focused themes
    {"category": "special", "season": "any season", "setting": "anywhere in Finland", "activity": "an immigrant's first winter in Finland", "mood": "cultural discovery"},
    {"category": "special", "season": "any season", "setting": "a retirement home or elderly person's house", "activity": "a grandchild visiting grandparents", "mood": "intergenerational"},
    {"category": "special", "season": "any season", "setting": "a pet store or animal shelter", "activity": "adopting a pet", "mood": "heartwarming"},
    {"category": "special", "season": "any season", "setting": "a Finnish-Swedish bilingual area like Vaasa", "activity": "navigating two languages", "mood": "educational"},
    {"category": "special", "season": "any season", "setting": "a wedding venue", "activity": "attending a Finnish wedding", "mood": "celebratory"},
    {"category": "special", "season": "any season", "setting": "a Finnish church or cemetery (hautausmaa)", "activity": "remembering loved ones on All Saints' Day", "mood": "thoughtful"},
    {"category": "special", "season": "any season", "setting": "a children's birthday party", "activity": "celebrating with games and cake", "mood": "joyful"},
    {"category": "special", "season": "any season", "setting": "a driving school", "activity": "learning to drive in Finnish conditions", "mood": "challenging"},
    {"category": "special", "season": "any season", "setting": "a Finnish language course classroom", "activity": "learning Finnish with classmates from around the world", "mood": "educational"},
    {"category": "special", "season": "any season", "setting": "an escape room or game café", "activity": "solving puzzles with friends", "mood": "fun"},
]

def get_theme_categories():
    """Returns available theme categories for the UI dropdown."""
    return THEME_CATEGORIES

def get_themes_by_category(category=None):
    """Returns themes filtered by category. If None or 'random', returns all themes."""
    if category is None or category == "random":
        return STORY_THEMES
    return [t for t in STORY_THEMES if t["category"] == category]

def select_theme(category=None, used_themes=None):
    """
    Selects a random theme from the specified category, avoiding recently used themes.
    
    Args:
        category: Theme category (e.g., 'winter', 'summer') or None/'random' for any
        used_themes: List of recently used theme settings to avoid
    """
    available_themes = get_themes_by_category(category)
    
    # Filter out recently used themes if provided
    if used_themes:
        # Create a set of (setting, activity) tuples that were recently used
        used_set = {(t.get("setting"), t.get("activity")) for t in used_themes}
        filtered = [t for t in available_themes if (t["setting"], t["activity"]) not in used_set]
        
        # If we've used all themes in this category, just use all available
        if filtered:
            available_themes = filtered
    
    return random.choice(available_themes)


# CEFR writing constraints per level, shared with the topic suggester.
LEVEL_CONSTRAINTS = {
    "A1": """
**Constraints:**
1.  **Level:** A1 (Breakthrough).
2.  **Sentence Structure:** Very simple Subject-Verb or Subject-Verb-Object only. One clause per sentence.
3.  **Verb Forms:** Present tense only (minä olen, hän menee). Only 1st and 3rd person singular.
4.  **Cases:** Nominative and basic Partitive only. No complex case endings.
5.  **Vocabulary:** Most basic everyday words only (max 200-300 most common Finnish words). Greetings, numbers, colors, family, food.
6.  **Sentence Length:** 3-6 words per sentence maximum.
7.  **Grammar:** No negation chains. Simple "ei" negation only. No possessive suffixes.
""",
    "A2": """
**Constraints:**
1.  **Level:** A2 (Elementary).
2.  **Sentence Structure:** Simple Subject-Verb-Object (SVO). Avoid complex inversions. Occasional "ja" (and) conjunctions.
3.  **Verb Forms:** Present (minä asun) and simple past (hän käveli). Minimize perfect tenses/passive.
4.  **Cases:** Nominative, Partitive, Illative, Inessive. Avoid complex cases.
5.  **Vocabulary:** Common, everyday words (max 500 most common Finnish words). Daily routines, shopping, weather.
6.  **Sentence Length:** 5-10 words per sentence maximum.
7.  **Grammar:** Simple negation. Basic postpositions. No complex verb chains.
""",
    "B1": """
**Constraints:**
1.  **Level:** B1 (Intermediate).
2.  **Sentence Structure:** Mix of simple and compound sentences. Basic subordinate clauses with "koska" (because), "kun" (when).
3.  **Verb Forms:** Present, past, and perfect tenses. Introduce conditional mood (haluaisin). Some passive voice.
4.  **Cases:** All basic cases including Elative, Adessive, Ablative, Allative. Introduce Essive occasionally.
5.  **Vocabulary:** Broader vocabulary including common abstract concepts. Opinions, emotions, plans.
6.  **Sentence Length:** 8-12 words per sentence.
7.  **Grammar:** Comparative adjectives. Basic relative clauses. Simple infinitive constructions.
""",
    "B2": """
**Constraints:**
1.  **Level:** B2 (Upper Intermediate).
2.  **Sentence Structure:** Compound and complex sentences. Multiple subordinate clauses. Relative clauses with "joka".
3.  **Verb Forms:** All common tenses and moods. Conditional and passive used naturally. Perfect and pluperfect tenses.
4.  **Cases:** All common cases used naturally including Essive and Translative.
5.  **Vocabulary:** Rich vocabulary including abstract concepts, less common words, and some idiomatic expressions.
6.  **Sentence Length:** 10-15 words per sentence.
7.  **Grammar:** Participial constructions. Complex verb chains. Possessive suffixes.
""",
    "C1": """
**Constraints:**
1.  **Level:** C1 (Advanced).
2.  **Sentence Structure:** Complex sentences with multiple clauses, inversions, and varied structures. Natural Finnish word order.
3.  **Verb Forms:** All tenses and moods including potential mood. Passive voice used frequently and naturally.
4.  **Cases:** All 15 cases used naturally, including Comitative and Instructive where appropriate.
5.  **Vocabulary:** Rich, nuanced vocabulary. Some idioms, colloquialisms, and varied register.
6.  **Sentence Length:** 10-18 words per sentence. Varied for rhythm.
7.  **Grammar:** Agent participles. Temporal constructions. Nuanced modal expressions.
""",
    "C2": """
**Constraints:**
1.  **Level:** C2 (Mastery).
2.  **Sentence Structure:** Fully natural Finnish prose. Complex nested clauses, literary devices, and stylistic variation.
3.  **Verb Forms:** All tenses, moods, and voices used masterfully. Archaic or literary forms where stylistically appropriate.
4.  **Cases:** All 15 cases deployed with native-like precision and frequency.
5.  **Vocabulary:** Extensive vocabulary including literary expressions, proverbs, wordplay, and register-appropriate language.
6.  **Sentence Length:** 12-25 words per sentence. Varied and rhythmic.
7.  **Grammar:** Full command of Finnish grammar. Rare constructions, emphasis particles, and discourse markers used naturally.
"""
}


def get_story_prompt(level="A1", previous_stories=None, theme_category=None, used_themes=None, custom_topic=None, page_count=10, custom_setting=None, grammar_feedback=None):
    """
    Generate a story prompt based on the difficulty level, history, and theme.
    
    Args:
        level: "A1", "A2", "B1", "B2", "C1", or "C2"
        previous_stories: List of dicts containing info about past stories.
        theme_category: Optional category to constrain theme selection
        used_themes: List of recently used themes to avoid
        grammar_feedback: Feedback from a previous failed grammar check to avoid the same mistakes
    """

    
    constraints = LEVEL_CONSTRAINTS.get(level, LEVEL_CONSTRAINTS["A1"])
    
    # Build history context
    history_context = ""
    if previous_stories:
        history_list = "\n".join([f"- {s.get('title_en')} (Characters: {', '.join(s.get('characters', []))})" for s in previous_stories])
        history_context = f"""
**AVOID REPETITION:**
The following stories have already been generated. DO NOT repeat these exact plots, titles, or character combinations.
{history_list}
"""
    
    
    # Select a theme for this story (respecting category and avoiding used themes)
    if custom_topic:
        theme_instruction = f"""
**MANDATORY CUSTOM TOPIC (You MUST follow this):**
The user has requested a story about: **{custom_topic}**

- **Topic:** {custom_topic}
- **Season & Setting:** Choose an appropriate season and valid Finnish setting for this topic. {'(Use the user-provided setting below)' if custom_setting else '(Choose a diverse setting)'}
- **Mood:** Choose a mood that matches the topic.

**CREATIVITY GUIDELINES:**
- The story must center around the requested topic.
- The story is about daily situations, not a fairy tale (unless the topic implies otherwise, but try to keep it grounded in reality/authentic Finnish culture).
- The story should be engaging and interesting.
- Add some humor to the story when appropriate.
- Create diverse characters: Different ages, backgrounds, professions, include foreigners/immigrants when fitting.
- There can be animals in the story to make it more interesting.
- Make the ending satisfying and memorable.
"""
    else:
        theme = select_theme(category=theme_category, used_themes=used_themes)
        theme_instruction = f"""
**MANDATORY THEME (You MUST follow this):**
- **Season:** {theme['season']}
- **Setting:** {theme['setting']}
- **Main Activity:** {theme['activity']}
- **Mood/Tone:** {theme['mood']}

**CREATIVITY GUIDELINES:**
- DO NOT make stories about buying strawberries at a market/tori
- The story is about daily situations, not a fairy tale
- The story should be engaging and interesting, incorporating authentic Finnish culture
- Add some humor to the story when appropriate
- Create diverse characters: Different ages, backgrounds, professions, include foreigners/immigrants when fitting
- There can be animals in the story to make it more interesting
- Make the ending satisfying and memorable
"""

    
    # Setting instruction
    setting_instruction = "7.  **Setting:** "
    if custom_setting:
        setting_instruction += f"{custom_setting}. (You MUST use this specific setting!)"
    else:
        setting_instruction += "A REAL, specific location in Finland (e.g., Helsinki, Tampere, Turku, Oulu, Rovaniemi, Porvoo, at home, at school, at work, etc.). AVOID repetitive famous tourist spots (like Helsinki Market Square) unless specifically requested. Use diverse settings: libraries, parks, suburbs, small towns, nature trails, etc."

    # One camera framing per page, so the illustrations do not all end up as the
    # same straight-on mid shot (see cinematography.py).
    shot_plan_instruction = format_shot_plan(build_shot_plan(page_count))

    return f"""
You are a Finnish language learning content creator. Your goal is to generate an engaging and UNIQUE story for {level} level learners.

{history_context}

{theme_instruction}

{constraints}
{setting_instruction}
8.  **Length:** EXACTLY {page_count} pages (plus cover).
9.  **Format:** Return ONLY a valid JSON object.
{f'''
**⚠️ CRITICAL: PREVIOUS GRAMMAR ERRORS — DO NOT REPEAT THESE MISTAKES:**
A previous version of this story was rejected for the following grammar issues. You MUST avoid these exact errors in your new version:
{grammar_feedback}

Pay extra attention to:
- Correct Finnish case usage (partitive, accusative, etc.)
- Natural Finnish word order and phrasing (avoid direct translations from English)
- Proper Finnish name constructions (e.g., use "Anni-tyttö" not "tyttö Anni")
''' if grammar_feedback else ''}

**CRITICAL INSTRUCTION: VISUAL CONSISTENCY**
- **Randomly decide** to have 1, 2, or 3 main characters for the story.
- You MUST define ALL main characters in the `characters` list.
- **IMPORTANT**: In every `image_description`, you MUST repeat the **FULL VISUAL DESCRIPTION** of ALL characters present in the scene. Do NOT just use their names.
    - BAD: "Sofia is smiling."
    - GOOD: "Sofia, a young girl with curly blonde hair wearing a blue dress, is smiling."

**CRITICAL INSTRUCTION: NARRATIVE PERSPECTIVE CONSISTENCY**
- Choose ONE narrative perspective for the entire story and keep it consistent on EVERY page.
- If the story uses 3rd person (hän, Samu, isä), ALL pages must use 3rd person.
- If the story uses 1st person (minä), ALL pages must use 1st person.
- NEVER switch perspective mid-story. The camera shot type (e.g. FIRST-PERSON POV) describes only the ILLUSTRATION angle — it must NOT change the grammatical person of the Finnish text.

{shot_plan_instruction}

**TITLE GUIDELINES:**
- Do NOT use "[Activity] in [Place]" format (e.g., avoid "Ice Cream Summer in Tampere", "Swimming in Helsinki").
- Do NOT use overly dramatic or mysterious titles (e.g., avoid "The Sweet Mystery", "The Secret Recipe", "The Hidden Truth").
- Instead, use NATURAL, straightforward titles that describe what the story is about.
- Good examples: "Oliverin jäätelökioski" / "Oliver's Ice Cream Kiosk", "Uusi naapuri" / "The New Neighbor", "Pikon ensimmäinen talvi" / "Piko's First Winter", "Saunapäivä" / "Sauna Day".
- The title should feel natural and fitting — like the name of a short story, not a thriller or a fairy tale.

**JSON Structure:**
{{
  "title_fi": "Natural Finnish Title",
  "title_en": "Natural English Title",
  "characters": [
    {{
      "name": "Name",
      "description": "Detailed visual description (hair, skin, clothes, accessories)."
    }}
  ],
  "pages": [
    {{
      "page_number": 1,
      "type": "cover",
      "text_fi": "Title of the story",
      "text_en": "Title of the story",
      "image_description": "HERO POSTER SHOT: a dynamic, mid-action scene that teases the story. Show characters DOING something (not standing still). The subject of the title (object, animal, place, etc.) MUST be prominently visible — if the title is 'The Blue Backpack', the blue backpack must be large and obvious. INCLUDE FULL CHARACTER DETAILS."
    }},
    {{
      "page_number": 2,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "<THIS PAGE'S ASSIGNED SHOT NAME>: visual description written so the camera angle, height and distance are unmistakable. REMEMBER TO DESCRIBE CHARACTERS FULLY."
    }},
    {{
      "page_number": 3,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "<THIS PAGE'S ASSIGNED SHOT NAME>: visual description..."
    }},
    {{
      "page_number": 4,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "<THIS PAGE'S ASSIGNED SHOT NAME>: visual description..."
    }},
    {{
      "page_number": 5,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "<THIS PAGE'S ASSIGNED SHOT NAME>: visual description..."
    }},
    {{
      "page_number": 6,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "<THIS PAGE'S ASSIGNED SHOT NAME>: visual description..."
    }},
    {{
      "page_number": 7,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "<THIS PAGE'S ASSIGNED SHOT NAME>: visual description..."
    }}
  ]
}}
"""

IMAGE_STYLE_GUIDE = """
Illustration style: A playful, modern minimalist doodle-style 2D illustration. 
The illustration must feature bold, thick, uniform black outlines with flat, naturalistic colors.
Do not use gradients, 3D rendering, or complex shading. Characters should have friendly, exaggerated proportions with simple, clean features. 
High quality vector-art style.

IMPORTANT: Do NOT include any text, words, letters, or numbers in the image. The image should be purely visual.
""" + CAMERA_STYLE_GUIDE
