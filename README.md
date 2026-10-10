# Story Book Generator (Finnish & Swedish)

An AI-powered tool that generates illustrated language learning stories in Finnish or Swedish, with adjustable difficulty levels.

## Features

- 🎨 **AI-Generated Stories**: Creates unique stories set in real Finnish cities
- 📚 **Multiple Difficulty Levels**: Beginner (A1-A2), Intermediate (B1-B2), Advanced (C1-C2)
- ✍️ **Custom Topics**: Create stories about any topic you choose
- 💡 **AI Topic Suggestions**: Topic ideas written for the chosen CEFR level, generated only when
  you ask for them and cached afterwards. Each fills in the topic, setting and a suitable page
  count, and says which grammar it drills. Ideas never repeat, skip topics you have already made
  into books, and fall back to a built-in list if the API is unavailable (see `topic_suggestions.py`)
- 📄 **Adjustable Length**: Control story length (3-20 pages)
- 👥 **Multi-Character Support**: Randomly generates 1-3 main characters per story
- 🖼️ **Illustrated Pages**: Modern flat illustration style with character consistency
- 🎬 **Comic-Style Camera Work**: Every page gets its own framing — establishing wides, close-ups,
  worm's-eye angles, first-person POV, top-down detail shots — planned in a comic rhythm so no two
  consecutive pages look alike (see `cinematography.py`)
- 📱 **Story Cards**: Bilingual (Finnish/English) cards optimized for mobile viewing
- 📄 **PDF Export**: Automatically compiles stories into printable PDF books
- 🌐 **Web Interface**: Beautiful dark-mode UI with real-time progress tracking

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd kielo-story-book-generator
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Google API key:
Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

### Web Interface (Recommended)

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser to `http://localhost:5000`

3. Select your desired difficulty level

4. Click "Generate New Story"

5. View the generated story and download the PDF

### Command Line

Generate a story directly from the command line:

```bash
# Default (Beginner level)
python story_generator.py

# Specify difficulty level and topic
python story_generator.py --level Intermediate --topic "A summer day in Turku"

# Custom output directory and page count
python story_generator.py --output_dir my_stories --level Advanced --pages 12
```

### Clean Up

Remove generated files:
```bash
python cleanup.py
```

## Output Structure

```
output/
├── images/           # Generated page images
│   ├── character_model_*.png
│   └── page_*.png
├── cards/            # Composited story cards (image + text)
│   └── story_card_*.png
├── data/             # Story metadata
│   └── story.json
└── story.pdf         # Final compiled PDF
```

## Languages

Pick **Finnish** or **Swedish** in the web UI (or pass `--language fi|sv` on the command line). Finnish is the default.

- Stories, CEFR constraints, themes, topic ideas and the grammar check follow the chosen language (`languages.py`, `prompts.py`, `topic_suggestions.py`, `grammar_checker.py`).
- Story JSON stores text as `text_fi` / `text_sv` (and `title_fi` / `title_sv`), with a top-level `language` field. Older Finnish archives without that field still load as Finnish.

## Language Levels

### Beginner (A1-A2)
- Simple SVO sentence structure
- Present and simple past tense
- Basic cases (Nominative, Partitive, Illative, Inessive)
- Common everyday vocabulary
- 5-10 words per sentence

### Intermediate (B1-B2)
- Compound sentences with subordinate clauses
- Perfect tenses and conditional mood
- Extended case usage (Elative, Adessive, Ablative, Allative, Essive)
- Broader vocabulary including abstract concepts
- 8-15 words per sentence

### Advanced (C1-C2)
- Complex sentences with multiple clauses
- All tenses and moods (potential, imperative)
- All 15 Finnish cases
- Rich vocabulary with idioms and literary expressions
- 10-20 words per sentence

## Technical Stack

- **AI Models**: Google Gemini 2.0 Flash (text), Gemini 2.5 Flash Image (illustrations)
- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Image Processing**: Pillow (PIL)

## Project Structure

```
kielo-story-book-generator/
├── app.py                 # Flask web application
├── story_generator.py     # Core story generation logic
├── image_composer.py      # Story card composition
├── pdf_generator.py       # PDF compilation
├── prompts.py             # AI prompts for different levels
├── cleanup.py             # Utility to clean output
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   └── index.html
└── static/                # CSS and JavaScript
    ├── style.css
    └── app.js
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.