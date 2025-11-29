// AI Flashcard Generator JavaScript

let aiGeneratorModal = null;

function openAIGeneratorModal() {
    aiGeneratorModal = document.getElementById('ai-generator-modal');
    if (aiGeneratorModal) {
        aiGeneratorModal.style.display = 'block';
        loadModules();
    }
}

function closeAIGeneratorModal() {
    if (aiGeneratorModal) {
        aiGeneratorModal.style.display = 'none';
        resetAIGeneratorForm();
    }
}

function resetAIGeneratorForm() {
    document.getElementById('ai-module-select').value = '';
    const topicSelect = document.getElementById('ai-topic-select');
    if (topicSelect) {
        topicSelect.innerHTML = '<option value="">All topics</option>';
        topicSelect.disabled = true;
    }
    document.getElementById('ai-card-count').value = '50';
    document.querySelectorAll('input[name="ai-difficulty"]').forEach(radio => {
        radio.checked = radio.value === 'medium';
    });
    document.getElementById('ai-progress').style.display = 'none';
}

function loadModules() {
    fetch('/api/ai/modules')
        .then(response => response.json())
        .then(data => {
            const moduleSelect = document.getElementById('ai-module-select');
            moduleSelect.innerHTML = '<option value="">Select a module...</option>';
            
            if (data.success && data.modules) {
                data.modules.forEach(module => {
                    const option = document.createElement('option');
                    option.value = module.name;
                    option.textContent = module.name;
                    option.dataset.topics = JSON.stringify(module.topics);
                    moduleSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading modules:', error);
            alert('Failed to load modules. Please try again.');
        });
}

function onModuleChange() {
    const moduleSelect = document.getElementById('ai-module-select');
    const topicSelect = document.getElementById('ai-topic-select');
    const selectedOption = moduleSelect.options[moduleSelect.selectedIndex];
    
    topicSelect.innerHTML = '<option value="">All topics (general overview)</option>';
    topicSelect.disabled = true;
    
    if (selectedOption && selectedOption.dataset.topics) {
        const topics = JSON.parse(selectedOption.dataset.topics);
        topics.forEach(topic => {
            const option = document.createElement('option');
            option.value = topic;
            option.textContent = topic;
            topicSelect.appendChild(option);
        });
        if (topics.length > 0) {
            topicSelect.disabled = false;
        }
    }
}

function generateAICards() {
    const modal = document.getElementById('ai-generator-modal');
    const deckId = modal.dataset.deckId;
    const moduleName = document.getElementById('ai-module-select').value;
    const topic = document.getElementById('ai-topic-select').value;
    const count = parseInt(document.getElementById('ai-card-count').value);
    const difficulty = document.querySelector('input[name="ai-difficulty"]:checked').value;
    
    if (!moduleName) {
        alert('Please select a module');
        return;
    }
    
    if (count < 1 || count > 100) {
        alert('Please enter a number between 1 and 100');
        return;
    }
    
    // Show progress
    const progressDiv = document.getElementById('ai-progress');
    const progressText = document.getElementById('ai-progress-text');
    progressDiv.style.display = 'block';
    progressText.textContent = `Generating ${count} flashcards using AI... This may take 30-60 seconds.`;
    
    // Disable generate button
    const generateBtn = document.getElementById('ai-generate-btn');
    generateBtn.disabled = true;
    
    // Make API call
    fetch('/api/ai/generate-cards', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            deck_id: deckId,
            module: moduleName,
            topic: topic || null,
            count: count,
            difficulty: difficulty
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            progressText.textContent = `✅ Successfully generated ${data.cards_generated} flashcards!`;
            setTimeout(() => {
                closeAIGeneratorModal();
                location.reload(); // Reload to show new cards
            }, 2000);
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        progressText.textContent = `❌ Error: ${error.message}`;
        generateBtn.disabled = false;
    });
}

// Initialize module decks
function initializeModuleDecks() {
    if (!confirm('This will create 8 parent module decks with subtopic child decks. Continue?')) {
        return;
    }
    
    const btn = document.getElementById('init-decks-btn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Creating decks...';
    }
    
    fetch('/api/ai/initialize-decks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`✅ Created ${data.decks_created} decks!\n\nParent Decks: ${data.parent_decks}\nChild Decks: ${data.child_decks}`);
            location.reload();
        } else {
            throw new Error(data.error || 'Failed to initialize decks');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`❌ Error: ${error.message}`);
        if (btn) {
            btn.disabled = false;
            btn.textContent = '🚀 Initialize Module Decks';
        }
    });
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target === aiGeneratorModal) {
        closeAIGeneratorModal();
    }
}
