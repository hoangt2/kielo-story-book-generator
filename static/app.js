let isGenerating = false;
let currentAspectRatio = '9:16';
let currentPromptsOnly = false;

// --- Topic suggestions -------------------------------------------------------

const suggestionCache = {};
let suggestionsOpen = false;

function getSelectedLevel() {
    return document.getElementById('levelSelect').value;
}

function fetchSuggestions(level, { refresh = false, cachedOnly = false } = {}) {
    // The model costs tokens, so it is only asked when ideas are actually
    // wanted: opening the panel on a level with none yet, or "New ideas".
    // Everything else reuses what has already been generated.
    if (!refresh && suggestionCache[level]) return Promise.resolve(suggestionCache[level]);

    let url = `/api/suggestions?level=${encodeURIComponent(level)}`;
    if (refresh) url += '&refresh=1';
    if (cachedOnly) url += '&cached=1';

    return fetch(url)
        .then(response => response.json())
        .then(data => {
            // Only remember real ideas — a curated stand-in must not stick.
            if (data.source === 'ai') suggestionCache[level] = data;
            return data;
        });
}

function buildSuggestionCard(suggestion) {
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'suggestion-card';

    const topic = document.createElement('span');
    topic.className = 'suggestion-topic';
    topic.textContent = suggestion.topic;

    const meta = document.createElement('span');
    meta.className = 'suggestion-meta';
    meta.textContent = `📍 ${suggestion.setting} · 📄 ${suggestion.pages} pages`;

    const drills = document.createElement('span');
    drills.className = 'suggestion-drills';
    drills.textContent = `Drills: ${suggestion.drills}`;

    card.appendChild(topic);
    card.appendChild(meta);
    card.appendChild(drills);
    card.addEventListener('click', () => applySuggestion(suggestion));
    return card;
}

function paintSuggestions(level, data) {
    if (!suggestionsOpen || getSelectedLevel() !== level) return false;

    const list = document.getElementById('suggestionList');
    document.getElementById('suggestionHint').textContent = data.source === 'curated'
        ? `${data.hint} Built-in ideas — press 🔄 New ideas to write fresh ones.`
        : data.hint;
    list.innerHTML = '';
    data.suggestions.forEach(suggestion => {
        list.appendChild(buildSuggestionCard(suggestion));
    });
    return true;
}

function renderSuggestions(options = {}) {
    const level = getSelectedLevel();
    const hint = document.getElementById('suggestionHint');
    const list = document.getElementById('suggestionList');
    const refreshBtn = document.getElementById('suggestionRefresh');

    const willGenerate = !options.cachedOnly && (options.refresh || !suggestionCache[level]);

    if (willGenerate) {
        // Writing a batch takes a while. Fill the panel with the built-in ideas
        // meanwhile — that request never reaches the model — so the panel is
        // usable immediately instead of sitting empty.
        hint.textContent = `Writing ${level} topic ideas…`;
        list.innerHTML = '';
        refreshBtn.disabled = true;

        fetchSuggestions(level, { cachedOnly: true })
            .then(data => {
                if (!suggestionCache[level] && refreshBtn.disabled) {
                    if (paintSuggestions(level, data)) {
                        hint.textContent = `${data.hint} Built-in ideas — writing fresh ones…`;
                    }
                }
            })
            .catch(() => {});
    }

    fetchSuggestions(level, options)
        .then(data => paintSuggestions(level, data))
        .catch(err => {
            console.error(err);
            if (getSelectedLevel() === level) hint.textContent = 'Could not load topic ideas.';
        })
        .finally(() => {
            refreshBtn.disabled = false;
        });
}

function refreshSuggestions() {
    renderSuggestions({ refresh: true });
}

function toggleSuggestions() {
    const panel = document.getElementById('suggestionPanel');
    suggestionsOpen = !suggestionsOpen;
    panel.classList.toggle('hidden', !suggestionsOpen);
    if (suggestionsOpen) renderSuggestions();
}

function applySuggestion(suggestion) {
    document.getElementById('customTopic').value = suggestion.topic;
    document.getElementById('customSetting').value = suggestion.setting;
    document.getElementById('pageCount').value = suggestion.pages;

    // Custom topics override the theme dropdown, so make that explicit.
    document.getElementById('themeSelect').value = 'random';

    suggestionsOpen = false;
    document.getElementById('suggestionPanel').classList.add('hidden');

    const topicBox = document.getElementById('customTopic');
    topicBox.classList.add('topic-applied');
    setTimeout(() => topicBox.classList.remove('topic-applied'), 800);
}

