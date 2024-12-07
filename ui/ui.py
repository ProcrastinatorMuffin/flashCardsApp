import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use('TkAgg')  # Must be before pyplot import
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import sys
import os
from typing import Optional, Dict, List
import math

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.latex2png import render_latex, setup_latex
from model.deck import Deck
from model.flashcard import Flashcard
from model.study_session_stats import StudySession
from repetition.repetition_logic import RepetitionLogic, StudyMode

class FlashcardUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # Check LaTeX setup
        if not setup_latex():
            messagebox.showerror(
                "Setup Error",
                "LaTeX or ImageMagick not found. Some features will be disabled."
            )
        
        self.title("Flashcards")
        self.geometry("1200x800")
        
        # Theme configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # State
        self.current_deck: Optional[Deck] = None
        self.current_card: Optional[Flashcard] = None
        self.is_card_flipped = False
        self.repetition_logic = RepetitionLogic()
        self.study_mode = StudyMode.NORMAL
        
        self.setup_ui()
        
    def configure_styles(self):
        """Configure custom styles for widgets"""
        self.style.configure(
            'Flashcard.TFrame',
            background='white',
            relief='raised',
            borderwidth=2
        )
        self.style.configure(
            'Sidebar.TFrame',
            background='#f0f0f0',
            relief='flat'
        )
        
    def setup_ui(self):
        """Setup main UI components"""
        # Main container
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        self.setup_sidebar()
        
        # Main content area
        self.content_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.content_frame, weight=3)
        
        # Flashcard area
        self.setup_flashcard_area()
        
        # Controls
        self.setup_controls()
        
    def setup_sidebar(self):
        """Setup sidebar with deck list and stats"""
        self.sidebar = ttk.Frame(self.main_container, style='Sidebar.TFrame')
        self.main_container.add(self.sidebar, weight=1)
        
        # Deck selection
        ttk.Label(self.sidebar, text="Decks").pack(pady=10)
        self.deck_list = ttk.Treeview(self.sidebar, height=10)
        self.deck_list.pack(fill=tk.X, padx=5)
        self.deck_list.bind('<<TreeviewSelect>>', self.on_deck_selected)
        
        # Stats section
        ttk.Label(self.sidebar, text="Statistics").pack(pady=10)
        self.stats_frame = ttk.Frame(self.sidebar)
        self.stats_frame.pack(fill=tk.X, padx=5)
        
        # Study mode selection
        ttk.Label(self.sidebar, text="Study Mode").pack(pady=10)
        self.mode_var = tk.StringVar(value=StudyMode.NORMAL.value)
        for mode in StudyMode:
            ttk.Radiobutton(
                self.sidebar,
                text=mode.value.title(),
                value=mode.value,
                variable=self.mode_var,
                command=self.on_mode_changed
            ).pack()
            
    def setup_flashcard_area(self):
        """Setup flashcard display area"""
        self.card_frame = ttk.Frame(
            self.content_frame,
            style='Flashcard.TFrame',
            height=400,
            width=600
        )
        self.card_frame.pack(pady=50, padx=50, expand=True)
        self.card_frame.pack_propagate(False)
        
        # Card content
        self.card_content = tk.Text(
            self.card_frame,
            wrap=tk.WORD,
            font=('Arial', 14),
            relief='flat',
            padx=20,
            pady=20
        )
        self.card_content.pack(fill=tk.BOTH, expand=True)
        self.card_content.bind('<Button-1>', self.flip_card)
        
    def setup_controls(self):
        """Setup control buttons"""
        self.control_frame = ttk.Frame(self.content_frame)
        self.control_frame.pack(pady=20)
        
        ttk.Button(
            self.control_frame,
            text="Correct ✓",
            command=lambda: self.handle_response(True)
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            self.control_frame,
            text="Incorrect ✗",
            command=lambda: self.handle_response(False)
        ).pack(side=tk.LEFT, padx=10)
        
    def flip_card(self, event=None):
        """Animate card flip"""
        if not self.current_card:
            return
            
        self.is_card_flipped = not self.is_card_flipped
        content = self.current_card.back if self.is_card_flipped else self.current_card.front
        
        # Animate flip
        for i in range(90):
            scale = abs(math.cos(math.radians(i)))
            self.card_frame.configure(width=int(600 * scale))
            self.update()
            
        self.update_card_content(content)
        
        for i in range(90, 180):
            scale = abs(math.cos(math.radians(i)))
            self.card_frame.configure(width=int(600 * scale))
            self.update()
            
    def update_card_content(self, content: str):
        """Update card content with LaTeX support"""
        self.card_content.delete('1.0', tk.END)
        
        # Parse content for LaTeX
        parts = self.parse_latex(content)
        for part in parts:
            if part.startswith('$$'):
                # Render LaTeX
                latex = part[2:-2]
                img = latex2png.render_latex(latex)
                self.card_content.image_create(tk.END, image=img)
                self.card_content.image = img  # Keep reference
            else:
                self.card_content.insert(tk.END, part)
                
    def parse_latex(self, content: str) -> List[str]:
        """Parse content into text and LaTeX parts"""
        parts = []
        current = ""
        i = 0
        
        while i < len(content):
            if content[i:i+2] == "$$":
                if current:
                    parts.append(current)
                    current = ""
                    
                # Find closing $$
                end = content.find("$$", i+2)
                if end == -1:
                    current += content[i:]
                    break
                    
                parts.append(content[i:end+2])
                i = end + 2
            else:
                current += content[i]
                i += 1
                
        if current:
            parts.append(current)
            
        return parts
        
    def handle_response(self, correct: bool):
        """Handle user response to current card"""
        if not self.current_card:
            return
            
        # Update repetition logic
        next_interval = self.repetition_logic.update_review(
            self.current_card,
            correct,
            StudyMode(self.mode_var.get())
        )
        
        # Show next card
        self.show_next_card()
        
        # Update stats
        self.update_stats()
        
    def show_next_card(self):
        """Show next due card"""
        if not self.current_deck:
            return
            
        due_cards = self.repetition_logic.get_due_cards(
            self.current_deck,
            StudyMode(self.mode_var.get()),
            limit=1
        )
        
        if due_cards:
            self.current_card = due_cards[0]
            self.is_card_flipped = False
            self.update_card_content(self.current_card.front)
        else:
            self.card_content.delete('1.0', tk.END)
            self.card_content.insert('1.0', "No more cards due for review!")
            
    def update_stats(self):
        """Update statistics display"""
        if not self.current_deck:
            return
            
        stats = self.current_deck.get_stats()
        study_patterns = self.repetition_logic.get_study_patterns()
        
        # Clear previous stats
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        # Create stats display
        stats_text = (
            f"Total Cards: {stats['total_cards']}\n"
            f"Average Confidence: {stats['average_confidence']:.1f}\n"
            f"Session Accuracy: {study_patterns.get('average_accuracy', 0):.1%}\n"
            f"Cards Reviewed: {study_patterns.get('total_cards_reviewed', 0)}"
        )
        
        ttk.Label(self.stats_frame, text=stats_text).pack()
        
        # Add progress chart
        self.update_progress_chart()
        
    def update_progress_chart(self):
        """Update progress chart in sidebar"""
        fig, ax = plt.subplots(figsize=(3, 2))
        
        # Get study session data
        sessions = self.repetition_logic.session_history
        dates = [s.stats.start_time for s in sessions]
        accuracies = [s.stats.accuracy for s in sessions]
        
        if dates:
            ax.plot(dates, accuracies, marker='o')
            ax.set_ylabel('Accuracy')
            ax.set_title('Learning Progress')
            
            # Rotate dates for better readability
            plt.xticks(rotation=45)
            
            # Add to sidebar
            canvas = FigureCanvasTkAgg(fig, self.stats_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.X, pady=10)
            
    def on_deck_selected(self, event):
        """Handle deck selection"""
        selection = self.deck_list.selection()
        if not selection:
            return
            
        deck_id = self.deck_list.item(selection[0])['values'][0]
        self.current_deck = self.load_deck(deck_id)
        self.show_next_card()
        self.update_stats()
        
    def on_mode_changed(self):
        """Handle study mode change"""
        self.study_mode = StudyMode(self.mode_var.get())
        if self.current_deck:
            self.show_next_card()
            
    def load_deck(self, deck_id: int) -> Deck:
        """Load deck from repository"""
        # Implementation depends on your data access layer
        pass

if __name__ == "__main__":
    app = FlashcardUI()
    app.mainloop()