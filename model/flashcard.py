class Flashcard:
    def __init__(self, front, back, familiarity=0):
        self.front = front
        self.back = back
        self.confidence = 0
        self.familiarity = familiarity  # New attribute for initial familiarity

    @staticmethod
    def import_flashcards(file_path):
        flashcards = []
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split('|')
                front = parts[0]
                back = parts[1]
                familiarity = int(parts[2]) if len(parts) > 2 else 0
                flashcards.append(Flashcard(front, back, familiarity))
        return flashcards

    def display_flashcard(self):
        print(f"Front: {self.front}")
        input("Press Enter to flip the card...")
        print(f"Back: {self.back}")

    def update_confidence(self, correct):
        if correct:
            self.confidence += 1
        else:
            self.confidence -= 1

    @staticmethod
    def display_stats(flashcards):
        total_cards = len(flashcards)
        total_confidence = sum(card.confidence for card in flashcards)
        average_confidence = total_confidence / total_cards if total_cards > 0 else 0
        print(f"Total flashcards: {total_cards}")
        print(f"Average confidence: {average_confidence:.2f}")