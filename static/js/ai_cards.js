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
    const topicCheckboxes = document.getElementById('aiTopicCheckboxes');
    const selectedModule = moduleSelect.value;
    
    topicCheckboxes.innerHTML = '';
    
    if (!selectedModule) {
        topicCheckboxes.innerHTML = '<small style="color: rgba(255,255,255,0.5);">Select a ' + 
            (generatorType === 'payal' ? 'subject' : 'module') + ' first</small>';
        return;
    }
    
    // Fetch topics for the selected module
    const apiEndpoint = generatorType === 'payal'
        ? `/api/ai/modules-payal/${encodeURIComponent(selectedModule)}/topics`
        : `/api/ai/modules/${encodeURIComponent(selectedModule)}/topics`;
    
    fetch(apiEndpoint)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.topics && data.topics.length > 0) {
                data.topics.forEach((topic, index) => {
                    const label = document.createElement('label');
                    label.style.display = 'block';
                    label.style.marginBottom = '8px';
                    label.style.cursor = 'pointer';
                    label.style.padding = '5px';
                    label.style.borderRadius = '4px';
                    label.style.transition = 'background 0.2s';
                    label.onmouseover = () => label.style.background = 'rgba(255,255,255,0.1)';
                    label.onmouseout = () => label.style.background = 'transparent';
                    
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.name = 'topic_checkbox';
                    checkbox.value = topic;
                    checkbox.id = `topic_${index}`;
                    checkbox.style.marginRight = '8px';
                    
                    const text = document.createTextNode(topic);
                    
                    label.appendChild(checkbox);
                    label.appendChild(text);
                    topicCheckboxes.appendChild(label);
                });
            } else {
                topicCheckboxes.innerHTML = '<small style="color: rgba(255,255,255,0.5);">No topics available</small>';
            }
        })
        .catch(error => {
            console.error('Error loading topics:', error);
            topicCheckboxes.innerHTML = '<small style="color: #ff6b6b;">Error loading topics</small>';
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
            
            // Get checked topics
            const checkedTopics = Array.from(document.querySelectorAll('#aiTopicCheckboxes input[type="checkbox"]:checked'))
                .map(cb => cb.value);
            
            const deckId = parseInt(formData.get('deck_id'));
            
            const data = {
                deck_id: deckId,
                module: formData.get('module'),
                topics: checkedTopics.length > 0 ? checkedTopics : null,
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
