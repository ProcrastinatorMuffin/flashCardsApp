import sqlite3
from datetime import datetime
from typing import Dict, List

class Database:
    def __init__(self, db_path: str = "flashcards.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        """Create all necessary tables"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP,
                last_studied TIMESTAMP,
                category TEXT
            );

            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY,
                deck_id INTEGER,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                confidence INTEGER DEFAULT 0,
                familiarity INTEGER DEFAULT 0,
                FOREIGN KEY (deck_id) REFERENCES decks(id)
            );

            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY,
                deck_id INTEGER,
                mode TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                correct_answers INTEGER,
                total_answers INTEGER,
                FOREIGN KEY (deck_id) REFERENCES decks(id)
            );

            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY,
                card_id INTEGER,
                timestamp TIMESTAMP,
                correct BOOLEAN,
                FOREIGN KEY (card_id) REFERENCES cards(id)
            );
        """)