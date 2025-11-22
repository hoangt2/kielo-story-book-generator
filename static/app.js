let isGenerating = false;

function startGeneration() {
    if (isGenerating) return;

    const btn = document.getElementById('generateBtn');
    const status = document.getElementById('status');
    const progress = document.getElementById('progressContainer');
    const storyContainer = document.getElementById('storyContainer');
    const downloadSection = document.getElementById('downloadSection');
    const levelSelect = document.getElementById('levelSelect');
    const selectedLevel = levelSelect.value;

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
        body: JSON.stringify({ level: selectedLevel })
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
                `;
                container.appendChild(card);
            });
        });
}

// Load existing story on startup if available
window.addEventListener('DOMContentLoaded', () => {
    fetch('/api/story')
        .then(response => {
            if (response.ok) loadStory();
        });
});
