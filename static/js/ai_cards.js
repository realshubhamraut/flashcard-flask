// AI Card Generation
async function openAIModal(generatorType = 'shubham') {
    const modal = document.getElementById('aiModal');
    modal.dataset.generatorType = generatorType; // Store generator type
    
    // Update modal title and styling based on generator type
    const modalTitle = modal.querySelector('h2');
    if (generatorType === 'payal') {
        modalTitle.textContent = '🎓 Generate AI Cards for Payal';
        modalTitle.style.color = '#2563eb';
    } else {
        modalTitle.textContent = '💻 Generate AI Cards for Shubham';
        modalTitle.style.color = '#16a34a';
    }
    
    modal.style.display = 'flex';
    modal.classList.add('active');
    await loadModules(generatorType);
}

function closeAIModal() {
    const modal = document.getElementById('aiModal');
    modal.style.display = 'none';
    modal.classList.remove('active');
}

async function loadModules(generatorType = 'shubham') {
    try {
        const apiEndpoint = generatorType === 'payal' 
            ? '/api/ai/modules-payal' 
            : '/api/ai/modules';
        
        const response = await fetch(apiEndpoint);
        const data = await response.json();
        
        if (data.success) {
            const moduleSelect = document.getElementById('aiModule');
            moduleSelect.innerHTML = '<option value="">-- Select ' + 
                (generatorType === 'payal' ? 'Subject' : 'Module') + ' --</option>';
            const topicSelect = document.getElementById('aiTopic');
            if (topicSelect) {
                topicSelect.innerHTML = '<option value="">All topics (general overview)</option>';
                topicSelect.disabled = true;
            }
            
            data.modules.forEach(module => {
                const option = document.createElement('option');
                option.value = typeof module === 'string' ? module : module.name;
                option.textContent = typeof module === 'string' ? module : module.name;
                if (typeof module === 'object' && module.topics) {
                    option.dataset.topics = JSON.stringify(module.topics);
                }
                moduleSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading modules:', error);
        alert('Failed to load modules');
    }
}

function onModuleChange() {
    const modal = document.getElementById('aiModal');
    const generatorType = modal.dataset.generatorType || 'shubham';
    const moduleSelect = document.getElementById('aiModule');
    const topicSelect = document.getElementById('aiTopic');
    const selectedModule = moduleSelect.value;
    
    if (!topicSelect) {
        return;
    }
    
    topicSelect.innerHTML = '<option value="">All topics (general overview)</option>';
    topicSelect.disabled = true;
    
    if (!selectedModule) {
        return;
    }
    
    // Fetch topics for the selected module
    const apiEndpoint = generatorType === 'payal'
        ? `/api/ai/modules-payal/${encodeURIComponent(selectedModule)}/topics`
        : `/api/ai/modules/${encodeURIComponent(selectedModule)}/topics`;
    
    fetch(apiEndpoint)
        .then(response => response.json())
        .then(data => {
            if (data.success && Array.isArray(data.topics) && data.topics.length > 0) {
                data.topics.forEach(topic => {
                    const option = document.createElement('option');
                    option.value = topic;
                    option.textContent = topic;
                    topicSelect.appendChild(option);
                });
                topicSelect.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error loading topics:', error);
            topicSelect.innerHTML = '<option value="">Unable to load topics</option>';
            topicSelect.disabled = true;
        });
}

document.addEventListener('DOMContentLoaded', function() {
    const aiForm = document.getElementById('aiForm');
    if (aiForm) {
        aiForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const modal = document.getElementById('aiModal');
            const generatorType = modal.dataset.generatorType || 'shubham';
            const formData = new FormData(aiForm);
            
            const deckId = parseInt(formData.get('deck_id'));
            const selectedTopic = formData.get('topic');
            
            const data = {
                deck_id: deckId,
                module: formData.get('module'),
                topic: selectedTopic && selectedTopic.length ? selectedTopic : null,
                count: parseInt(formData.get('count')),
                difficulty: formData.get('difficulty')
            };
            
            console.log('Sending data:', data);
            console.log('Generator type:', generatorType);
            
            document.getElementById('aiProgress').style.display = 'block';
            
            try {
                // Determine API endpoint based on generator type
                const apiEndpoint = generatorType === 'payal'
                    ? '/api/ai/generate-cards-payal'
                    : '/api/ai/generate-cards-shubham';
                
                const response = await fetch(apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                console.log('Response:', result);
                
                if (result.success) {
                    alert(`Successfully generated ${result.cards_generated || result.cards_added} cards!`);
                    closeAIModal();
                    location.reload();
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate cards. Check console.');
            } finally {
                document.getElementById('aiProgress').style.display = 'none';
            }
        });
    }
});

window.onclick = function(event) {
    const modal = document.getElementById('aiModal');
    if (event.target === modal) {
        closeAIModal();
    }
}
