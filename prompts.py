# Prompts for Finnish Story Generator

def get_story_prompt(level="Beginner"):
    """
    Generate a story prompt based on the difficulty level.
    
    Args:
        level: "Beginner", "Intermediate", or "Advanced"
    """
    
    level_constraints = {
        "Beginner": """
**Constraints:**
1.  **Level:** Beginner (A1-A2).
2.  **Sentence Structure:** Simple Subject-Verb-Object (SVO). Avoid complex inversions.
3.  **Verb Forms:** Present (minä asun) and simple past (hän käveli). Minimize perfect tenses/passive.
4.  **Cases:** Nominative, Partitive, Illative, Inessive. Avoid complex cases.
5.  **Vocabulary:** Common, everyday words (max 500 most common Finnish words).
6.  **Sentence Length:** 5-10 words per sentence maximum.
""",
        "Intermediate": """
**Constraints:**
1.  **Level:** Intermediate (B1-B2).
2.  **Sentence Structure:** Mix of simple and compound sentences. Some subordinate clauses allowed.
3.  **Verb Forms:** Present, past, perfect tenses. Conditional mood (conditional). Some passive voice.
4.  **Cases:** All basic cases including Elative, Adessive, Ablative, Allative. Introduce Essive.
5.  **Vocabulary:** Broader vocabulary including abstract concepts and less common words.
6.  **Sentence Length:** 8-15 words per sentence.
""",
        "Advanced": """
**Constraints:**
1.  **Level:** Advanced (C1-C2).
2.  **Sentence Structure:** Complex sentences with multiple clauses, inversions, and varied structures.
3.  **Verb Forms:** All tenses and moods including potential, imperative. Passive voice frequently.
4.  **Cases:** All 15 cases used naturally, including rare ones (Comitative, Instructive).
5.  **Vocabulary:** Rich, nuanced vocabulary. Idioms, colloquialisms, and literary expressions.
6.  **Sentence Length:** 10-20 words per sentence. Varied for rhythm.
"""
    }
    
    constraints = level_constraints.get(level, level_constraints["Beginner"])
    
    return f"""
You are a Finnish language learning content creator. Your goal is to generate an engaging story for {level} level learners.

{constraints}
7.  **Setting:** A REAL, specific location in a Finnish city (e.g., Helsinki, Tampere, Turku, Oulu).
8.  **Length:** Exactly 8 pages.
9.  **Format:** Return ONLY a valid JSON object.

**CRITICAL INSTRUCTION: VISUAL CONSISTENCY**
- **Randomly decide** to have 1, 2, or 3 main characters for the story.
- You MUST define ALL main characters in the `characters` list.
- **IMPORTANT**: In every `image_description`, you MUST repeat the **FULL VISUAL DESCRIPTION** of ALL characters present in the scene. Do NOT just use their names.
    - BAD: "Sofia is smiling."
    - GOOD: "Sofia, a young girl with curly blonde hair wearing a blue dress, is smiling."

**JSON Structure:**
{{
  "title_fi": "Finnish Title",
  "title_en": "English Title",
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
      "image_description": "Visual description for the cover image. INCLUDE FULL CHARACTER DETAILS."
    }},
    {{
      "page_number": 2,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "Visual description... REMEMBER TO DESCRIBE CHARACTERS FULLY."
    }},
    {{
      "page_number": 3,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "Visual description..."
    }},
    {{
      "page_number": 4,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "Visual description..."
    }},
    {{
      "page_number": 5,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "Visual description..."
    }},
    {{
      "page_number": 6,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "Visual description..."
    }},
    {{
      "page_number": 7,
      "type": "story",
      "text_fi": "Finnish text...",
      "text_en": "English translation...",
      "image_description": "Visual description..."
    }},
    {{
      "page_number": 8,
      "type": "cta",
      "text_fi": "Simple question?",
      "text_en": "Simple question?",
      "image_description": "Visual description for the CTA..."
    }}
  ]
}}
"""

IMAGE_STYLE_GUIDE = """
Illustration style: Modern flat illustration with clean lines and a soft, muted color palette. The characters have a friendly, approachable appearance with rounded features and simple, expressive faces. Details are minimal but effective, focusing on essential elements like clothing textures, subtle shadows for depth, and distinct objects. The overall aesthetic is warm, inviting, and slightly whimsical, reminiscent of casual lifestyle or explainer video graphics. The style avoids harsh outlines or heavy shading, opting for a light and airy feel.

IMPORTANT: Do NOT include any text, words, letters, or numbers in the image. The image should be purely visual.
"""
