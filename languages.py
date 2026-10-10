# Per-language settings for the story generator.
#
# Each language supplies the wording the prompts need (adjective, country,
# culture, grammar reminders) plus its own CEFR constraints, story themes and
# curated topic ideas. Story JSON is keyed by language code: `title_<code>` and
# `text_<code>` (so Finnish keeps `text_fi`, matching older archives).

DEFAULT_LANGUAGE = "fi"

LANGUAGES = {
    "fi": {
        "code": "fi",
        "name": "Finnish",
        "label": "🇫🇮 Finnish (Suomi)",
        "adjective": "Finnish",
        "country": "Finland",
        "culture_rule": "Set them in Finland, or in ordinary life a person in Finland would recognise. Use real Finnish places, seasons and culture (mökki, sauna, ruska, vappu, talkoot, kaupat…).",
        "location_examples": "Helsinki, Tampere, Turku, Oulu, Rovaniemi, Porvoo",
        "tourist_spot": "Helsinki Market Square",
        "perspective_3rd": "hän, Samu, isä",
        "perspective_1st": "minä",
        "title_examples": '"Oliverin jäätelökioski" / "Oliver\'s Ice Cream Kiosk", "Uusi naapuri" / "The New Neighbor", "Pikon ensimmäinen talvi" / "Piko\'s First Winter", "Saunapäivä" / "Sauna Day"',
        "grammar_reminders": """- Correct Finnish case usage (partitive, accusative, etc.)
- Natural Finnish word order and phrasing (avoid direct translations from English)
- Proper Finnish name constructions (e.g., use "Anni-tyttö" not "tyttö Anni")""",
        "grammar_checks": """- Watch out for "Minulla on hyvä" (I have good) -> SHOULD BE "Minulla on kaikki hyvin" or "Minulle kuuluu hyvää".
- Watch out for "Otan bussia" (I take bus) -> SHOULD BE "Menen bussilla".
- Ensure object cases (partitive vs genitive/accusative) are correct for the context.""",
        "grammar_example_feedback": """e.g., 'Minulla on myös hyvä' is an unnatural direct translation, suggest 'Minulle kuuluu myös hyvää'""",
        "grammar_sample": "Minä olen kissa.",
        "cliche": "DO NOT make stories about buying strawberries at a market/tori",
    },
    "sv": {
        "code": "sv",
        "name": "Swedish",
        "label": "🇸🇪 Swedish (Svenska)",
        "adjective": "Swedish",
        "country": "Sweden",
        "culture_rule": "Set them in Sweden, or in ordinary life a person in Sweden would recognise. Use real Swedish places, seasons and culture (fika, midsommar, lucia, kräftskiva, skärgården, påsk…).",
        "location_examples": "Stockholm, Göteborg, Malmö, Uppsala, Lund, Umeå, Visby",
        "tourist_spot": "Gamla stan",
        "perspective_3rd": "hon, Sam, pappa",
        "perspective_1st": "jag",
        "title_examples": '"Olivers glasskiosk" / "Oliver\'s Ice Cream Kiosk", "Den nya grannen" / "The New Neighbor", "Pikes första vinter" / "Pike\'s First Winter", "Bastukväll" / "Sauna Evening"',
        "grammar_reminders": """- Correct en/ett genders and definite forms (en bil → bilen, ett hus → huset)
- Correct verb word order: the verb is second in main clauses ("Igår gick jag…", not "Igår jag gick…")
- Natural Swedish word order and phrasing (avoid direct translations from English)
- Correct use of "att" in subordinate clauses and idiomatic prepositions""",
        "grammar_checks": """- Watch out for wrong gender: "en hus" -> SHOULD BE "ett hus"; "ett bil" -> SHOULD BE "en bil".
- Watch out for word order: "Igår jag gick" -> SHOULD BE "Igår gick jag".
- Watch out for English calques: "Jag har 20 år" -> SHOULD BE "Jag är 20 år".
- Ensure the right tense is used (preteritum vs perfekt) and that definite/indefinite forms fit the context.""",
        "grammar_example_feedback": """e.g., 'Igår jag gick' is wrong word order, suggest 'Igår gick jag'""",
        "grammar_sample": "Jag är en katt.",
        "cliche": "DO NOT make stories about buying strawberries at a market (torg)",
    },
}


