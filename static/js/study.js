// Study session functionality - Simple tracking (no spaced repetition)

let cardStartTime = Date.now();
let sessionInProgress = false;
let hasUnsavedProgress = false;

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

// Handle option selection with trippy button using event delegation
document.addEventListener('DOMContentLoaded', function() {
    // Set session as in progress
    sessionInProgress = true;
    hasUnsavedProgress = true;
    
    // Use event delegation on the card-container for all option clicks
    const cardContainer = document.getElementById('card-container');
    
    if (cardContainer) {
        cardContainer.addEventListener('click', function(e) {
            // Check if click is on option button
            if (e.target.closest('.option-btn')) {
                const optionBtn = e.target.closest('.option-btn');
                const wrapper = optionBtn.closest('.option-wrapper');
                const card = optionBtn.closest('.flashcard');
                
                // Don't process if already disabled
                if (optionBtn.disabled) {
                    console.log('Option button already disabled');
                    return;
                }
                
                const cardId = parseInt(card.dataset.cardId);
                const correctAnswer = parseInt(card.dataset.correctAnswer);
                const index = parseInt(optionBtn.dataset.index);
                
                console.log(`Option clicked: index=${index}, cardId=${cardId}, correctAnswer=${correctAnswer}`);
                selectAnswer(wrapper, cardId, correctAnswer, index, false);
            }
            
            // Check if click is on trippy button
            else if (e.target.closest('.trippy-btn')) {
                e.stopPropagation();
                const trippyBtn = e.target.closest('.trippy-btn');
                const wrapper = trippyBtn.closest('.option-wrapper');
                const card = trippyBtn.closest('.flashcard');
                
                // Don't process if already disabled
                if (trippyBtn.disabled) {
                    console.log('Trippy button already disabled');
                    return;
                }
                
                const optionBtn = wrapper.querySelector('.option-btn');
                const cardId = parseInt(card.dataset.cardId);
                const correctAnswer = parseInt(card.dataset.correctAnswer);
                const index = parseInt(optionBtn.dataset.index);
                
                console.log(`Trippy button clicked: index=${index}, cardId=${cardId}`);
                selectAnswer(wrapper, cardId, correctAnswer, index, true);
            }
        });
    }
});

function selectAnswer(wrapper, cardId, correctAnswer, selectedIndex, isTrippy) {
    const container = wrapper.parentElement;
    const allWrappers = container.querySelectorAll('.option-wrapper');
    
    // Disable all options
    allWrappers.forEach(w => {
        const btn = w.querySelector('.option-btn');
        const trippy = w.querySelector('.trippy-btn');
        btn.disabled = true;
        trippy.disabled = true;
        trippy.style.display = 'none';
        
        const idx = parseInt(btn.dataset.index);
        
        if (idx === correctAnswer) {
            btn.classList.add('correct');
        } else if (idx === selectedIndex) {
            btn.classList.add('incorrect');
        }
    });
    
    // Determine result
    let result;
    if (isTrippy) {
        result = 'trippy';
        wrapper.querySelector('.option-btn').classList.add('trippy-marked');
    } else if (selectedIndex === correctAnswer) {
        result = 'correct';
    } else {
        result = 'incorrect';
    }
    
    // Show explanation
    showAnswer(cardId, result);
}

function showAnswer(cardId, result) {
    const explanation = document.getElementById(`explanation-${cardId}`);
    explanation.style.display = 'block';
    
    // Record the result
    recordReview(cardId, result);
    
    // Scroll to explanation
    setTimeout(() => {
        explanation.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

function showAnswerOnly(cardId) {
    const explanation = document.getElementById(`explanation-${cardId}`);
    explanation.style.display = 'block';
    
    setTimeout(() => {
        explanation.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

function recordReview(cardId, result) {
    const duration = Math.floor((Date.now() - cardStartTime) / 1000);
    
    fetch('/api/review', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            card_id: cardId,
            result: result,
            duration: duration,
            session_id: sessionId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            cardsReviewed++;
            console.log(`Card reviewed: ${result}. Counts - Correct: ${data.correct_count}, Incorrect: ${data.incorrect_count}, Trippy: ${data.trippy_count}`);
        } else {
            console.error('Review failed:', data.error);
        }
    })
    .catch(error => {
        console.error('Error recording review:', error);
        alert('Failed to record your answer. Please check your connection and try again.');
    });
}

function nextCardAction() {
    nextCard();
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
    document.getElementById('card-container').style.display = 'none';
    document.querySelector('.study-header').style.display = 'none';
    document.getElementById('session-complete').style.display = 'block';
    
    // Update session stats
    document.getElementById('session-stats').innerHTML = `
        <p>Cards reviewed: ${cardsReviewed} / ${totalCards}</p>
    `;
    
    // End session on server
    fetch(`/api/session/${sessionId}/end`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    });
}

// End session button
document.getElementById('end-session').addEventListener('click', function() {
    if (confirm('Are you sure you want to end this session?')) {
        endStudySession();
    }
});

function deleteCard(cardId, event) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this card? This action cannot be undone.')) {
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
            // Find current card and remove it
            const cards = document.querySelectorAll('.flashcard');
            const currentCard = cards[currentCardIndex];
            
            // Adjust total cards
            totalCards--;
            document.getElementById('total-cards').textContent = totalCards;
            
            if (totalCards === 0) {
                // No more cards
                sessionInProgress = false;
                hasUnsavedProgress = false;
                alert('No more cards in this session!');
                window.location.href = '/';
            } else {
                // Move to next card without incrementing index
                currentCard.remove();
                const remainingCards = document.querySelectorAll('.flashcard');
                
                if (currentCardIndex >= remainingCards.length) {
                    currentCardIndex = remainingCards.length - 1;
                }
                
                remainingCards[currentCardIndex].style.display = 'block';
                document.getElementById('current-card').textContent = currentCardIndex + 1;
                cardStartTime = Date.now();
            }
        } else {
            alert('Failed to delete card: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to delete card. Please try again.');
    });
}

function markAsCleared(cardId, event) {
    event.preventDefault();
    event.stopPropagation();
    
    if (!confirm('Mark this card as mastered? It will be removed from this review list.')) {
        return;
    }
    
    fetch(`/api/card/${cardId}/clear_status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            const card = document.querySelector(`[data-card-id="${cardId}"]`);
            const explanation = card.querySelector('.explanation-section');
            
            // Add success message
            const successMsg = document.createElement('div');
            successMsg.style.cssText = 'background: var(--success); color: white; padding: 0.75rem; border-radius: 8px; margin-top: 1rem; text-align: center;';
            successMsg.innerHTML = '✓ Card marked as mastered! Moving to next...';
            explanation.insertBefore(successMsg, explanation.querySelector('.action-buttons'));
            
            // Auto-advance to next card after 1.5 seconds
            setTimeout(() => {
                nextCard();
            }, 1500);
        } else {
            alert('Failed to clear card status: ' + (data.message || data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to clear card status. Please try again.');
    });
}
