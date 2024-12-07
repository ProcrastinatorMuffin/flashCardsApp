from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import math

from model.study_session_stats import StudySession, StudySessionStats
from model.flashcard import Flashcard
from typing import List, Optional, Dict
from enum import Enum
from model.deck import Deck
from model.study_modes import StudyMode

class RepetitionLogic:
    def __init__(self):
        # Base intervals for normal mode (in days)
        self.base_intervals = [1, 3, 7, 14, 30, 60, 120]
        self.current_session: Optional[StudySession] = None
        self.session_history: List[StudySession] = []

        
        # Mode-specific multipliers
        self.mode_multipliers = {
            StudyMode.QUICK: 0.3,      # Shorter intervals
            StudyMode.NORMAL: 1.0,     # Standard intervals
            StudyMode.EXAM_PREP: 0.5   # Medium intervals but more repetitions
        }
        
        # Track review history
        self.review_history: Dict[int, List[tuple]] = {}  # card_id: [(timestamp, correct)]
        self.last_review: Dict[int, datetime] = {}
        
    def calculate_card_priority(self, card: 'Flashcard', mode: StudyMode) -> float:
        """Calculate priority score for card selection"""
        now = datetime.now()
        card_id = id(card)
        last_review = self.last_review.get(card_id)
        
        # Base priority factors
        time_factor = 1.0
        confidence_factor = math.exp(-0.5 * card.confidence)  # Lower confidence = higher priority
        
        if last_review:
            days_since_review = (now - last_review).days
            time_factor = math.log(days_since_review + 1)
        
        # Mode-specific adjustments
        if mode == StudyMode.QUICK:
            # Prioritize cards with low confidence
            priority = confidence_factor * 2 + time_factor
        elif mode == StudyMode.EXAM_PREP:
            # Balance between confidence and time
            priority = confidence_factor + time_factor * 1.5
        else:  # NORMAL
            priority = (confidence_factor + time_factor) / 2
            
        return priority

    def get_next_interval(self, card: 'Flashcard', correct: bool, mode: StudyMode) -> int:
        """Calculate next review interval based on performance and mode"""
        card_id = id(card)
        
        # Initialize or update review history
        if card_id not in self.review_history:
            self.review_history[card_id] = []
        self.review_history[card_id].append((datetime.now(), correct))
        
        # Calculate success rate
        recent_reviews = self.review_history[card_id][-5:]  # Last 5 reviews
        success_rate = sum(1 for _, correct in recent_reviews if correct) / len(recent_reviews)
        
        # Get current level and adjust
        current_level = len(self.review_history[card_id]) - 1
        if not correct:
            current_level = max(0, current_level - 1)
            
        # Get base interval
        level_index = min(current_level, len(self.base_intervals) - 1)
        base_interval = self.base_intervals[level_index]
        
        # Apply mode multiplier
        interval = base_interval * self.mode_multipliers[mode]
        
        # Adjust for success rate
        interval *= (0.5 + success_rate)
        
        return max(1, round(interval))

    def get_due_cards(self, deck: 'Deck', mode: StudyMode, limit: Optional[int] = None) -> List['Flashcard']:
        """Get cards due for review based on mode and priorities"""
        now = datetime.now()
        all_cards = deck.flashcards
        
        # Calculate priority for each card
        card_priorities = [
            (card, self.calculate_card_priority(card, mode))
            for card in all_cards
        ]
        
        # Sort by priority (highest first)
        sorted_cards = [card for card, priority in 
                       sorted(card_priorities, key=lambda x: x[1], reverse=True)]
        
        if limit:
            return sorted_cards[:limit]
        return sorted_cards

    def update_review(self, card: 'Flashcard', correct: bool, mode: StudyMode) -> int:
        """Update card review status and handle session tracking"""
        # Session tracking logic
        if self.current_session:
            self.current_session.record_review(card, correct)
            
            # Check if session should end (duration reached)
            if self.current_session.target_duration:
                elapsed = (datetime.now() - self.current_session.stats.start_time).total_seconds() / 60
                if elapsed >= self.current_session.target_duration:
                    self.end_session()

        # Core review update logic
        card_id = id(card)
        self.last_review[card_id] = datetime.now()
        
        # Update confidence
        confidence_change = 1 if correct else -1
        if mode == StudyMode.EXAM_PREP:
            confidence_change *= 1.5
        card.confidence += confidence_change
        
        return self.get_next_interval(card, correct, mode)
    
    def start_session(self, mode: StudyMode, duration_minutes: Optional[int] = None) -> None:
        """Start a new study session"""
        if self.current_session:
            self.end_session()
        self.current_session = StudySession(mode, duration_minutes)
    
    def end_session(self) -> StudySessionStats:
        """End current session and return stats"""
        if self.current_session:
            self.current_session.end_session()
            self.session_history.append(self.current_session)
            stats = self.current_session.stats
            self.current_session = None
            return stats
        return None

    def get_study_patterns(self) -> Dict:
        """Analyze study patterns from session history"""
        if not self.session_history:
            return {}
            
        return {
            'average_accuracy': sum(s.stats.accuracy for s in self.session_history) / len(self.session_history),
            'average_duration': sum(s.stats.duration_minutes for s in self.session_history) / len(self.session_history),
            'total_cards_reviewed': sum(len(s.reviewed_cards) for s in self.session_history),
            'preferred_mode': max(
                StudyMode,
                key=lambda m: sum(1 for s in self.session_history if s.mode == m)
            )
        }
    
    def persist_review_history(self, db_cursor) -> None:
        """Save review history to database"""
        for card_id, reviews in self.review_history.items():
            for timestamp, correct in reviews:
                db_cursor.execute("""
                    INSERT INTO review_history 
                    (card_id, timestamp, correct)
                    VALUES (?, ?, ?)
                """, (card_id, timestamp, correct))
    
    def load_review_history(self, db_cursor) -> None:
        """Load review history from database"""
        cursor = db_cursor.execute("SELECT * FROM review_history ORDER BY timestamp")
        for row in cursor:
            card_id = row['card_id']
            if card_id not in self.review_history:
                self.review_history[card_id] = []
            self.review_history[card_id].append(
                (datetime.fromisoformat(row['timestamp']), row['correct'])
            )