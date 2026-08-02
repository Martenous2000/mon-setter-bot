"""Configuration de l'agent pilote — toutes les valeurs viennent des variables d'environnement Railway."""

import os

TELEGRAM_BOT_TOKEN = os.getenv("PILOT_TELEGRAM_BOT_TOKEN", "")
AUTHORIZED_CHAT_ID = os.getenv("PILOT_AUTHORIZED_CHAT_ID", "")

N8N_URL = os.getenv("N8N_URL", "https://n8n.srv940192.hstgr.cloud")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

GITHUB_TOKEN = os.getenv("PILOT_GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("PILOT_GITHUB_REPO", "Martenous2000/mon-setter-bot")

RAILWAY_TOKEN = os.getenv("PILOT_RAILWAY_TOKEN", "")
RAILWAY_PROJECT_ID = os.getenv("PILOT_RAILWAY_PROJECT_ID", "")

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