def normalize_language(code):
    """Returns a supported language code, falling back to the default."""
    return code if code in LANGUAGES else DEFAULT_LANGUAGE


def title_key(code):
    return f"title_{normalize_language(code)}"


def text_key(code):
    return f"text_{normalize_language(code)}"


# --- Swedish CEFR constraints -----------------------------------------------
# Swedish has no case endings, so the constraints track gender (en/ett),
# definiteness, word order and tense instead.

SV_LEVEL_CONSTRAINTS = {
    "A1": """
**Constraints:**
1.  **Level:** A1 (Breakthrough).
2.  **Sentence Structure:** Very simple Subject-Verb or Subject-Verb-Object only. One clause per sentence. The verb is always second in the sentence.
3.  **Verb Forms:** Present tense only (jag är, hon har, han bor). No past tense.
4.  **Nouns:** Basic nouns with en/ett (en katt, ett hus). Only the most common definite forms (huset).
5.  **Vocabulary:** Most basic everyday words only (max 200-300 most common Swedish words). Greetings, numbers, colours, family, food.
6.  **Sentence Length:** 3-6 words per sentence maximum.
7.  **Grammar:** Simple "inte" negation only. No compound tenses, no passive, no subordinate clauses.
""",
    "A2": """
**Constraints:**
1.  **Level:** A2 (Elementary).
2.  **Sentence Structure:** Simple Subject-Verb-Object (SVO). Simple connectors "och", "men", "för". Keep word order simple.
3.  **Verb Forms:** Present (jag bor) and simple past of common verbs (hon gick, han åt). Simple perfect with "har" + past participle. Minimize passive.
4.  **Nouns:** en/ett genders and definite forms. Prepositions i, på, till, från, med.
5.  **Vocabulary:** Common, everyday words (max 500 most common Swedish words). Daily routines, shopping, weather.
6.  **Sentence Length:** 5-10 words per sentence maximum.
7.  **Grammar:** Simple negation. Possessives min/din/sin. No complex verb chains.
""",
    "B1": """
**Constraints:**
1.  **Level:** B1 (Intermediate).
2.  **Sentence Structure:** Mix of simple and compound sentences. Subordinate clauses with "att", "när", "om", "eftersom".
3.  **Verb Forms:** Present, past, and perfect tenses. Introduce the conditional (skulle). Some passive (blir, blev).
4.  **Nouns:** Definite and indefinite forms used consistently. Comparative and superlative adjectives.
5.  **Vocabulary:** Broader vocabulary including common abstract concepts. Opinions, emotions, plans.
6.  **Sentence Length:** 8-12 words per sentence.
7.  **Grammar:** Basic relative clauses with "som". Simple infinitive constructions (att göra).
""",
    "B2": """
**Constraints:**
1.  **Level:** B2 (Upper Intermediate).
2.  **Sentence Structure:** Compound and complex sentences. Multiple subordinate clauses. Relative clauses with "som" and "vilket".
3.  **Verb Forms:** All common tenses and moods. Conditional and passive used naturally. Pluperfect (hade + past participle).
4.  **Nouns:** Correct en/ett, definite and indefinite forms, and adjective agreement throughout.
5.  **Vocabulary:** Rich vocabulary including abstract concepts, less common words, and some idiomatic expressions.
6.  **Sentence Length:** 10-15 words per sentence.
7.  **Grammar:** Modal particles (ju, väl, nog). Participial constructions. Complex verb chains.
""",
    "C1": """
**Constraints:**
1.  **Level:** C1 (Advanced).
2.  **Sentence Structure:** Complex sentences with multiple clauses, inversions, and varied structures. Natural Swedish word order.
3.  **Verb Forms:** All tenses and moods. Passive voice used frequently and naturally. Set subjunctive-like forms (vore, finge) where idiomatic.
4.  **Nouns:** Full command of definiteness, agreement, and prepositional usage.
5.  **Vocabulary:** Rich, nuanced vocabulary. Some idioms, colloquialisms, and varied register.
6.  **Sentence Length:** 10-18 words per sentence. Varied for rhythm.
7.  **Grammar:** Participial constructions. Temporal clauses. Nuanced modal expressions and modal particles.
""",
    "C2": """
**Constraints:**
1.  **Level:** C2 (Mastery).
2.  **Sentence Structure:** Fully natural Swedish prose. Complex nested clauses, literary devices, and stylistic variation.
3.  **Verb Forms:** All tenses, moods, and voices used masterfully. Archaic or literary forms where stylistically appropriate.
4.  **Nouns:** Native-like precision in definiteness, agreement, and word order.
5.  **Vocabulary:** Extensive vocabulary including literary expressions, proverbs, wordplay, and register-appropriate language.
6.  **Sentence Length:** 12-25 words per sentence. Varied and rhythmic.
7.  **Grammar:** Full command of Swedish grammar. Rare constructions, modal particles, and discourse markers used naturally.
""",
}

