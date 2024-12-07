class UserStats:
    def __init__(self, flashcards):
        self.flashcards = flashcards

    def calculate_mastery(self):
        mastery = {}
        for flashcard in self.flashcards:
            deck = flashcard.deck
            if deck not in mastery:
                mastery[deck] = {'total': 0, 'confidence': 0}
            mastery[deck]['total'] += 1
            mastery[deck]['confidence'] += flashcard.confidence
        for deck in mastery:
            mastery[deck]['average_confidence'] = mastery[deck]['confidence'] / mastery[deck]['total']
        return mastery

    def display_mastery(self):
        mastery = self.calculate_mastery()
        for deck, stats in mastery.items():
            print(f"Deck: {deck}")
            print(f"Total flashcards: {stats['total']}")
            print(f"Average confidence: {stats['average_confidence']:.2f}")

    def display_overall_stats(self):
        total_flashcards = len(self.flashcards)
        total_confidence = sum(flashcard.confidence for flashcard in self.flashcards)
        average_confidence = total_confidence / total_flashcards if total_flashcards > 0 else 0
        print(f"Total flashcards: {total_flashcards}")
        print(f"Average confidence: {average_confidence:.2f}")