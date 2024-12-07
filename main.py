from ui.ui import FlashcardUI
from model.deck import Deck
from model.flashcard import Flashcard

class FlashcardApp:
    def __init__(self, default_deck_path="resources/flashcards.txt"):
        self.default_deck_path = default_deck_path
        self.ui = None

    def load_default_deck(self) -> Deck:
        """Load the default flashcard deck"""
        try:
            deck = Deck.from_file("Default Deck", self.default_deck_path)
            return deck
        except FileNotFoundError:
            print(f"Warning: Default deck file not found at {self.default_deck_path}")
            return Deck("Default Deck")

    def run(self):
        """Start the flashcard application"""
        # Initialize UI
        self.ui = FlashcardUI()
        
        # Load default deck
        default_deck = self.load_default_deck()
        
        # Set up initial UI state
        if default_deck.get_card_count() > 0:
            self.ui.current_deck = default_deck
            self.ui.show_next_card()
            self.ui.update_stats()

        # Start UI main loop
        self.ui.mainloop()

def main():
    app = FlashcardApp()
    app.run()

if __name__ == "__main__":
    main()