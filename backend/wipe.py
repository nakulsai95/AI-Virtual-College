"""Wipe the college — back to fresh onboarding.

Clears the curriculum, faculty, lessons, exams, board, channels, materials and
progress. KEEPS your connector key, credit budget, and usage history.
Safe to run while the server is up.

Usage:  .venv\\Scripts\\python wipe.py   (or double-click wipe.bat)
"""
from app import db

db.init_db()
db.reset_college()
print("College wiped — reload the app (Ctrl+F5) to onboard fresh.")
print("Your model connection and credit budget were kept.")