function applyRandomSuggestion() {
    fetchSuggestions(getSelectedLevel(), { cachedOnly: true }).then(data => {
        const pool = data.suggestions;
        if (!pool.length) return;
        applySuggestion(pool[Math.floor(Math.random() * pool.length)]);
    });
}

function onLevelChange() {
    // No generation on a level switch — that is not a request for new ideas.
    if (suggestionsOpen) renderSuggestions({ cachedOnly: true });
}

function startGeneration() {
    if (isGenerating) return;

    const btn = document.getElementById('generateBtn');
    const status = document.getElementById('status');
    const progress = document.getElementById('progressContainer');
    const storyContainer = document.getElementById('storyContainer');
    const downloadSection = document.getElementById('downloadSection');
    const levelSelect = document.getElementById('levelSelect');
    const themeSelect = document.getElementById('themeSelect');
    const selectedLevel = levelSelect.value;
    const selectedTheme = themeSelect.value;

    const customTopic = document.getElementById('customTopic').value;
    const customSetting = document.getElementById('customSetting').value;
    const pageCount = document.getElementById('pageCount').value;
    const aspectRatio = document.getElementById('aspectRatio').value;
    const promptsOnly = document.getElementById('promptsOnly').checked;
    currentAspectRatio = aspectRatio;
    currentPromptsOnly = promptsOnly;

    btn.disabled = true;
    isGenerating = true;
    status.classList.remove('hidden');
    progress.classList.remove('hidden');
    storyContainer.classList.add('hidden');
    downloadSection.classList.add('hidden');
    storyContainer.innerHTML = '';

    fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            level: selectedLevel,
            theme_category: selectedTheme,
            custom_topic: customTopic,
            page_count: pageCount,
            custom_setting: customSetting,
            aspect_ratio: aspectRatio,
            prompts_only: promptsOnly
        })
    })
        .then(response => response.json())
        .then(data => {
            pollStatus();
        })
        .catch(err => {
            console.error(err);
            btn.disabled = false;
            isGenerating = false;
        });
}

function pollStatus() {
    const statusText = document.getElementById('status');
    const logMessage = document.getElementById('logMessage');
    const progressFill = document.querySelector('.progress-fill');

    const interval = setInterval(() => {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                statusText.innerText = data.status;
                logMessage.innerText = data.status;

                // Fake progress based on status keywords
                let percent = 10;
                if (data.status.includes("Processing Page")) {
                    // Extract page number if possible, or just increment
                    percent = 30 + (Math.random() * 40);
                } else if (data.status.includes("Compiling")) {
                    percent = 90;
                } else if (data.status === "Complete") {
                    percent = 100;
                }
                progressFill.style.width = percent + '%';

                if (data.status === "Complete" || data.status.startsWith("Error") || data.status.includes("Prompts export complete")) {
                    clearInterval(interval);
                    isGenerating = false;
                    document.getElementById('generateBtn').disabled = false;
                    if (data.status === "Complete" || data.status.includes("Prompts export complete")) {
                        if (currentPromptsOnly) {
                            loadPromptsOnlyView();
                        } else {
                            loadStory();
                        }
                    }
                }
            });
    }, 1000);
}

function loadStory() {
    fetch('/api/story')
        .then(response => response.json())
        .then(story => {
            const container = document.getElementById('storyContainer');
            container.classList.remove('hidden');
            
            const downloadSection = document.getElementById('downloadSection');
            downloadSection.classList.remove('hidden');
            document.getElementById('pdfDownload').classList.remove('hidden');
            document.getElementById('promptsDownload').classList.add('hidden');

            story.pages.forEach(page => {
                const card = document.createElement('div');
                card.className = 'story-card';

                // Use the story card image (composited)
                const imgPath = `/output/cards/story_card_${page.page_number}.png`;

                card.innerHTML = `
                    <img src="${imgPath}" alt="Page ${page.page_number}">
                    <div class="story-card-content">
                        <p class="fi-text">${page.text_fi}</p>
                        <p class="en-text">${page.text_en}</p>
                    </div>
                    <button class="regenerate-btn" onclick="regenerateImage(${page.page_number}, this)" title="Regenerate Illustration">🔄</button>
                `;
                container.appendChild(card);
            });
        });
}

