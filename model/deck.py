from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from model.flashcard import Flashcard

# Type hint only, no runtime import
if TYPE_CHECKING:
    from data.data_access import DeckRepository


class Deck:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.flashcards: List[Flashcard] = []
        self.created_at = datetime.now()
        self.last_studied = None
        self.category = "General"
        self.study_sessions = []

    def add_card(self, card: Flashcard) -> None:
        """Add a single card to the deck"""
        self.flashcards.append(card)

    def add_cards(self, cards: List[Flashcard]) -> None:
        """Add multiple cards to the deck"""
        self.flashcards.extend(cards)

    def remove_card(self, card: Flashcard) -> None:
        """Remove a card from the deck"""
        if card in self.flashcards:
            self.flashcards.remove(card)

    def get_card_count(self) -> int:
        """Return total number of cards in deck"""
        return len(self.flashcards)

    def get_due_cards(self, study_mode: str = "normal") -> List[Flashcard]:
        """Return cards due for review based on study mode"""
        # To be implemented with repetition logic
        return self.flashcards

    def get_stats(self) -> dict:
        """Get deck statistics"""
        if not self.flashcards:
            return {"total_cards": 0, "average_confidence": 0}

        total_cards = len(self.flashcards)
        avg_confidence = sum(card.confidence for card in self.flashcards) / total_cards
        
        return {
            "total_cards": total_cards,
            "average_confidence": round(avg_confidence, 2),
            "last_studied": self.last_studied,
            "created_at": self.created_at
        }

    @classmethod
    def from_file(cls, name: str, file_path: str) -> 'Deck':
        """Create a deck from a file"""
        deck = cls(name)
        deck.flashcards = Flashcard.import_flashcards(file_path)
        return deck

    def export_to_file(self, file_path: str) -> None:
        """Export deck to a file"""
        with open(file_path, 'w') as f:
            for card in self.flashcards:
                f.write(f"{card.front}|{card.back}|{card.familiarity}\n")

    def start_study_session(self, mode: str = "normal", duration: Optional[int] = None) -> None:
        """Start a new study session"""
        self.last_studied = datetime.now()
        # Add study session tracking logic here

    def get_weak_cards(self) -> List[Flashcard]:
        """Get cards with low confidence scores"""
        return [card for card in self.flashcards if card.confidence < 0]
    
    def save(self, repository: 'DeckRepository') -> None:
        """Save deck and all its cards"""
        deck_id = repository.save_deck(self)
        for card in self.flashcards:
            repository.card_repo.save_card(card, deck_id)

    @classmethod
    def load(cls, deck_id: int, repository: 'DeckRepository') -> 'Deck':
        """Load deck with all its cards"""
        return repository.load_deck(deck_id)