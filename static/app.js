let isGenerating = false;

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
            custom_setting: customSetting
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

                if (data.status === "Complete" || data.status.startsWith("Error")) {
                    clearInterval(interval);
                    isGenerating = false;
                    document.getElementById('generateBtn').disabled = false;
                    if (data.status === "Complete") {
                        loadStory();
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
            document.getElementById('downloadSection').classList.remove('hidden');

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
            body: JSON.stringify({ page_number: pageNumber })
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
    fetch('/api/story')
        .then(response => {
            if (response.ok) loadStory();
        });
});