SV_LEVEL_HINTS = {
    "A1": "A1 allows 3–6 word sentences, present tense and basic en/ett nouns only. These topics repeat a small set of concrete nouns so the story stays inside that.",
    "A2": "A2 adds the simple past and everyday prepositions. These topics follow a clear sequence of events with familiar daily vocabulary.",
    "B1": "B1 allows subordinate clauses with att/när/eftersom and the conditional. These topics need opinions, plans and reasons — not just description.",
    "B2": "B2 handles complex clauses and abstract ideas. These topics carry a disagreement or a shift in perspective.",
    "C1": "C1 uses all tenses and registers naturally. These topics lean on nuance, contrast and reflection.",
    "C2": "C2 is native-level prose. These topics invite literary devices, dialect, register play and wordplay.",
}

# --- Swedish story themes ---------------------------------------------------

SV_STORY_THEMES = [
    # Winter
    {"category": "winter", "season": "Winter", "setting": "a ski resort in Åre", "activity": "learning to ski or snowboard", "mood": "adventurous"},
    {"category": "winter", "season": "Winter", "setting": "a cozy cabin (stuga) by a frozen lake", "activity": "ice skating and drinking hot chocolate", "mood": "peaceful"},
    {"category": "winter", "season": "Winter", "setting": "Stockholm during the Christmas markets", "activity": "shopping for gifts and drinking glögg", "mood": "festive"},
    {"category": "winter", "season": "Winter", "setting": "a school on Lucia morning", "activity": "singing and serving saffron buns (lussekatter)", "mood": "festive"},
    {"category": "winter", "season": "Winter", "setting": "the northern lights area near Kiruna", "activity": "waiting to see the aurora borealis", "mood": "magical"},
    {"category": "winter", "season": "Winter", "setting": "a cross-country ski trail in a snowy forest", "activity": "skiing with friends or family", "mood": "invigorating"},
    {"category": "winter", "season": "Winter", "setting": "a cozy library during a snowstorm", "activity": "reading books and having fika", "mood": "cozy"},
    {"category": "winter", "season": "Winter", "setting": "a city park in Umeå after the first snow", "activity": "building a snowman and having a snowball fight", "mood": "playful"},
    # Spring
    {"category": "spring", "season": "Spring", "setting": "a park during Valborg (Walpurgis night)", "activity": "having a picnic and watching the students sing", "mood": "joyful"},
    {"category": "spring", "season": "Spring", "setting": "a Swedish school before graduation", "activity": "preparing for exams and the last day", "mood": "hopeful"},
    {"category": "spring", "season": "Spring", "setting": "a garden allotment (koloni)", "activity": "planting vegetables and flowers", "mood": "refreshing"},
    {"category": "spring", "season": "Spring", "setting": "a nature trail in a national park", "activity": "bird watching as birds return from migration", "mood": "curious"},
    {"category": "spring", "season": "Spring", "setting": "a small town during Easter", "activity": "children dressed as Easter witches (påskkärringar) going door to door", "mood": "playful"},
    {"category": "spring", "season": "Spring", "setting": "a lakeside during the spring thaw", "activity": "watching the ice break up and the geese return", "mood": "hopeful"},
    {"category": "spring", "season": "Spring", "setting": "a city during spring cleaning", "activity": "cleaning and organising the home", "mood": "productive"},
    # Summer
    {"category": "summer", "season": "Summer", "setting": "a summer cottage (sommarstuga)", "activity": "swimming, sauna, and grilling sausages", "mood": "relaxing"},
    {"category": "summer", "season": "Summer", "setting": "a Midsummer (midsommar) celebration in the countryside", "activity": "dancing around the midsummer pole", "mood": "festive"},
    {"category": "summer", "season": "Summer", "setting": "an island in the Stockholm archipelago (skärgården)", "activity": "kayaking and exploring nature", "mood": "adventurous"},
    {"category": "summer", "season": "Summer", "setting": "a crayfish party (kräftskiva) on a summer evening", "activity": "eating crayfish and singing drinking songs", "mood": "social"},
    {"category": "summer", "season": "Summer", "setting": "the midnight sun in Abisko", "activity": "hiking at midnight when the sun does not set", "mood": "surreal"},
    {"category": "summer", "season": "Summer", "setting": "a forest looking for wild blueberries (blåbär)", "activity": "picking berries with grandparents", "mood": "peaceful"},
    {"category": "summer", "season": "Summer", "setting": "a harbour in Visby on Gotland", "activity": "watching sailboats and learning to sail", "mood": "curious"},
    {"category": "summer", "season": "Summer", "setting": "a sandy beach (strand) in Skåne", "activity": "swimming and having a picnic", "mood": "carefree"},
    # Autumn
    {"category": "autumn", "season": "Autumn", "setting": "a forest in full autumn colours", "activity": "picking mushrooms and berries", "mood": "peaceful"},
    {"category": "autumn", "season": "Autumn", "setting": "a library or bookshop in Uppsala", "activity": "discovering a new favourite book", "mood": "cozy"},
    {"category": "autumn", "season": "Autumn", "setting": "a Swedish school on the first day of the autumn term", "activity": "meeting new classmates", "mood": "nervous but exciting"},
    {"category": "autumn", "season": "Autumn", "setting": "an apple orchard in Skåne during harvest", "activity": "helping with apple picking", "mood": "hardworking"},
    {"category": "autumn", "season": "Autumn", "setting": "a café in Stockholm on a rainy day", "activity": "having fika and people-watching", "mood": "reflective"},
    {"category": "autumn", "season": "Autumn", "setting": "a Halloween party in Malmö", "activity": "carving pumpkins and wearing costumes", "mood": "spooky fun"},
    {"category": "autumn", "season": "Autumn", "setting": "a nature reserve during bird migration", "activity": "watching cranes fly south", "mood": "contemplative"},
    {"category": "autumn", "season": "Autumn", "setting": "a Swedish home preparing for winter", "activity": "changing to winter tyres and storing summer things", "mood": "practical"},
    # Everyday life
    {"category": "everyday", "season": "any season", "setting": "a Swedish sauna (bastu)", "activity": "relaxing and taking a dip in cold water", "mood": "relaxing"},
    {"category": "everyday", "season": "any season", "setting": "a health centre (vårdcentral)", "activity": "visiting a doctor or nurse", "mood": "caring"},
    {"category": "everyday", "season": "any season", "setting": "a train travelling from Stockholm to Malmö", "activity": "a long journey through the countryside", "mood": "contemplative"},
    {"category": "everyday", "season": "any season", "setting": "a workplace or office", "activity": "the first day at a new job", "mood": "nervous"},
    {"category": "everyday", "season": "any season", "setting": "a Swedish home kitchen", "activity": "cooking meatballs (köttbullar) together", "mood": "warm"},
    {"category": "everyday", "season": "any season", "setting": "a museum like Vasamuseet or Moderna museet", "activity": "learning about ships or modern art", "mood": "curious"},
    {"category": "everyday", "season": "any season", "setting": "a supermarket (ICA or Coop)", "activity": "doing the weekly grocery shopping", "mood": "everyday"},
    {"category": "everyday", "season": "any season", "setting": "a gym or sports centre", "activity": "trying a new sport or exercise class", "mood": "energetic"},
    {"category": "everyday", "season": "any season", "setting": "a public swimming pool (simhall)", "activity": "swimming laps and relaxing afterwards", "mood": "refreshing"},
    {"category": "everyday", "season": "any season", "setting": "an apartment building (flerfamiljshus)", "activity": "meeting neighbours or fixing a maintenance problem", "mood": "community"},
    {"category": "everyday", "season": "any season", "setting": "a bus or the metro (tunnelbana) in Stockholm", "activity": "commuting to work or school", "mood": "routine"},
    {"category": "everyday", "season": "any season", "setting": "a post office or parcel pickup point", "activity": "sending or collecting a parcel", "mood": "practical"},
    {"category": "everyday", "season": "any season", "setting": "a Swedish Social Insurance Agency office (Försäkringskassan)", "activity": "handling paperwork or asking for help", "mood": "bureaucratic"},
    {"category": "everyday", "season": "any season", "setting": "a hairdresser", "activity": "getting a new haircut and chatting", "mood": "social"},
    # Special occasions and character-focused
    {"category": "special", "season": "any season", "setting": "anywhere in Sweden", "activity": "an immigrant's first winter in Sweden", "mood": "cultural discovery"},
    {"category": "special", "season": "any season", "setting": "a care home (äldreboende)", "activity": "a grandchild visiting a grandparent", "mood": "intergenerational"},
    {"category": "special", "season": "any season", "setting": "an animal shelter", "activity": "adopting a pet", "mood": "heartwarming"},
    {"category": "special", "season": "any season", "setting": "the Swedish-speaking island of Åland in Finland", "activity": "a family trip by ferry and a visit to the local market", "mood": "educational"},
    {"category": "special", "season": "any season", "setting": "a wedding venue in the countryside", "activity": "attending a Swedish wedding", "mood": "celebratory"},
    {"category": "special", "season": "any season", "setting": "a cemetery on All Saints' Day", "activity": "lighting candles for loved ones", "mood": "thoughtful"},
    {"category": "special", "season": "any season", "setting": "a children's birthday party", "activity": "celebrating with games and cake", "mood": "joyful"},
    {"category": "special", "season": "any season", "setting": "a driving school (trafikskola)", "activity": "learning to drive in Swedish traffic", "mood": "challenging"},
    {"category": "special", "season": "any season", "setting": "a Swedish language class for adults (SFI)", "activity": "learning Swedish with classmates from around the world", "mood": "educational"},
    {"category": "special", "season": "any season", "setting": "an escape room", "activity": "solving puzzles with friends", "mood": "fun"},
]

