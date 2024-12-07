from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from model.card_stats import CardStats, ReviewResult
from model.study_session_stats import StudySession
from data.database.database import Database

@dataclass
class DeckStats:
    deck_id: int
    total_cards: int = 0
    cards_stats: Dict[int, CardStats] = field(default_factory=dict)
    study_sessions: List[StudySession] = field(default_factory=list)
    last_studied: datetime = None

    def __post_init__(self):
        self.db = Database()
    
    def add_card_stats(self, card_stats: CardStats) -> None:
        """Add or update statistics for a card"""
        self.cards_stats[card_stats.card_id] = card_stats
        self.total_cards = len(self.cards_stats)

    def record_study_session(self, session: StudySession) -> None:
        """Record a completed study session"""
        self.study_sessions.append(session)
        self.last_studied = session.stats.end_time

    def get_overall_stats(self) -> Dict:
        """Calculate overall deck statistics"""
        if not self.cards_stats:
            return {
                "total_cards": 0,
                "average_accuracy": 0.0,
                "average_response_time": 0.0,
                "mastery_level": 0.0
            }

        total_accuracy = sum(cs.get_accuracy() for cs in self.cards_stats.values())
        total_time = sum(cs.average_response_time for cs in self.cards_stats.values())
        
        return {
            "total_cards": self.total_cards,
            "average_accuracy": total_accuracy / self.total_cards,
            "average_response_time": total_time / self.total_cards,
            "mastery_level": self._calculate_mastery_level()
        }

    def get_study_trends(self, days: int = 30) -> Dict:
        """Analyze study trends over time"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_sessions = [s for s in self.study_sessions 
                         if s.stats.start_time >= cutoff]
        
        if not recent_sessions:
            return {
                "sessions_count": 0,
                "total_study_time": 0,
                "average_accuracy": 0.0,
                "cards_per_session": 0
            }
            
        total_time = sum(s.stats.duration_minutes for s in recent_sessions)
        total_accuracy = sum(s.stats.accuracy for s in recent_sessions)
        cards_reviewed = sum(len(s.reviewed_cards) for s in recent_sessions)
        
        return {
            "sessions_count": len(recent_sessions),
            "total_study_time": total_time,
            "average_accuracy": total_accuracy / len(recent_sessions),
            "cards_per_session": cards_reviewed / len(recent_sessions)
        }

    def get_weak_cards(self, threshold: float = 0.7) -> List[int]:
        """Get cards with below-threshold accuracy"""
        return [card_id for card_id, stats in self.cards_stats.items()
                if stats.get_accuracy() < threshold]

    def _calculate_mastery_level(self) -> float:
        """Calculate overall deck mastery level (0-1)"""
        if not self.cards_stats:
            return 0.0
            
        total_mastery = sum(
            (cs.correct_reviews / cs.total_reviews if cs.total_reviews > 0 else 0)
            * (1 - min(5, cs.average_response_time) / 5)  # Time factor
            for cs in self.cards_stats.values()
        )
        return total_mastery / self.total_cards

    def save(self, db_cursor) -> None:
        """Save deck statistics to database"""
        db_cursor.execute("""
            INSERT OR REPLACE INTO deck_stats 
            (deck_id, total_cards, last_studied)
            VALUES (?, ?, ?)
        """, (self.deck_id, self.total_cards, self.last_studied))
        
        # Save individual card stats
        for card_stats in self.cards_stats.values():
            card_stats.save(db_cursor)

    @classmethod
    def load(cls, deck_id: int, db_cursor) -> 'DeckStats':
        """Load deck statistics from database"""
        cursor = db_cursor.execute(
            "SELECT * FROM deck_stats WHERE deck_id = ?", (deck_id,))
        row = cursor.fetchone()
        
        if not row:
            return cls(deck_id=deck_id)
            
        stats = cls(
            deck_id=deck_id,
            total_cards=row['total_cards'],
            last_studied=datetime.fromisoformat(row['last_studied'])
            if row['last_studied'] else None
        )
        
        # Load card stats
        cursor = db_cursor.execute(
            "SELECT card_id FROM cards WHERE deck_id = ?", (deck_id,))
        for card_row in cursor.fetchall():
            card_stats = CardStats.load(card_row['card_id'], db_cursor)
            stats.cards_stats[card_row['card_id']] = card_stats
            
        return stats