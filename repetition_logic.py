class RepetitionLogic:
    def __init__(self):
        self.repetition_intervals = [1, 3, 7, 14, 30]  # days
        self.flashcard_schedule = {}

    def calculate_next_repetition_time(self, flashcard, correct):
        if flashcard not in self.flashcard_schedule:
            self.flashcard_schedule[flashcard] = 0

        if correct:
            self.flashcard_schedule[flashcard] += 1
        else:
            self.flashcard_schedule[flashcard] = max(0, self.flashcard_schedule[flashcard] - 1)

        interval_index = min(self.flashcard_schedule[flashcard], len(self.repetition_intervals) - 1)
        next_repetition_days = self.repetition_intervals[interval_index]
        return next_repetition_days

    def update_confidence(self, flashcard, correct):
        if correct:
            flashcard.confidence += 1
        else:
            flashcard.confidence -= 1
