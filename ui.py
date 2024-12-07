import tkinter as tk
from flashcards import Flashcard

class FlashcardsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcards App")
        self.current_flashcard = None
        self.flashcards = []
        self.front_displayed = True

        self.frame = tk.Frame(self.root)
        self.frame.pack(pady=20)

        self.flashcard_label = tk.Label(self.frame, text="", font=("Helvetica", 24))
        self.flashcard_label.pack(pady=10)

        self.flip_button = tk.Button(self.frame, text="Flip", command=self.flip_flashcard)
        self.flip_button.pack(side=tk.LEFT, padx=10)

        self.correct_button = tk.Button(self.frame, text="Correct", command=lambda: self.update_confidence(True))
        self.correct_button.pack(side=tk.LEFT, padx=10)

        self.incorrect_button = tk.Button(self.frame, text="Incorrect", command=lambda: self.update_confidence(False))
        self.incorrect_button.pack(side=tk.LEFT, padx=10)

        self.stats_button = tk.Button(self.frame, text="Stats", command=self.display_stats)
        self.stats_button.pack(side=tk.LEFT, padx=10)

    def load_flashcards(self, file_path):
        self.flashcards = Flashcard.import_flashcards(file_path)
        if self.flashcards:
            self.current_flashcard = self.flashcards[0]
            self.display_flashcard()

    def display_flashcard(self):
        if self.current_flashcard:
            self.flashcard_label.config(text=self.current_flashcard.front if self.front_displayed else self.current_flashcard.back)

    def flip_flashcard(self):
        self.front_displayed = not self.front_displayed
        self.display_flashcard()

    def update_confidence(self, correct):
        if self.current_flashcard:
            self.current_flashcard.update_confidence(correct)
            self.next_flashcard()

    def next_flashcard(self):
        if self.flashcards:
            current_index = self.flashcards.index(self.current_flashcard)
            next_index = (current_index + 1) % len(self.flashcards)
            self.current_flashcard = self.flashcards[next_index]
            self.front_displayed = True
            self.display_flashcard()

    def display_stats(self):
        Flashcard.display_stats(self.flashcards)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardsApp(root)
    app.load_flashcards("flashcards.txt")
    root.mainloop()