# --- Swedish curated topic ideas (fallback when the model is unavailable) ----

SV_TOPIC_SUGGESTIONS = {
    "A1": [
        {"topic": "A child names the colours of everything on the way to school", "setting": "a leafy street in Göteborg in autumn", "drills": "Colours, 'det är' + adjective, en/ett basics", "pages": 5},
        {"topic": "A grandmother and a child count the ducks on a pond", "setting": "a park pond in Stockholm", "drills": "Numbers 1–10, animal nouns, en/ett", "pages": 5},
        {"topic": "A family eats breakfast and each person says what they eat", "setting": "a Swedish kitchen in the morning", "drills": "Food nouns, 'jag äter / jag dricker', en/ett", "pages": 4},
        {"topic": "A child puts on winter clothes one piece at a time before going out", "setting": "the hall of a Swedish apartment", "drills": "Clothing nouns, present tense, verb second", "pages": 5},
    ],
    "A2": [
        {"topic": "A girl tells what she did yesterday, hour by hour", "setting": "her home and school in Malmö", "drills": "Simple past (gick, åt, var), clock times", "pages": 6},
        {"topic": "Two children take the bus to the swimming pool alone for the first time", "setting": "a city bus and the simhall in Linköping", "drills": "Prepositions i / på / till, directions, tickets", "pages": 6},
        {"topic": "A boy writes a shopping list and finds every item in the shop", "setting": "an ICA store on a Friday afternoon", "drills": "Food vocabulary, plural nouns, prices", "pages": 6},
        {"topic": "A family packs the car for the summer cottage and forgets something", "setting": "a driveway and the road to a sommarstuga", "drills": "Possessives min / din / sin, past tense", "pages": 6},
    ],
    "B1": [
        {"topic": "A woman decides to change jobs and explains her reasons to a friend over fika", "setting": "a café in Stockholm on a rainy afternoon", "drills": "'eftersom', 'att' clauses, conditional 'skulle'", "pages": 8},
        {"topic": "A father and son disagree about whether to take the train or the car to the mountains", "setting": "a kitchen table in Östersund", "drills": "Opinions with 'tycker att', 'för att', comparatives", "pages": 8},
        {"topic": "Neighbours argue about a shared garden fence and find a compromise", "setting": "an apartment courtyard in Västerås", "drills": "Relative clauses with 'som', 'men', 'trots att'", "pages": 8},
        {"topic": "A student from Finland learns that the Swedish word 'lagom' has no easy translation", "setting": "a school in Gävle", "drills": "Abstract nouns, 'när' vs 'om', reflexive verbs", "pages": 9},
    ],
    "B2": [
        {"topic": "A translator struggles with a word that has no equivalent in Swedish", "setting": "a publishing office in Stockholm", "drills": "Passive 'blir / blev', complex clauses, nuance", "pages": 9},
        {"topic": "An older man decides whether to sell the family summer house", "setting": "a summer island in the Stockholm archipelago", "drills": "Modal particles 'ju / väl', pluperfect 'hade', conditional", "pages": 10},
        {"topic": "Two colleagues disagree about a project deadline and must find common ground", "setting": "an office in Malmö", "drills": "Hedging, 'skulle ha' + perfect, relative clauses", "pages": 10},
        {"topic": "A young person regrets a decision and writes a letter to their past self", "setting": "a flat in Göteborg", "drills": "Perfect and pluperfect, reflective language", "pages": 9},
    ],
    "C1": [
        {"topic": "A village debates whether to keep its old school building or sell it", "setting": "a small town in Dalarna", "drills": "Nuanced arguments, passive constructions, register", "pages": 11},
        {"topic": "A woman reflects on allemansrätten and what the freedom to roam means to her", "setting": "a forest walk near Sundsvall", "drills": "Abstract nouns, participial constructions", "pages": 11},
        {"topic": "An elderly couple talk about how their town has changed in fifty years", "setting": "a bench by the harbour in Karlskrona", "drills": "Temporal constructions, idioms, nostalgic register", "pages": 12},
        {"topic": "Two siblings argue over their late father's workshop", "setting": "a barn outside Kalmar", "drills": "Irony, idioms, emotionally nuanced dialogue", "pages": 12},
    ],
    "C2": [
        {"topic": "A poet tries to write about snow without using the word snow", "setting": "a winter cabin in Lapland", "drills": "Metaphor, wordplay, literary register", "pages": 12},
        {"topic": "A story told through the proverbs of a grandmother who has used them all her life", "setting": "a kitchen in Skåne", "drills": "Proverbs, dialect, register shifts", "pages": 13},
        {"topic": "A journalist interviews a fisherman about a sea that is slowly changing", "setting": "a fishing harbour on the west coast", "drills": "Complex nested clauses, varied rhythm", "pages": 13},
        {"topic": "A man returns to his hometown and finds his childhood street renamed", "setting": "a suburb of Norrköping", "drills": "Literary style, subtle irony, stylistic variation", "pages": 13},
    ],
}