function regenerateImage(pageNumber, btnElement) {
    if (confirm("Are you sure you want to regenerate this image? It will replace the current one.")) {
        const originalText = btnElement.innerText;
        btnElement.innerText = "Regenerating...";
        btnElement.disabled = true;

        // Find the image element for this page
        const card = btnElement.closest('.story-card');
        const img = card.querySelector('img');

        fetch('/api/regenerate_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ page_number: pageNumber, aspect_ratio: currentAspectRatio })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                    btnElement.innerText = originalText;
                    btnElement.disabled = false;
                } else {
                    // Success! Force reload image with timestamp
                    const timestamp = new Date().getTime();
                    // We need to reload the image source. 
                    // The filename is likely the same, so cache busting is needed.
                    // Construct path safely
                    const currentSrc = img.src.split('?')[0];
                    img.src = `${currentSrc}?t=${timestamp}`;

                    btnElement.innerText = "✨ Regenerated!";
                    setTimeout(() => {
                        btnElement.innerText = originalText;
                        btnElement.disabled = false;
                    }, 2000);
                }
            })
            .catch(err => {
                console.error(err);
                alert('Failed to connect to server.');
                btnElement.innerText = originalText;
                btnElement.disabled = false;
            });
    }
}

function loadPromptsOnlyView() {
    fetch('/api/story')
        .then(response => response.json())
        .then(story => {
            const container = document.getElementById('storyContainer');
            container.classList.remove('hidden');
            container.innerHTML = '';

            // --- Character Reference Prompts ---
            const characters = story.characters || [];
            if (characters.length > 0) {
                const charHeader = document.createElement('div');
                charHeader.className = 'section-header';
                charHeader.innerHTML = `<h2>🎨 Character Reference Sheets</h2>`;
                container.appendChild(charHeader);

                characters.forEach((char, i) => {
                    const card = document.createElement('div');
                    card.className = 'story-card prompts-only-card character-card';

                    const charPrompt = `Character sheet showing the following character: ${char.description}. Multiple views if possible, white background.`;

                    card.innerHTML = `
                        <div class="story-card-content">
                            <div class="page-number">Character ${i + 1}</div>
                            <p class="fi-text">${char.name}</p>
                            <p class="en-text">${char.description}</p>
                            <details class="prompt-details">
                                <summary>📝 Character Prompt</summary>
                                <p class="prompt-text">${charPrompt}</p>
                            </details>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }

            // --- Scene Prompts ---
            const sceneHeader = document.createElement('div');
            sceneHeader.className = 'section-header';
            sceneHeader.innerHTML = `<h2>🖼️ Scene Prompts</h2>`;
            container.appendChild(sceneHeader);

            story.pages.forEach(page => {
                const card = document.createElement('div');
                card.className = 'story-card prompts-only-card';

                card.innerHTML = `
                    <div class="story-card-content">
                        <div class="page-number">Page ${page.page_number}</div>
                        <p class="fi-text">${page.text_fi}</p>
                        <p class="en-text">${page.text_en}</p>
                        <details class="prompt-details">
                            <summary>📝 Image Prompt</summary>
                            <p class="prompt-text">${page.image_description}</p>
                        </details>
                    </div>
                `;
                container.appendChild(card);
            });

            // Show prompts download, hide PDF download
            const downloadSection = document.getElementById('downloadSection');
            downloadSection.classList.remove('hidden');
            document.getElementById('pdfDownload').classList.add('hidden');
            document.getElementById('promptsDownload').classList.remove('hidden');
        });
}

function archiveStory() {
    fetch('/api/archive', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error archiving story: ' + data.error);
            } else {
                alert('Story saved to archive!');
            }
        })
        .catch(err => {
            console.error(err);
            alert('Failed to connect to server.');
        });
}

// Load existing story on startup if available
window.addEventListener('DOMContentLoaded', () => {
    document.getElementById('levelSelect').addEventListener('change', onLevelChange);
    onLevelChange();

    fetch('/api/story')
        .then(response => {
            if (response.ok) loadStory();
        });
});
