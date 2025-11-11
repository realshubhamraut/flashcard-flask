// Study session functionality

let cardStartTime = Date.now();

function toggleHint(button) {
    const hintContent = button.nextElementSibling;
    if (hintContent.style.display === 'none') {
        hintContent.style.display = 'block';
        button.textContent = '💡 Hide Hint';
    } else {
        hintContent.style.display = 'none';
        button.textContent = '💡 Show Hint';
    }
}

function selectAnswer(button, cardId, correctAnswer) {
    const options = button.parentElement.querySelectorAll('.option-btn');
    const selectedIndex = parseInt(button.dataset.index);
    
    // Disable all options
    options.forEach(opt => {
        opt.disabled = true;
        const index = parseInt(opt.dataset.index);
        
        if (index === correctAnswer) {
            opt.classList.add('correct');
        } else if (index === selectedIndex && index !== correctAnswer) {
            opt.classList.add('incorrect');
        }
    });
    
    // Show result and explanation immediately
    const isCorrect = selectedIndex === correctAnswer;
    showAnswer(cardId, isCorrect);
}

function showAnswer(cardId, isCorrect = null) {
    const explanation = document.getElementById(`explanation-${cardId}`);
    
    // Just show explanation without the result message
    explanation.style.display = 'block';
    
    // Scroll to explanation smoothly
    setTimeout(() => {
        explanation.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

function rateCard(cardId, rating) {
    const duration = Math.floor((Date.now() - cardStartTime) / 1000);
    
    // Send review to server
    fetch('/api/review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            card_id: cardId,
            rating: rating,
            duration: duration,
            session_id: sessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cardsReviewed++;
            nextCard();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to record review. Please try again.');
    });
}

function nextCard() {
    const cards = document.querySelectorAll('.flashcard');
    const currentCard = cards[currentCardIndex];
    
    currentCardIndex++;
    
    if (currentCardIndex < totalCards) {
        // Hide current card
        currentCard.style.display = 'none';
        
        // Show next card
        const nextCard = cards[currentCardIndex];
        nextCard.style.display = 'block';
        
        // Update progress
        document.getElementById('current-card').textContent = currentCardIndex + 1;
        
        // Reset timer
        cardStartTime = Date.now();
    } else {
        // Session complete
        endStudySession();
    }
}

function endStudySession() {
    // Hide card container
    document.getElementById('card-container').style.display = 'none';
    
    // Show completion screen
    const completeScreen = document.getElementById('session-complete');
    completeScreen.style.display = 'block';
    document.getElementById('cards-reviewed').textContent = cardsReviewed;
    
    // End session on server
    fetch(`/api/session/${sessionId}/end`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    });
}

// End session button
const endSessionBtn = document.getElementById('end-session');
if (endSessionBtn) {
    endSessionBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to end this study session?')) {
            endStudySession();
        }
    });
}

// Delete card function
let currentEditingCardId = null;

function deleteCard(cardId, event) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this card? This cannot be undone.')) {
        return;
    }
    
    fetch(`/api/card/${cardId}/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const cardElement = document.querySelector(`[data-card-id="${cardId}"]`);
            cardElement.remove();
            
            totalCards--;
            document.getElementById('total-cards').textContent = totalCards;
            
            if (totalCards === 0) {
                endStudySession();
            } else if (currentCardIndex >= totalCards) {
                currentCardIndex = totalCards - 1;
                const cards = document.querySelectorAll('.flashcard');
                if (cards[currentCardIndex]) {
                    cards[currentCardIndex].style.display = 'block';
                }
            } else {
                const cards = document.querySelectorAll('.flashcard');
                if (cards[currentCardIndex]) {
                    cards[currentCardIndex].style.display = 'block';
                }
            }
            
            alert('Card deleted successfully');
        } else {
            alert('Failed to delete card: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to delete card. Please try again.');
    });
}

function openScheduleEditor(cardId) {
    currentEditingCardId = cardId;
    
    fetch(`/api/card/${cardId}/progress`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const progress = data.progress;
            
            document.getElementById('card-state').value = progress.state || 'new';
            document.getElementById('interval-days').value = progress.interval || 0;
            document.getElementById('ease-factor').value = progress.ease_factor || 2.5;
            document.getElementById('repetitions').value = progress.repetitions || 0;
            
            const dueDate = progress.due_date ? new Date(progress.due_date) : new Date();
            const formatted = dueDate.toISOString().slice(0, 16);
            document.getElementById('next-review-date').value = formatted;
            
            document.getElementById('schedule-modal').style.display = 'flex';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to load card progress');
    });
}

function closeScheduleEditor() {
    document.getElementById('schedule-modal').style.display = 'none';
    currentEditingCardId = null;
}

function saveSchedule() {
    if (!currentEditingCardId) return;
    
    const scheduleData = {
        state: document.getElementById('card-state').value,
        due_date: document.getElementById('next-review-date').value,
        interval: parseInt(document.getElementById('interval-days').value),
        ease_factor: parseFloat(document.getElementById('ease-factor').value),
        repetitions: parseInt(document.getElementById('repetitions').value)
    };
    
    fetch(`/api/card/${currentEditingCardId}/progress`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(scheduleData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Schedule updated successfully!');
            closeScheduleEditor();
        } else {
            alert('Failed to update schedule: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save schedule. Please try again.');
    });
}
