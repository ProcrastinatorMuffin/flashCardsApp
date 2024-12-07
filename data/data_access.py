from datetime import datetime
from typing import List, TYPE_CHECKING
from model.study_session_stats import StudySession
from model.flashcard import Flashcard
from data.database.database import Database
import sqlite3

if TYPE_CHECKING:
    from model.deck import Deck

class DeckRepository:
    def __init__(self, db: Database):
        self.db = db
        self.card_repo = CardRepository(db)

    def save_deck(self, deck: 'Deck') -> int:
        cursor = self.db.conn.execute("""
            INSERT INTO decks (name, description, created_at, last_studied, category)
            VALUES (?, ?, ?, ?, ?)
        """, (deck.name, deck.description, deck.created_at, deck.last_studied, deck.category))
        self.db.conn.commit()
        return cursor.lastrowid

    def load_deck(self, deck_id: int) -> 'Deck':
        cursor = self.db.conn.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Deck {deck_id} not found")
            
        deck = Deck(row['name'], row['description'])
        deck.created_at = datetime.fromisoformat(row['created_at'])
        deck.last_studied = datetime.fromisoformat(row['last_studied']) if row['last_studied'] else None
        deck.category = row['category']
        
        # Load cards
        deck.flashcards = self.card_repo.load_cards_for_deck(deck_id)
        return deck

class StudySessionRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_session(self, session: StudySession, deck_id: int) -> int:
        cursor = self.db.conn.execute("""
            INSERT INTO study_sessions 
            (deck_id, mode, start_time, end_time, correct_answers, total_answers)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (deck_id, session.mode, session.stats.start_time, 
              session.stats.end_time, session.stats.correct_answers,
              session.stats.total_answers))
        self.db.conn.commit()
        return cursor.lastrowid

    def get_sessions_for_deck(self, deck_id: int) -> List[StudySession]:
        cursor = self.db.conn.execute(
            "SELECT * FROM study_sessions WHERE deck_id = ?", (deck_id,))
        return [self._map_to_session(row) for row in cursor.fetchall()]

class CardRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_card(self, card: 'Flashcard', deck_id: int) -> int:
        cursor = self.db.conn.execute("""
            INSERT INTO cards (deck_id, front, back, confidence, familiarity)
            VALUES (?, ?, ?, ?, ?)
        """, (deck_id, card.front, card.back, card.confidence, card.familiarity))
        self.db.conn.commit()
        return cursor.lastrowid

    def load_cards_for_deck(self, deck_id: int) -> List['Flashcard']:
        cursor = self.db.conn.execute(
            "SELECT * FROM cards WHERE deck_id = ?", (deck_id,))
        return [self._map_to_card(row) for row in cursor.fetchall()]

    def _map_to_card(self, row: sqlite3.Row) -> 'Flashcard':
        card = Flashcard(row['front'], row['back'], row['familiarity'])
        card.confidence = row['confidence']
        return card