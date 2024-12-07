from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, TYPE_CHECKING
from enum import Enum
import math
from model.flashcard import Flashcard
from model.study_modes import StudyMode  # Add direct import

@dataclass
class StudySessionStats:
    correct_answers: int = 0
    total_answers: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = None
    
    @property
    def duration_minutes(self) -> float:
        if not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds() / 60
    
    @property
    def accuracy(self) -> float:
        return self.correct_answers / self.total_answers if self.total_answers > 0 else 0

class StudySession:
    def __init__(self, mode: StudyMode, target_duration: Optional[int] = None):
        self.mode = mode
        self.target_duration = target_duration
        self.stats = StudySessionStats()
        self.reviewed_cards: Set[int] = set()
        
    def record_review(self, card: 'Flashcard', correct: bool) -> None:
        self.stats.total_answers += 1
        if correct:
            self.stats.correct_answers += 1
        self.reviewed_cards.add(id(card))
    
    def end_session(self) -> None:
        self.stats.end_time = datetime.now()