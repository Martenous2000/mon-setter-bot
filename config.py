"""Configuration centrale — TOUT ce qui est propre à ton business vient d'ici.

Les valeurs sont lues depuis les variables d'environnement (fichier .env en local,
ou variables Railway en production). Aucune info personnelle n'est codée en dur ici :
tu remplis ton .env (voir .env.example), et c'est tout.
"""

import os

# --- Identité du persona (toi) ---
# PERSONA_KEY doit correspondre au nom du fichier dans prompts/personas/ (sans .md).
# Par défaut "me" → prompts/personas/me.md
PERSONA_KEY = os.getenv("PERSONA_KEY", "me")
# Le prénom affiché dans l'historique de conversation envoyé au modèle.
PERSONA_DISPLAY_NAME = os.getenv("PERSONA_DISPLAY_NAME", "Moi")

# --- Liens canoniques de ton offre ---
# Le bot ne les écrit JAMAIS à la main : il appelle un tool qui renvoie ces URLs.
# Laisse vide ("") un lien que tu n'utilises pas — le tool correspondant le signalera.
CALENDLY_URL = os.getenv("CALENDLY_URL", "")
YOUTUBE_URL = os.getenv("YOUTUBE_URL", "")
WEBSITE_URL = os.getenv("WEBSITE_URL", "")

# --- Alerte Telegram (invitation directe demandée par un prospect) ---
TELEGRAM_ALERT_BOT_TOKEN = os.getenv("TELEGRAM_ALERT_BOT_TOKEN", "")
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")

# --- Google Calendar (lecture des créneaux libres pour proposer un rendez-vous) ---
GOOGLE_CALENDAR_CLIENT_ID = os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "")
GOOGLE_CALENDAR_CLIENT_SECRET = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "")
GOOGLE_CALENDAR_REFRESH_TOKEN = os.getenv("GOOGLE_CALENDAR_REFRESH_TOKEN", "")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")
# Contraintes de disponibilité (heures locales, fuseau Europe/Paris)
WORKDAY_START_HOUR = 8
WORKDAY_START_MINUTE = 30
WORKDAY_END_HOUR = 21
WORKDAY_END_MINUTE = 15
LUNCH_BREAK_START_HOUR = 12
LUNCH_BREAK_START_MINUTE = 30
LUNCH_BREAK_END_HOUR = 13
LUNCH_BREAK_END_MINUTE = 30

# --- Modèle & limites (réglages avancés, valeurs par défaut OK) ---
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_THINKING_TOKENS = int(os.getenv("MAX_THINKING_TOKENS", "8000"))
MAX_TURNS = int(os.getenv("MAX_TURNS", "15"))

# Signal interne de handover (ne pas changer)
HANDOVER_SIGNAL = "PAUSE_CONVERSATION"
