from datetime import datetime, timedelta
from sqlalchemy import func
from models import CardProgress, Review, db


class SpacedRepetition:
    """
    Implementation of SM-2 spaced repetition algorithm (similar to Anki)
    
    The algorithm adjusts review intervals based on how well you remember each card.
    Ratings: Again (1), Hard (2), Good (3), Easy (4)
    """
    
    # Configuration constants
    GRADUATING_INTERVAL = 1  # Days to wait after first successful review
    EASY_INTERVAL = 4  # Days to wait for easy cards
    STARTING_EASE = 2.5  # Initial ease factor
    MINIMUM_EASE = 1.3  # Minimum ease factor
    EASY_BONUS = 1.3  # Multiplier for easy cards
    HARD_INTERVAL = 1.2  # Multiplier for hard cards
    
    # Rating values
    RATING_AGAIN = 'again'
    RATING_HARD = 'hard'
    RATING_GOOD = 'good'
    RATING_EASY = 'easy'
    
    @staticmethod
    def schedule_card(card_progress, rating):
        """
        Update card scheduling based on user rating
        
        Args:
            card_progress: CardProgress object
            rating: String - 'again', 'hard', 'good', or 'easy'
        
        Returns:
            Updated CardProgress object
        """
        now = datetime.utcnow()
        
        if rating == SpacedRepetition.RATING_AGAIN:
            # Reset the card - start over
            card_progress.state = 'learning'
            card_progress.interval = 0
            card_progress.repetitions = 0
            card_progress.lapses += 1
            card_progress.due_date = now + timedelta(minutes=10)
            # Reduce ease factor
            card_progress.ease_factor = max(
                SpacedRepetition.MINIMUM_EASE,
                card_progress.ease_factor - 0.2
            )
            
        elif rating == SpacedRepetition.RATING_HARD:
            if card_progress.state == 'new':
                card_progress.state = 'learning'
                card_progress.interval = 0
                card_progress.due_date = now + timedelta(hours=1)
            else:
                # Reduce ease factor slightly
                card_progress.ease_factor = max(
                    SpacedRepetition.MINIMUM_EASE,
                    card_progress.ease_factor - 0.15
                )
                # Increase interval by hard multiplier
                new_interval = max(1, int(card_progress.interval * SpacedRepetition.HARD_INTERVAL))
                card_progress.interval = new_interval
                card_progress.due_date = now + timedelta(days=new_interval)
                card_progress.state = 'review'
            
        elif rating == SpacedRepetition.RATING_GOOD:
            if card_progress.state == 'new':
                card_progress.state = 'learning'
                card_progress.interval = SpacedRepetition.GRADUATING_INTERVAL
                card_progress.due_date = now + timedelta(days=SpacedRepetition.GRADUATING_INTERVAL)
            elif card_progress.state == 'learning':
                card_progress.state = 'review'
                card_progress.interval = SpacedRepetition.GRADUATING_INTERVAL
                card_progress.due_date = now + timedelta(days=SpacedRepetition.GRADUATING_INTERVAL)
                card_progress.repetitions += 1
            else:
                # Standard SM-2 algorithm
                if card_progress.repetitions == 0:
                    new_interval = SpacedRepetition.GRADUATING_INTERVAL
                elif card_progress.repetitions == 1:
                    new_interval = 6
                else:
                    new_interval = int(card_progress.interval * card_progress.ease_factor)
                
                card_progress.interval = new_interval
                card_progress.due_date = now + timedelta(days=new_interval)
                card_progress.repetitions += 1
                card_progress.state = 'review'
                
                # Update mastered status
                if card_progress.interval >= 21 and card_progress.repetitions >= 3:
                    card_progress.state = 'mastered'
            
        elif rating == SpacedRepetition.RATING_EASY:
            if card_progress.state == 'new':
                card_progress.state = 'review'
                card_progress.interval = SpacedRepetition.EASY_INTERVAL
                card_progress.due_date = now + timedelta(days=SpacedRepetition.EASY_INTERVAL)
                card_progress.repetitions = 1
            else:
                # Increase ease factor
                card_progress.ease_factor += 0.15
                
                # Calculate new interval with easy bonus
                if card_progress.repetitions == 0:
                    new_interval = SpacedRepetition.EASY_INTERVAL
                else:
                    base_interval = card_progress.interval * card_progress.ease_factor
                    new_interval = int(base_interval * SpacedRepetition.EASY_BONUS)
                
                card_progress.interval = new_interval
                card_progress.due_date = now + timedelta(days=new_interval)
                card_progress.repetitions += 1
                card_progress.state = 'review'
                
                # Update mastered status
                if card_progress.interval >= 21 and card_progress.repetitions >= 3:
                    card_progress.state = 'mastered'
        
        card_progress.last_reviewed = now
        card_progress.updated_at = now
        
        return card_progress
    
    @staticmethod
    def get_due_cards(deck_id, limit=20):
        """
        Get cards that are due for review
        
        Args:
            deck_id: ID of the deck
            limit: Maximum number of cards to return
        
        Returns:
            List of Card objects
        """
        from models import Card
        
        now = datetime.utcnow()
        
        # Get cards that are due or new - shuffled for variety
        cards = Card.query.filter_by(deck_id=deck_id).join(
            CardProgress, Card.id == CardProgress.card_id, isouter=True
        ).filter(
            db.or_(
                CardProgress.due_date == None,  # New cards
                CardProgress.due_date <= now   # Due cards
            )
        ).order_by(
            func.random()  # Shuffle cards for variety
        ).limit(limit).all()
        
        return cards
    
    @staticmethod
    def initialize_card_progress(card):
        """
        Initialize progress tracking for a new card
        
        Args:
            card: Card object
        
        Returns:
            CardProgress object
        """
        progress = CardProgress(
            card_id=card.id,
            state='new',
            due_date=datetime.utcnow(),
            interval=0,
            ease_factor=SpacedRepetition.STARTING_EASE,
            repetitions=0,
            lapses=0
        )
        return progress
    
    @staticmethod
    def record_review(card_id, rating, duration=0):
        """
        Record a review session
        
        Args:
            card_id: ID of the card
            rating: Rating given ('again', 'hard', 'good', 'easy')
            duration: Time spent reviewing in seconds
        
        Returns:
            Review object
        """
        review = Review(
            card_id=card_id,
            rating=rating,
            duration=duration,
            reviewed_at=datetime.utcnow()
        )
        return review
