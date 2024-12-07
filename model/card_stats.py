from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict
from enum import Enum
from data.database.database import Database

class ReviewResult(Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    SKIPPED = "skipped"

@dataclass
class ReviewEntry:
    timestamp: datetime
    result: ReviewResult
    time_taken: float  # seconds
    confidence_before: int
    confidence_after: int

@dataclass
class CardStats:
    card_id: int
    total_reviews: int = 0
    correct_reviews: int = 0
    review_history: List[ReviewEntry] = field(default_factory=list)
    last_reviewed: datetime = None
    average_response_time: float = 0.0

    def __post_init__(self):
        self.db = Database()
    
    def record_review(self, result: ReviewResult, time_taken: float, 
                     confidence_before: int, confidence_after: int) -> None:
        """Record a new review attempt"""
        self.total_reviews += 1
        if result == ReviewResult.CORRECT:
            self.correct_reviews += 1
            
        entry = ReviewEntry(
            timestamp=datetime.now(),
            result=result,
            time_taken=time_taken,
            confidence_before=confidence_before,
            confidence_after=confidence_after
        )
        self.review_history.append(entry)
        self.last_reviewed = entry.timestamp
        
        # Update average response time
        self.average_response_time = (
            (self.average_response_time * (self.total_reviews - 1) + time_taken) 
            / self.total_reviews
        )

    def get_accuracy(self) -> float:
        """Calculate overall accuracy rate"""
        return self.correct_reviews / self.total_reviews if self.total_reviews > 0 else 0.0

    def get_recent_performance(self, days: int = 7) -> Dict:
        """Get performance statistics for recent reviews"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_reviews = [r for r in self.review_history if r.timestamp >= cutoff]
        
        if not recent_reviews:
            return {
                "total_reviews": 0,
                "accuracy": 0.0,
                "average_time": 0.0,
                "confidence_change": 0.0
            }
            
        correct = sum(1 for r in recent_reviews if r.result == ReviewResult.CORRECT)
        avg_time = sum(r.time_taken for r in recent_reviews) / len(recent_reviews)
        confidence_change = recent_reviews[-1].confidence_after - recent_reviews[0].confidence_before
        
        return {
            "total_reviews": len(recent_reviews),
            "accuracy": correct / len(recent_reviews),
            "average_time": avg_time,
            "confidence_change": confidence_change
        }

    def needs_review(self, interval_hours: int = 24) -> bool:
        """Check if card needs review based on time interval"""
        if not self.last_reviewed:
            return True
        time_since_review = datetime.now() - self.last_reviewed
        return time_since_review.total_seconds() >= (interval_hours * 3600)

    def save(self, db_cursor) -> None:
        """Save card statistics to database"""
        db_cursor.execute("""
            INSERT OR REPLACE INTO card_stats 
            (card_id, total_reviews, correct_reviews, last_reviewed, average_response_time)
            VALUES (?, ?, ?, ?, ?)
        """, (self.card_id, self.total_reviews, self.correct_reviews,
              self.last_reviewed, self.average_response_time))
        
        # Save review history
        for entry in self.review_history:
            db_cursor.execute("""
                INSERT INTO review_history 
                (card_id, timestamp, result, time_taken, 
                 confidence_before, confidence_after)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.card_id, entry.timestamp, entry.result.value,
                  entry.time_taken, entry.confidence_before, 
                  entry.confidence_after))

    @classmethod
    def load(cls, card_id: int, db_cursor) -> 'CardStats':
        """Load card statistics from database"""
        db_cursor.execute(
            "SELECT * FROM card_stats WHERE card_id = ?", (card_id,))
        stats_row = db_cursor.fetchone()
        
        if not stats_row:
            return cls(card_id=card_id)
            
        stats = cls(
            card_id=card_id,
            total_reviews=stats_row['total_reviews'],
            correct_reviews=stats_row['correct_reviews'],
            last_reviewed=datetime.fromisoformat(stats_row['last_reviewed']),
            average_response_time=stats_row['average_response_time']
        )
        
        # Load review history
        db_cursor.execute(
            "SELECT * FROM review_history WHERE card_id = ?", (card_id,))
        for row in db_cursor.fetchall():
            entry = ReviewEntry(
                timestamp=datetime.fromisoformat(row['timestamp']),
                result=ReviewResult(row['result']),
                time_taken=row['time_taken'],
                confidence_before=row['confidence_before'],
                confidence_after=row['confidence_after']
            )
            stats.review_history.append(entry)
            
        return stats