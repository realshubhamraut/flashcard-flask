from app import app, db
from models import Review, Card, Deck
from datetime import datetime, timedelta
from sqlalchemy import func

with app.app_context():
    # Check if there are any reviews
    review_count = db.session.query(Review).count()
    print(f"Total reviews in database: {review_count}")
    
    if review_count > 0:
        # Get recent reviews
        recent = db.session.query(Review).order_by(Review.reviewed_at.desc()).limit(5).all()
        print("\nRecent reviews:")
        for r in recent:
            print(f"  - Card ID: {r.card_id}, Rating: {r.rating}, Date: {r.reviewed_at}")
    
    # Check the API data
    start_date = datetime.utcnow() - timedelta(days=7)
    accuracy_history = db.session.query(
        func.date(Review.reviewed_at).label('date'),
        func.count(Review.id).label('total'),
        func.sum(
            db.case(
                (Review.rating == 'correct', 1),
                else_=0
            )
        ).label('correct')
    ).filter(
        Review.reviewed_at >= start_date
    ).group_by(
        func.date(Review.reviewed_at)
    ).all()
    
    print(f"\nAccuracy data for last 7 days: {len(accuracy_history)} days")
    for a in accuracy_history:
        acc = round((a.correct / a.total * 100), 1) if a.total > 0 else 0
        print(f"  {a.date}: {a.correct}/{a.total} = {acc}%")
