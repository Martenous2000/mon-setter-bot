import asyncio
import contextvars
import json
import os
import re
import urllib.request
import httpx
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import calendar_utils
import config

load_dotenv()

# Valeurs propres au business — viennent de config.py (lui-même alimenté par le .env)
CANONICAL_CALENDLY = config.CALENDLY_URL
CANONICAL_YOUTUBE = config.YOUTUBE_URL
CANONICAL_WEBSITE = config.WEBSITE_URL
HANDOVER_SIGNAL = config.HANDOVER_SIGNAL
TELEGRAM_ALERT_BOT_TOKEN = config.TELEGRAM_ALERT_BOT_TOKEN
TELEGRAM_ALERT_CHAT_ID = config.TELEGRAM_ALERT_CHAT_ID

# Contexte de la conversation en cours (chat_id, compte) — lu par les tools qui en ont besoin,
# posé au début de chaque requête /chat. Un ContextVar isole correctement les requêtes concurrentes.
CURRENT_CHAT_CONTEXT: contextvars.ContextVar[dict] = contextvars.ContextVar("chat_context", default={})

MODEL = config.MODEL
MAX_THINKING_TOKENS = config.MAX_THINKING_TOKENS
MAX_TURNS = config.MAX_TURNS

PROMPTS_DIR = Path(__file__).parent / "prompts"
PERSONAS_DIR = PROMPTS_DIR / "personas"
SKILLS_DIR = PROMPTS_DIR / "skills"

PERSONA_CACHE: dict[str, str] = {
    p.stem: p.read_text(encoding="utf-8") for p in PERSONAS_DIR.glob("*.md")
}
PRINCIPES = (PROMPTS_DIR / "principes.md").read_text(encoding="utf-8")

# Skills loaded on demand by the bot via load_skill(name) tool.
SKILLS_CACHE: dict[str, str] = {
    s.stem: s.read_text(encoding="utf-8") for s in SKILLS_DIR.glob("*.md")
}

DEFAULT_PERSONA = config.PERSONA_KEY


def build_full_system_prompt(persona: str) -> str:
    """System prompt = persona injecté en haut, puis le doc 'principes premiers'."""
    persona_block = PERSONA_CACHE.get(persona) or next(iter(PERSONA_CACHE.values()), "")
    return f"{persona_block}\n\n---\n\n{PRINCIPES}"


SYSTEM_PROMPTS: dict[str, str] = {
    p: build_full_system_prompt(p) for p in PERSONA_CACHE.keys()
}


@tool(
    "get_calendly_link",
    "Retourne l'URL canonique de ton Calendly. UTILISE ce tool dès que tu veux partager le lien de réservation — ne jamais écrire l'URL à la main.",
    {},
)
async def get_calendly_link(args):
    ctx = CURRENT_CHAT_CONTEXT.get()
    persona = ctx.get("persona", "")
    if persona == "nathan-elora":
        url = "https://calendly.com/nathan-vanbignoot-bananagency/30mi"
    elif persona == "enzo":
        url = "https://calendly.com/enzo-vidiella83/30min"
    elif persona == "florian":
        url = "https://calendly.com/floriangrospro/call-rencontre"
    else:
        url = CANONICAL_CALENDLY or "https://app.iclosed.io/e/visionary-consulting/visionary-consulting"
    return {"content": [{"type": "text", "text": url}]}


_JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


@tool(
    "get_available_slots",
    (
        "Retourne 2 créneaux de rendez-vous réellement libres dans l'agenda, en respectant les horaires de "
        "disponibilité et en excluant tout ce qui est déjà bloqué. UTILISE ce tool dès que tu t'apprêtes à "
        "proposer un ou plusieurs créneaux horaires précis au prospect (Temps 4b de phase-4-call) — ne propose "
        "JAMAIS un horaire au hasard ou inventé, appelle toujours ce tool d'abord."
    ),
    {},
)
async def get_available_slots(args):
    try:
        slots = await asyncio.to_thread(calendar_utils.get_next_available_slots, 2)
    except Exception:
        return {
            "content": [{"type": "text", "text": "Agenda indisponible pour le moment — propose de vive voix sans créneau précis, ou passe par notify_booking_issue si le prospect insiste."}],
            "is_error": True,
        }
    if not slots:
        return {"content": [{"type": "text", "text": "Aucun créneau libre trouvé dans les 10 prochains jours."}], "is_error": True}
    formatted = [f"{_JOURS_FR[s.weekday()]} à {s.strftime('%Hh%M')}" for s in slots]
    return {"content": [{"type": "text", "text": " ou ".join(formatted)}]}


@tool(
    "get_youtube_link",
    "Retourne l'URL canonique de ta vidéo / mini-VSL. UTILISE ce tool dès que tu veux partager la vidéo.",
    {},
)
async def get_youtube_link(args):
    url = CANONICAL_YOUTUBE or "(aucune vidéo configurée — ne propose pas de vidéo)"
    return {"content": [{"type": "text", "text": url}]}


@tool(
    "get_website_link",
    "Retourne l'URL canonique de ton site qui détaille l'offre, le mécanisme, les tarifs et la garantie. UTILISE ce tool quand le prospect demande plus d'infos sur l'offre, le fonctionnement, les tarifs, ou veut creuser avant de réserver. Tu envoies une brève explication de ta voix + le lien pour creuser.",
    {},
)
async def get_website_link(args):
    url = CANONICAL_WEBSITE or "(aucun site configuré — explique de vive voix sans lien)"
    return {"content": [{"type": "text", "text": url}]}


@tool(
    "load_skill",
    (
        "Charge le contenu d'une skill à la demande.\n\n"
        ""
        "⚠️ OBLIGATOIRE, PAS OPTIONNEL — `objections` : dès que le prospect formule QUOI QUE CE SOIT "
        "qui ressemble à une objection, une résistance, un doute ou une croyance qui s'oppose à ton offre "
        "(y compris tôt dans la conversation, y compris si tu penses déjà connaître la réponse), tu appelles "
        "load_skill('objections') AVANT de répondre. Ce n'est jamais laissé à ton instinct ni à ton jugement du "
        "moment — c'est une vérification systématique, à chaque objection, sans exception. Cette fiche contient "
        "notamment 3 réponses marquées \"COPIER-COLLER EXACT\" (bot repéré comme automatique, outil similaire déjà "
        "essayé sans succès, peur du bannissement LinkedIn) que tu dois recopier mot pour mot, sans reformuler "
        "une seule syllabe, si l'objection correspond à l'une des trois.\n\n"
        ""
        "Pour les autres skills ci-dessous, tu les invoques quand ton instinct le justifie — pas par défaut. "
        "Si tu doutes qu'une skill t'aide → ne charge pas.\n\n"
        ""
        "PHASES DU FIL ROUGE (charge la skill de la phase courante quand tu veux le détail tactique) :\n"
        "- `phase-1-defiance` — chitchat, casser la méfiance, signaux d'ouverture\n"
        "- `phase-2-acquisition` — faire émerger le pain + mini-transformation + offre modulaire\n"
        "- `phase-3-asset` — asset de valeur matché au pain + réciprocité\n"
        "- `phase-4-call` — proposer le call en 2 temps (4a tester l'intention, 4b envoyer le lien)\n"
        "- `phase-5-post-booking` — protéger le call, less is more, aucun ask\n\n"
        ""
        "TES AUTRES FICHES BUSINESS (à remplir, propres à ton activité) :\n"
        "- `bio-detail` — ton parcours complet et tes preuves sociales. "
        "À charger quand le prospect demande qui tu es, ton parcours, ta crédibilité.\n"
        "- `business-info` — ton offre détaillée, ton mécanisme, et les réponses canoniques "
        "aux questions pièges sur ton offre.\n\n"
        ""
        "10 LIVRES DE PERSUASION (références génériques) :\n"
        "cialdini-influence, cialdini-presuasion, voss-never-split, carnegie-win-friends, "
        "greene-human-nature, pink-to-sell-is-human, dixon-challenger-sale, fitzpatrick-mom-test, "
        "rackham-spin-selling, kahneman-thinking.\n\n"
        ""
        "ARGS :\n"
        "- name : le nom exact de la skill (kebab-case sans extension)"
    ),
    {"name": str},
)
async def load_skill(args):
    name = (args.get("name") or "").strip()
    content = SKILLS_CACHE.get(name)
    if not content:
        available = ", ".join(sorted(SKILLS_CACHE.keys()))
        return {"content": [{"type": "text", "text": f"Skill '{name}' introuvable. Disponibles : {available}"}], "is_error": True}
    return {"content": [{"type": "text", "text": content}]}


@tool(
    "notify_booking_issue",
    (
        "Alerte Martin sur Telegram QUAND la prise de rendez-vous via le lien de réservation ne peut pas se faire normalement. "
        "Deux cas d'usage : (1) le prospect dit explicitement qu'il ne veut PAS utiliser le lien et préfère une invitation "
        "calendrier directe, (2) le prospect signale un problème avec le lien lui-même (lien cassé, page qui ne charge pas, "
        "aucun créneau disponible, erreur au moment de valider). N'utilise JAMAIS ce tool pour un simple refus de call en "
        "général — uniquement quand il VEUT réserver mais que le lien standard ne fonctionne pas pour lui, quelle qu'en soit la raison. "
        "prospect_name = le nom du prospect (tiré de son profil). profile_url = l'URL du profil LinkedIn du prospect si elle "
        "est visible dans son profil fourni plus haut (sinon chaîne vide). reason = brève description de ce qui bloque, dans tes mots "
        "(ex: \"refuse le lien, veut une invitation directe\", \"dit que le lien est cassé\", \"aucun créneau dispo selon lui\")."
    ),
    {"prospect_name": str, "profile_url": str, "reason": str},
)
async def notify_booking_issue(args):
    prospect_name = (args.get("prospect_name") or "un prospect").strip()
    profile_url = (args.get("profile_url") or "").strip()
    reason = (args.get("reason") or "raison non précisée").strip()
    ctx = CURRENT_CHAT_CONTEXT.get()
    persona_label = ctx.get("persona_label", config.PERSONA_DISPLAY_NAME)
    chat_id = ctx.get("chat_id", "")
    account_id = ctx.get("account_id", "")
    text = (
        f"🚨 Problème de réservation LinkedIn ({persona_label})\n"
        f"Prospect : {prospect_name}\n"
        f"Profil LinkedIn : {profile_url or 'inconnu'}\n"
        f"Chat ID : {chat_id or 'inconnu'}\n"
        f"Compte Unipile : {account_id or 'inconnu'}\n"
        f"Raison : {reason}\n"
        f"Il veut réserver mais le lien standard ne fonctionne pas pour lui — occupe-toi de le recontacter directement."
    )
    if TELEGRAM_ALERT_BOT_TOKEN and TELEGRAM_ALERT_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_ALERT_BOT_TOKEN}/sendMessage"
            payload = json.dumps({"chat_id": TELEGRAM_ALERT_CHAT_ID, "text": text}).encode("utf-8")
            req_obj = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            await asyncio.to_thread(urllib.request.urlopen, req_obj, timeout=10)
        except Exception:
            pass
    return {"content": [{"type": "text", "text": "Alerte envoyée à Martin, il va s'en occuper directement."}]}


_ACTIVITY_ID_RE = re.compile(r"activity-(\d{6,})")
_TRAILING_DIGITS_RE = re.compile(r"(\d{6,})(?!.*\d)")


def _extract_activity_id(post_url: str) -> str:
    """Extrait l'ID d'activity LinkedIn d'une URL de post. Regex prioritaire sur 'activity-<ID>',
    repli sur la dernière suite de chiffres longue trouvée dans l'URL. Chaîne vide si rien trouvé."""
    url = (post_url or "").strip()
    if not url:
        return ""
    match = _ACTIVITY_ID_RE.search(url)
    if match:
        return match.group(1)
    match = _TRAILING_DIGITS_RE.search(url)
    if match:
        return match.group(1)
    return ""


@tool(
    "like_post",
    (
        "Réagit (like / love / etc.) à un post LinkedIn du prospect, avec le compte Unipile de la conversation en cours. "
        "UTILISE ce tool dès que le prospect te demande de liker, réagir, ou mettre un j'adore sur un de ses posts. "
        "post_url = l'URL complète du post LinkedIn (visible dans son profil fourni plus haut, ou donnée par le prospect). "
        "reaction_type = le type de réaction ('like', 'celebrate', 'support', 'love', 'insightful', 'funny'), "
        "'love' par défaut sauf si le prospect précise vouloir un simple like."
    ),
    {"post_url": str, "reaction_type": str},
)
async def like_post(args):
    post_url = (args.get("post_url") or "").strip()
    reaction_type = (args.get("reaction_type") or "love").strip().lower()
    valid_reactions = {"like", "celebrate", "support", "love", "insightful", "funny"}
    if reaction_type not in valid_reactions:
        reaction_type = "love"

    activity_id = _extract_activity_id(post_url)
    if not activity_id:
        return {
            "content": [{"type": "text", "text": f"Impossible de trouver l'ID du post dans cette URL : {post_url or '(vide)'}"}],
            "is_error": True,
        }

    ctx = CURRENT_CHAT_CONTEXT.get()
    account_id = ctx.get("account_id", "")
    if not account_id:
        return {"content": [{"type": "text", "text": "Compte Unipile introuvable dans le contexte de la conversation."}], "is_error": True}

    try:
        url = f"{UNIPILE_DSN}/api/v1/posts/reaction"
        payload = {
            "account_id": account_id,
            "post_id": f"urn:li:activity:{activity_id}",
            "reaction_type": reaction_type,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"X-API-KEY": UNIPILE_ACCOUNT_KEY, "content-type": "application/json"},
            )
            resp.raise_for_status()
    except Exception as e:
        err = str(e)[:300]
        return {"content": [{"type": "text", "text": f"Échec de la réaction Unipile sur le post : {err}"}], "is_error": True}

    return {"content": [{"type": "text", "text": f"Réaction '{reaction_type}' postée avec succès sur le post."}]}


@tool(
    "request_handover",
    "Demande un handover humain (tu prends le relais). UTILISE UNIQUEMENT si : (1) le prospect demande explicitement à parler à un humain, (2) frustration ou colère significative, (3) sujet sensible (santé, deuil, crise perso), (4) tu n'as pas l'info nécessaire pour répondre correctement, (5) incohérence repérée que tu ne peux pas résoudre. Reason = en quelques mots, pourquoi.",
    {"reason": str},
)
async def request_handover(args):
    return {"content": [{"type": "text", "text": f"HANDOVER_REQUESTED::{args.get('reason', 'unspecified')}"}]}


@tool(
    "notify_stuck_conversation",
    (
        "Alerte Martin sur Telegram QUAND un prospect insiste réellement (relance 2 fois ou plus, dans ses propres mots, "
        "sur la même question ouverte ou la même demande concrète) et que tu n'as toujours pas de quoi lui répondre "
        "correctement — ni via tes skills, ni via tes tools habituels (Calendly, créneaux, site, vidéo). "
        "Exemple typique : il redemande une date précise ('bon du coup on se voit quand ?'), ou insiste sur un point "
        "concret auquel tu n'as pas de réponse ferme, et ce n'est PAS un simple silence de sa part — c'est une vraie "
        "insistance perçue. N'utilise PAS ce tool pour une première question ouverte normale (tu as le temps de répondre "
        "naturellement) — uniquement quand tu sens toi-même que ça devient vraiment insistant et que tu bloques. "
        "Continue la conversation normalement après l'alerte (une phrase qui accuse réception, jamais un blanc) — ce n'est "
        "pas un handover complet, juste une alerte envoyée en parallèle. "
        "prospect_name = nom du prospect. profile_url = URL profil LinkedIn si visible (sinon vide). "
        "question = la question/demande précise sur laquelle il insiste, dans ses mots. "
        "why_stuck = en quelques mots, pourquoi tu n'as pas la réponse."
    ),
    {"prospect_name": str, "profile_url": str, "question": str, "why_stuck": str},
)
async def notify_stuck_conversation(args):
    prospect_name = (args.get("prospect_name") or "un prospect").strip()
    profile_url = (args.get("profile_url") or "").strip()
    question = (args.get("question") or "non précisée").strip()
    why_stuck = (args.get("why_stuck") or "non précisé").strip()
    ctx = CURRENT_CHAT_CONTEXT.get()
    persona_label = ctx.get("persona_label", config.PERSONA_DISPLAY_NAME)
    chat_id = ctx.get("chat_id", "")
    account_id = ctx.get("account_id", "")
    text = (
        f"🚨 Prospect insistant ({persona_label})\n"
        f"Prospect : {prospect_name}\n"
        f"Profil LinkedIn : {profile_url or 'inconnu'}\n"
        f"Chat ID : {chat_id or 'inconnu'}\n"
        f"Compte Unipile : {account_id or 'inconnu'}\n"
        f"Insiste sur : {question}\n"
        f"Pourquoi je bloque : {why_stuck}\n"
        f"Il relance plusieurs fois sans réponse satisfaisante — regarde directement la conversation."
    )
    if TELEGRAM_ALERT_BOT_TOKEN and TELEGRAM_ALERT_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_ALERT_BOT_TOKEN}/sendMessage"
            payload = json.dumps({"chat_id": TELEGRAM_ALERT_CHAT_ID, "text": text}).encode("utf-8")
            req_obj = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            await asyncio.to_thread(urllib.request.urlopen, req_obj, timeout=10)
        except Exception:
            pass
    return {"content": [{"type": "text", "text": "Alerte envoyée à Martin, il va regarder ça directement — continue la conversation normalement en attendant."}]}


SETTER_MCP_SERVER = create_sdk_mcp_server(
    name="setter_tools",
    version="1.0.0",
    tools=[
        get_calendly_link,
        get_available_slots,
        get_youtube_link,
        get_website_link,
        load_skill,
        notify_booking_issue,
        notify_stuck_conversation,
        request_handover,
        like_post,
    ],
)

ALLOWED_TOOLS = [
    "mcp__setter_tools__get_calendly_link",
    "mcp__setter_tools__get_available_slots",
    "mcp__setter_tools__get_youtube_link",
    "mcp__setter_tools__get_website_link",
    "mcp__setter_tools__load_skill",
    "mcp__setter_tools__notify_booking_issue",
    "mcp__setter_tools__notify_stuck_conversation",
    "mcp__setter_tools__request_handover",
    "mcp__setter_tools__like_post",
]


app = FastAPI(title="Setter Agent")


class HistoryMessage(BaseModel):
    role: Literal["prospect", "me"]
    text: str


class ChatRequest(BaseModel):
    history: list[HistoryMessage] = Field(default_factory=list)
    last_message: str
    lead_profile: str = ""
    agent_persona: str = DEFAULT_PERSONA
    chat_id: str = ""
    sender_account_id: str = ""
    persona_display_name: str = ""


class ChatResponse(BaseModel):
    messages: list[str]
    handover: bool
    handover_reason: str = ""
    raw: str
    tools_called: list[str] = Field(default_factory=list)
    cost_usd: float | None = None
    duration_ms: int | None = None
    num_turns: int | None = None


def build_user_prompt(req: ChatRequest) -> str:
    persona_label = req.persona_display_name or config.PERSONA_DISPLAY_NAME
    transcript_lines = []
    for m in req.history:
        speaker = persona_label if m.role == "me" else "Prospect"
        transcript_lines.append(f"{speaker}: {m.text}")
    transcript = (
        "\n".join(transcript_lines) if transcript_lines else "(conversation vide, premier échange)"
    )
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""Date du jour : {today} (utilise cette année et pas une autre quand tu mentionnes une date).

Profil du prospect (ce que tu SAIS DÉJÀ — c'est SA bio publique scrapée + analyse). Règles d'usage :
  ❌ Tu ne lui demandes JAMAIS une info qui est déjà ici (= signal d'incompétence = perte de crédibilité immédiate)
  ❌ Tu ne lui demandes JAMAIS son ICP cible en question ouverte multi-choix
  ✅ Tu DÉDUIS son ICP / sa cible / son contexte business à partir de son Occupation + Topics + Personalization
  ✅ Si tu hésites sur ta déduction, tu la proposes comme HYPOTHÈSE à valider en 1 phrase. JAMAIS comme question ouverte.
{req.lead_profile or "(pas de profil disponible)"}

Historique de la conversation (chronologique) :
{transcript}

Dernier message reçu du prospect :
{req.last_message}

═══════════════════════════════════════════════════════════════════
PRODUIS MAINTENANT le ou les messages que tu vas envoyer au prospect.
═══════════════════════════════════════════════════════════════════

⚠️ FORMAT DE SORTIE ABSOLU :
Ta sortie texte = EXACTEMENT ce que le prospect va recevoir mot pour mot dans son DM LinkedIn.
RIEN d'autre. C'est-à-dire :

❌ ZÉRO préambule, zéro analyse écrite, zéro diagnostic verbalisé
❌ ZÉRO explication de ton raisonnement
❌ ZÉRO méta-commentaire sur ta stratégie
❌ ZÉRO description de ton processus mental

✅ UNIQUEMENT les messages exacts à envoyer, séparés par `<<NEXT>>` si plusieurs bulles.

Tout ton diagnostic, ta lecture du prospect, ta mobilisation des principes — TOUT ça se fait en pensée (extended thinking interne), JAMAIS en texte visible au prospect. Si tu écris "Je vais analyser…" en tête de ta sortie, c'est un BUG GRAVE : le prospect le lit, sait que c'est une IA, et tu perds le call.

Tes messages sortent comme si tu tapais vite sur LinkedIn — chaleureux, casual, pas un robot qui pense à haute voix."""


RATE_LIMIT_PATTERNS = [
    "429",
    "rate limit",
    "rate_limit",
    "exceed your organization",
    "exceed your account",
    "input tokens per minute",
    "output tokens per minute",
    "requests per minute",
]
OTHER_API_ERROR_PATTERNS = [
    "api error",
    "request rejected",
    "internal server error",
    "server error",
    "connection error",
    "authentication_error",
    "permission_error",
    "claude.com/en/api",
    "console.anthropic.com",
    "credit balance is too low",
    "credit balance",
    "insufficient credit",
    "insufficient funds",
    "insufficient_funds",
    "out of credits",
    "billing_error",
    "billing error",
    "your account has been suspended",
    "account suspended",
    "402",
    "payment required",
    "anthropic-version",
    "invalid_request_error",
    "overloaded_error",
    "api_error",
]


def looks_like_suspicious_short_error(text: str) -> bool:
    if not text:
        return False
    if len(text) > 150:
        return False
    lowered = text.lower()
    suspicious_words = [
        "credit", "balance", "error", "failed", "exception",
        "timeout", "unavailable", "exceeded", "limit reached",
        "try again later", "503", "504", "500",
    ]
    return any(w in lowered for w in suspicious_words)
RETRY_BACKOFF_SECONDS = [5, 15, 30]


def looks_like_rate_limit(text: str) -> bool:
    lowered = (text or "").lower()
    return any(pat in lowered for pat in RATE_LIMIT_PATTERNS)


def looks_like_api_error(text: str) -> bool:
    lowered = (text or "").lower()
    return any(pat in lowered for pat in RATE_LIMIT_PATTERNS + OTHER_API_ERROR_PATTERNS)


META_LEAK_PATTERNS = [
    "je vais d'abord analyser",
    "je vais analyser",
    "d'abord, j'analyse",
    "d'abord j'analyse",
    "je commence par analyser",
    "analysons la situation",
    "analyse de la situation",
    "le prospect est ",
    "le prospect semble",
    "le prospect montre",
    "c'est un moment de",
    "pas besoin de lookup",
    "pas besoin d'appeler",
    "lookup tools ici",
    "lookup_tool",
    "mon raisonnement",
    "mon analyse interne",
    "voici mon analyse",
    "voici ma réponse",
    "je dois maintenant",
    "je vais maintenant",
    "ma stratégie ici",
    "stratégiquement, je",
    "pour bien faire, je",
    "première étape",
    "deuxième étape",
    "étape 1 :",
    "étape 2 :",
    "mobilise les leviers",
    "mobiliser les principes",
    "diagnostique",
    "diagnostic :",
    "internal :",
    "[analyse]",
    "[diagnostic]",
    "[réflexion]",
]


def looks_like_meta_leak(text: str) -> bool:
    if not text:
        return False
    head = text[:400].lower()
    return any(pat in head for pat in META_LEAK_PATTERNS)


def sanitize_human_style(text: str) -> str:
    """Strip AI tells (typographic punctuation, smart quotes, dashes) before sending to prospect."""
    if not text:
        return text
    replacements = {
        "—": ", ",
        "–": ", ",
        "…": "...",
        # Guillemets de toutes formes : jamais utilisés, on les retire plutot que de les normaliser.
        "«": "",
        "»": "",
        "“": "",
        "”": "",
        '"': "",
        "‘": "'",
        "’": "'",
        " ": " ",
        " ": " ",
    }
    out = text
    for k, v in replacements.items():
        out = out.replace(k, v)
    # Tiret simple utilisé comme séparateur de clause (" - ") -> virgule.
    # Ne touche pas aux mots composés légitimes ("bouche-à-oreille") car ceux-ci n'ont pas d'espaces autour du tiret.
    out = re.sub(r"\s+-\s+", ", ", out)
    while "  " in out:
        out = out.replace("  ", " ")
    out = out.replace(" ;", ";")
    out = out.replace(" ,", ",").replace(",,", ",")
    # Typographie française : "?" et "!" gardent toujours une espace avant, jamais collés au mot précédent.
    out = re.sub(r"\s*([!?])", r" \1", out)
    return out.strip()


def capitalize_sentences(text: str) -> str:
    """Force une majuscule en début de message et après chaque ponctuation de fin de phrase.

    Filet de sécurité déterministe : le prompt demande déjà cette règle au modèle,
    mais un LLM peut l'oublier occasionnellement — cette fonction garantit le résultat.
    """
    if not text:
        return text

    def _cap(match: re.Match) -> str:
        return match.group(1) + match.group(2).upper()

    out = re.sub(r"^(\s*)([a-zà-ÿ])", _cap, text)
    out = re.sub(r"([.!?]\s+)([a-zà-ÿ])", _cap, out)
    return out


def enforce_space_after_punctuation(text: str) -> str:
    """Force un espace apres !, ? ou : quand colles directement au mot suivant.

    Filet de securite deterministe : le prompt demande deja cette regle au modele,
    mais un LLM peut l'oublier occasionnellement — cette fonction garantit le resultat.
    """
    if not text:
        return text
    out = re.sub(r"([!?:])([A-Za-zÀ-ÿ0-9])", r"\1 \2", text)
    return out


def parse_final_text(text: str) -> tuple[list[str], bool, str]:
    text = text.strip()
    if not text:
        return [], True, "empty_response_from_agent"
    # Le modèle enrobe parfois le signal de backticks/gras Markdown (ex: `PAUSE_CONVERSATION`) —
    # on normalise avant la comparaison stricte pour ne jamais laisser fuiter le signal brut au prospect.
    stripped_signal = text.strip("`*_ \n\t")
    if stripped_signal == HANDOVER_SIGNAL or text == HANDOVER_SIGNAL or "HANDOVER_REQUESTED::" in text:
        return [], True, ""
    if looks_like_api_error(text):
        return [], True, f"api_error_detected: {text[:300]}"
    if looks_like_suspicious_short_error(text):
        return [], True, f"suspicious_short_error_response: {text[:300]}"
    if looks_like_meta_leak(text):
        return [], True, f"meta_reasoning_leak_detected: {text[:300]}"
    parts = [p.strip() for p in text.split("<<NEXT>>") if p.strip()]
    if not parts:
        return [], True, "no_parsable_message"
    parts = [capitalize_sentences(enforce_space_after_punctuation(sanitize_human_style(p))) for p in parts]
    parts = [p for p in parts if p]
    if not parts:
        return [], True, "no_parsable_message_after_sanitize"
    if any(looks_like_meta_leak(p) for p in parts):
        return [], True, "meta_reasoning_leak_detected_post_sanitize"
    if any(looks_like_suspicious_short_error(p) for p in parts):
        return [], True, "suspicious_short_error_post_sanitize"
    return parts, False, ""


@app.get("/")
async def root():
    return {
        "status": "alive",
        "model": MODEL,
        "personas_available": list(PERSONA_CACHE.keys()),
        "default_persona": DEFAULT_PERSONA,
        "system_prompt_chars_by_persona": {p: len(s) for p, s in SYSTEM_PROMPTS.items()},
        "principes_chars": len(PRINCIPES),
        "tools": [t.split("__")[-1] for t in ALLOWED_TOOLS],
        "max_thinking_tokens": MAX_THINKING_TOKENS,
        "max_turns": MAX_TURNS,
        "relance_prompts_chars": {"quand-relancer": len(QUAND_RELANCER), "relancer": len(RELANCER)},
    }


EDIT_MINIAPP_HTML = (Path(__file__).parent / "static" / "edit_miniapp.html").read_text(encoding="utf-8")


@app.get("/telegram/edit", response_class=HTMLResponse)
async def telegram_edit_miniapp():
    return EDIT_MINIAPP_HTML


WEBAPP_HITL_HTML = (Path(__file__).parent / "static" / "webapp_hitl.html").read_text(encoding="utf-8")


@app.get("/webapp-hitl", response_class=HTMLResponse)
async def webapp_hitl():
    return WEBAPP_HITL_HTML


UNIPILE_DSN = "https://api25.unipile.com:15533"
UNIPILE_ACCOUNT_KEY = "PO2/OM2m.YyJI9+EMh58AUmfj9bJddy/P8R6eFOO341Jkx1qzuGc="
TELEGRAM_VALIDATION_CHAT_ID = "8723535937"

# Un bot Telegram dédié par compte (validation human-in-the-loop) — même mapping que les routers n8n.
TELEGRAM_BOT_TOKEN_BY_ACCOUNT = {
    "martin": "8731294695:AAGw6i-_AbGMTDiZEbuoUFmEthHP9SLEo2w",
    "jules": "8866841683:AAGGiA9EXeV4-IFJxjEPGRfiEFe2pbFMHmU",
    "thomas": "8833621341:AAGCRIG7g6Kc2nrWY-CHj9p45sZMLVap0pE",
    "theo": "8906115707:AAE6aPwnTK1PvqgkpmVZpFAX1PxAYjipF4g",
    "nathan": "8995926182:AAHxIFlLXytUTPIr4kO9fijNbhRvFffeFXo",
    "keanu": "8746521874:AAH99GjASZsHAQWWo_bY2Gc0li7nE0MTwvE",
    "christiane": "8821418083:AAGRWNswAgcVcRopqqIZWCYaNWuv6byRGo0",
    "enzo": "8775385647:AAE4xzkrAiKoN4EVgYJqG-dvJ7bLKAIc5pM",
    "henry": "8481389495:AAHoLx8BOKmSrKraKNT2uygGZ5QemvN2fc0",
    "jeanpierre": "8849108958:AAFdLERIDkvU3aGGWl0VhcWnezQn4Od0xfs",
    "jean-pierre": "8849108958:AAFdLERIDkvU3aGGWl0VhcWnezQn4Od0xfs",
    "viannard": "8678263108:AAE1ojS89fO4el5rIn-R6vW6wRoV71ZYCLk",
    "samuellyon": "8919729318:AAEej6N9QGDnfi6HY7qbA_FDaYudz_N7u90",
    "samuel": "8919729318:AAEej6N9QGDnfi6HY7qbA_FDaYudz_N7u90",
    "florian": "8979351330:AAGgzmr0GrL5TxRxnpRfLU2d0Nh635Z0Kf4",
    "franck-andrianarivony": "8792288619:AAEQkKougLgsP64baFkhQTao3rblofX9ksY",
}


class EditSubmitRequest(BaseModel):
    accountKey: str
    chatId: str
    finalText: str


class ScheduleSubmitRequest(BaseModel):
    accountKey: str
    chatId: str
    finalText: str
    delaySeconds: int


async def get_chat_prospect_name(chat_id: str) -> str:
    try:
        url = f"{UNIPILE_DSN}/api/v1/chats/{chat_id}/attendees"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"X-API-KEY": UNIPILE_ACCOUNT_KEY, "accept": "application/json"})
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if items and items[0].get("name"):
                return items[0]["name"]
    except Exception:
        pass
    return "Prospect inconnu"


async def send_telegram_confirmation(account_key: str, ok: bool, error: str = "", prospect_name: str = "") -> None:
    bot_token = TELEGRAM_BOT_TOKEN_BY_ACCOUNT.get(account_key)
    if not bot_token:
        return
    who = prospect_name or "Prospect inconnu"
    text = (
        f"✅ Réponse envoyée sur LinkedIn à {who}."
        if ok
        else f"❌ Échec de l'envoi sur LinkedIn à {who} : {error}"
    )
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": TELEGRAM_VALIDATION_CHAT_ID, "text": text})
    except Exception:
        pass


@app.post("/telegram/edit-submit")
async def telegram_edit_submit(req: EditSubmitRequest):
    """Envoi direct sur LinkedIn depuis le Mini App Telegram (bouton Envoyer),
    en contournant Telegram.WebApp.sendData() qui a un support incomplet sur Desktop."""
    prospect_name = await get_chat_prospect_name(req.chatId) if req.chatId else "Prospect inconnu"
    if not req.chatId or not req.finalText.strip():
        await send_telegram_confirmation(req.accountKey, False, "chatId ou finalText manquant", prospect_name)
        return {"ok": False, "error": "chatId ou finalText manquant"}
    try:
        url = f"{UNIPILE_DSN}/api/v1/chats/{req.chatId}/messages"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json={"text": req.finalText},
                headers={"X-API-KEY": UNIPILE_ACCOUNT_KEY, "Content-Type": "application/json"},
            )
            resp.raise_for_status()
        await send_telegram_confirmation(req.accountKey, True, prospect_name=prospect_name)
        return {"ok": True}
    except Exception as e:
        err = str(e)[:300]
        await send_telegram_confirmation(req.accountKey, False, err, prospect_name)
        return {"ok": False, "error": err}


async def send_telegram_scheduled_ack(account_key: str, delay_seconds: int, prospect_name: str) -> None:
    bot_token = TELEGRAM_BOT_TOKEN_BY_ACCOUNT.get(account_key)
    if not bot_token:
        return
    mins, secs = divmod(delay_seconds, 60)
    delay_str = f"{mins}min {secs}s" if mins else f"{secs}s"
    text = f"⏰ Réponse programmée pour {prospect_name} dans {delay_str}."
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": TELEGRAM_VALIDATION_CHAT_ID, "text": text})
    except Exception:
        pass


async def _send_after_delay(account_key: str, chat_id: str, final_text: str, delay_seconds: int, prospect_name: str) -> None:
    await asyncio.sleep(delay_seconds)
    try:
        url = f"{UNIPILE_DSN}/api/v1/chats/{chat_id}/messages"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json={"text": final_text},
                headers={"X-API-KEY": UNIPILE_ACCOUNT_KEY, "Content-Type": "application/json"},
            )
            resp.raise_for_status()
        await send_telegram_confirmation(account_key, True, prospect_name=prospect_name)
    except Exception as e:
        await send_telegram_confirmation(account_key, False, str(e)[:300], prospect_name)


@app.post("/telegram/schedule-submit")
async def telegram_schedule_submit(req: ScheduleSubmitRequest):
    """Programme l'envoi sur LinkedIn dans X secondes/minutes, depuis le bouton
    ⏰ Programmer du Mini App. Confirme immédiatement la programmation sur Telegram,
    puis envoie automatiquement une fois le délai écoulé."""
    prospect_name = await get_chat_prospect_name(req.chatId) if req.chatId else "Prospect inconnu"
    if not req.chatId or not req.finalText.strip() or req.delaySeconds <= 0:
        return {"ok": False, "error": "chatId, finalText ou delaySeconds invalide"}
    asyncio.create_task(_send_after_delay(req.accountKey, req.chatId, req.finalText, req.delaySeconds, prospect_name))
    await send_telegram_scheduled_ack(req.accountKey, req.delaySeconds, prospect_name)
    return {"ok": True}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY non configurée")

    persona = req.agent_persona if req.agent_persona in SYSTEM_PROMPTS else DEFAULT_PERSONA
    if persona not in SYSTEM_PROMPTS and SYSTEM_PROMPTS:
        persona = next(iter(SYSTEM_PROMPTS))
    system_prompt = SYSTEM_PROMPTS[persona]

    CURRENT_CHAT_CONTEXT.set({
        "chat_id": req.chat_id,
        "persona_label": req.persona_display_name or config.PERSONA_DISPLAY_NAME,
        "account_id": req.sender_account_id,
        "persona": persona,
    })

    user_prompt = build_user_prompt(req)

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=system_prompt,
        mcp_servers={"setter_tools": SETTER_MCP_SERVER},
        allowed_tools=ALLOWED_TOOLS,
        max_turns=MAX_TURNS,
        max_thinking_tokens=MAX_THINKING_TOKENS,
        permission_mode="bypassPermissions",
    )

    raw = ""
    tools_called: list[str] = []
    handover = False
    handover_reason = ""
    cost_usd: float | None = None
    duration_ms: int | None = None
    num_turns: int | None = None
    attempts_used = 0
    last_error_summary = ""

    for attempt in range(len(RETRY_BACKOFF_SECONDS) + 1):
        attempts_used = attempt + 1
        raw_chunks_local: list[str] = []
        tools_called_local: list[str] = []
        handover_local = False
        handover_reason_local = ""
        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(user_prompt)
                async for msg in client.receive_response():
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                raw_chunks_local.append(block.text)
                            elif isinstance(block, ToolUseBlock):
                                tool_short = block.name.split("__")[-1]
                                tools_called_local.append(tool_short)
                                if tool_short == "request_handover":
                                    handover_local = True
                                    handover_reason_local = (block.input or {}).get("reason", "")
                    elif isinstance(msg, ResultMessage):
                        cost_usd = getattr(msg, "total_cost_usd", None)
                        duration_ms = getattr(msg, "duration_ms", None)
                        num_turns = getattr(msg, "num_turns", None)
            raw_local = "\n".join(raw_chunks_local).strip()
            if looks_like_rate_limit(raw_local) and attempt < len(RETRY_BACKOFF_SECONDS):
                wait = RETRY_BACKOFF_SECONDS[attempt]
                last_error_summary = f"rate_limit_in_response (attempt {attempt+1}, waiting {wait}s)"
                await asyncio.sleep(wait)
                continue
            raw = raw_local
            tools_called = tools_called_local
            handover = handover_local
            handover_reason = handover_reason_local
            break
        except Exception as e:
            err_summary = f"{type(e).__name__}: {str(e)[:300]}"
            last_error_summary = err_summary
            is_rate_limit = looks_like_rate_limit(err_summary) or looks_like_rate_limit(str(e))
            if is_rate_limit and attempt < len(RETRY_BACKOFF_SECONDS):
                wait = RETRY_BACKOFF_SECONDS[attempt]
                await asyncio.sleep(wait)
                continue
            return ChatResponse(
                messages=[],
                handover=True,
                handover_reason=f"agent_loop_exception (attempt {attempt+1}): {err_summary}",
                raw="",
                tools_called=tools_called_local,
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                num_turns=num_turns,
            )
    else:
        return ChatResponse(
            messages=[],
            handover=True,
            handover_reason=f"max_retries_exceeded ({attempts_used} attempts): {last_error_summary}",
            raw="",
            tools_called=tools_called,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            num_turns=num_turns,
        )

    messages, handover_from_text, handover_reason_from_text = parse_final_text(raw)
    handover = handover or handover_from_text
    if handover_reason_from_text and not handover_reason:
        handover_reason = handover_reason_from_text

    return ChatResponse(
        messages=messages,
        handover=handover,
        handover_reason=handover_reason,
        raw=raw,
        tools_called=tools_called,
        cost_usd=cost_usd,
        duration_ms=duration_ms,
        num_turns=num_turns,
    )

# ============================================================================
# RELANCE — endpoint dédié, ne touche jamais au chemin /chat ci-dessus.
# ============================================================================

RELANCE_DIR = PROMPTS_DIR / "relance"
QUAND_RELANCER = (RELANCE_DIR / "quand-relancer.md").read_text(encoding="utf-8")
RELANCER = (RELANCE_DIR / "relancer.md").read_text(encoding="utf-8")
BUSINESS_INFO = (SKILLS_DIR / "business-info.md").read_text(encoding="utf-8")

from anthropic import AsyncAnthropic

_anthropic_client: AsyncAnthropic | None = None


def get_anthropic_client() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic()
    return _anthropic_client


class RelanceHistoryMessage(BaseModel):
    role: Literal["prospect", "me"]
    text: str
    timestamp: str  # ISO 8601 — daté, contrairement au transcript du setter


class RelanceFacts(BaseModel):
    relances_deja_envoyees: int = 0
    a_lu_sans_repondre: Literal["oui", "inconnu"] = "inconnu"
    silence_heures: float = 0.0
    video_valeur_envoyee: Literal["oui", "inconnu"] = "inconnu"
    rendez_vous_deja_facilite: Literal["oui", "inconnu"] = "inconnu"


class RelanceRequest(BaseModel):
    history: list[RelanceHistoryMessage] = Field(default_factory=list)
    lead_profile: str = ""
    agent_persona: str = DEFAULT_PERSONA
    chat_id: str = ""
    sender_account_id: str = ""
    persona_display_name: str = ""
    facts: RelanceFacts


class RelanceDecisionResult(BaseModel):
    resume: str
    dernier_pas: str
    reponse_du_prospect: Literal[
        "aucune", "accuse_poli", "report", "objection",
        "declin_poli", "accord_sans_suite", "demande_d_arret", "rendez_vous_pris",
    ]
    porte: Literal["ouverte", "close"]
    decision: Literal["relancer", "laisser"]
    angle_neuf: str = ""
    preuve: str = ""


class RelanceResponse(BaseModel):
    decision: str
    porte: str
    messages: list[str]
    etat: RelanceDecisionResult | None = None
    raw_write: str = ""
    cost_usd: float | None = None
    duration_ms: int | None = None
    anomaly: str = ""  # non vide = silence forcé, jamais un envoi


DECISION_TOOL = {
    "name": "rendre_decision",
    "description": "Rend l'état complet et la décision de relance pour ce fil.",
    "input_schema": {
        "type": "object",
        "properties": {
            "resume": {"type": "string", "description": "Deux phrases sur où en est ce fil et pourquoi il s'est éteint."},
            "dernier_pas": {"type": "string", "description": "Ce que j'ai proposé en dernier."},
            "reponse_du_prospect": {
                "type": "string",
                "enum": ["aucune", "accuse_poli", "report", "objection", "declin_poli", "accord_sans_suite", "demande_d_arret", "rendez_vous_pris"],
            },
            "porte": {"type": "string", "enum": ["ouverte", "close"]},
            "decision": {"type": "string", "enum": ["relancer", "laisser"]},
            "angle_neuf": {"type": "string", "description": "Ce que ce message apporterait qu'il n'avait pas encore. Vide si décision = laisser."},
            "preuve": {"type": "string", "description": "La citation exacte qui porte la décision."},
        },
        "required": ["resume", "dernier_pas", "reponse_du_prospect", "porte", "decision"],
    },
}


def build_dated_transcript(history: list[RelanceHistoryMessage], persona_label: str) -> str:
    lines = []
    for m in history:
        speaker = persona_label if m.role == "me" else "Prospect"
        lines.append(f"[{m.timestamp}] {speaker}: {m.text}")
    return "\n".join(lines) if lines else "(conversation vide)"


async def decide_relance(req: RelanceRequest) -> tuple[RelanceDecisionResult | None, str]:
    """Appel 1 — décider. Aucun jugement métier côté code : tout vient du modèle via tool structuré.
    Retourne (résultat, erreur). Toute anomalie -> résultat=None, jamais une décision devinée."""
    persona_label = req.persona_display_name or config.PERSONA_DISPLAY_NAME
    transcript = build_dated_transcript(req.history, persona_label)
    facts = req.facts

    user_content = f"""Historique daté du fil (chronologique) :
{transcript}

Faits mesurés par le code (n8n), à lire tels quels :
- relances_déjà_envoyées : {facts.relances_deja_envoyees}
- a_lu_sans_répondre : {facts.a_lu_sans_repondre}
- silence_heures : {facts.silence_heures:.1f}
- video_valeur_envoyée : {facts.video_valeur_envoyee}
- rendez_vous_déjà_facilité : {facts.rendez_vous_deja_facilite}

Profil du prospect :
{req.lead_profile or "(pas de profil disponible)"}

Rends ta décision via le tool rendre_decision."""

    try:
        client = get_anthropic_client()
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=QUAND_RELANCER,
            tools=[DECISION_TOOL],
            tool_choice={"type": "tool", "name": "rendre_decision"},
            messages=[{"role": "user", "content": user_content}],
        )
        for block in resp.content:
            if block.type == "tool_use" and block.name == "rendre_decision":
                result = RelanceDecisionResult(**block.input)
                return result, ""
        return None, "no_tool_use_in_response"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:300]}"


def build_relance_system_prompt(persona: str) -> str:
    """Persona + principes (comme le setter) + relancer.md + la fiche d'offre TOUJOURS injectée en dur.
    On ne demande jamais au modèle d'aller charger la fiche lui-même — elle est déjà sous ses yeux."""
    persona_block = PERSONA_CACHE.get(persona) or next(iter(PERSONA_CACHE.values()), "")
    return (
        f"{persona_block}\n\n---\n\n{PRINCIPES}\n\n---\n\n{RELANCER}"
        f"\n\n---\n\n# Fiche de mon offre (business-info, toujours à jour, fait foi)\n\n{BUSINESS_INFO}"
    )


async def write_relance(req: RelanceRequest, etat: RelanceDecisionResult) -> tuple[list[str], str, float | None, int | None]:
    """Appel 2 — rédiger. Réutilise ClaudeSDKClient comme le setter pour garder l'accès aux tools
    (get_calendly_link, get_youtube_link) — jamais d'URL inventée à la main."""
    persona = req.agent_persona if req.agent_persona in SYSTEM_PROMPTS else DEFAULT_PERSONA
    system_prompt = build_relance_system_prompt(persona)

    user_prompt = f"""État de la décision (déjà tranchée, tu ne rejuges pas) :
- résumé : {etat.resume}
- dernier pas : {etat.dernier_pas}
- réponse du prospect : {etat.reponse_du_prospect}
- angle neuf à porter : {etat.angle_neuf}

Profil du prospect :
{req.lead_profile or "(pas de profil disponible)"}

═══════════════════════════════════════════════════════════════════
PRODUIS MAINTENANT le ou les messages de relance à envoyer.
═══════════════════════════════════════════════════════════════════

⚠️ FORMAT DE SORTIE ABSOLU (identique au setter) :
Ta sortie texte = EXACTEMENT ce que le prospect va recevoir mot pour mot.
ZÉRO préambule, ZÉRO analyse, ZÉRO méta-commentaire.
UNIQUEMENT les messages exacts, séparés par `<<NEXT>>` si plusieurs bulles."""

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=system_prompt,
        mcp_servers={"setter_tools": SETTER_MCP_SERVER},
        allowed_tools=[
            "mcp__setter_tools__get_calendly_link",
            "mcp__setter_tools__get_youtube_link",
            "mcp__setter_tools__get_website_link",
        ],
        max_turns=MAX_TURNS,
        max_thinking_tokens=MAX_THINKING_TOKENS,
        permission_mode="bypassPermissions",
    )

    CURRENT_CHAT_CONTEXT.set({
        "chat_id": req.chat_id,
        "persona_label": req.persona_display_name or config.PERSONA_DISPLAY_NAME,
        "account_id": req.sender_account_id,
        "persona": persona,
    })

    raw_chunks: list[str] = []
    cost_usd: float | None = None
    duration_ms: int | None = None
    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_prompt)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        raw_chunks.append(block.text)
            elif isinstance(msg, ResultMessage):
                cost_usd = getattr(msg, "total_cost_usd", None)
                duration_ms = getattr(msg, "duration_ms", None)

    raw = "\n".join(raw_chunks).strip()
    messages, is_error, _ = parse_final_text(raw)
    if is_error:
        return [], raw, cost_usd, duration_ms
    return messages, raw, cost_usd, duration_ms


@app.post("/relance", response_model=RelanceResponse)
async def relance(req: RelanceRequest):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY non configurée")

    # Appel 1 — décider. Aucun jugement métier hors du modèle.
    etat, error = await decide_relance(req)
    if etat is None:
        # Repli sûr : toute anomalie produit le silence, jamais un envoi.
        return RelanceResponse(decision="laisser", porte="inconnue", messages=[], anomaly=f"decision_call_failed: {error}")

    if etat.decision == "laisser" or etat.porte == "close":
        # Court-circuit immédiat : rien n'est rédigé.
        return RelanceResponse(decision=etat.decision, porte=etat.porte, messages=[], etat=etat)

    # Appel 2 — rédiger.
    try:
        messages, raw, cost_usd, duration_ms = await write_relance(req, etat)
    except Exception as e:
        return RelanceResponse(
            decision="laisser", porte=etat.porte, messages=[], etat=etat,
            anomaly=f"write_call_failed: {type(e).__name__}: {str(e)[:300]}",
        )

    if not messages:
        # Le rédacteur n'a rien produit d'exploitable -> silence, pas d'envoi.
        return RelanceResponse(
            decision="laisser", porte=etat.porte, messages=[], etat=etat, raw_write=raw,
            anomaly="write_call_produced_no_usable_message",
        )

    return RelanceResponse(
        decision=etat.decision, porte=etat.porte, messages=messages, etat=etat,
        raw_write=raw, cost_usd=cost_usd, duration_ms=duration_ms,
    )

# redeploy trigger: force le rechargement du dossier prompts/personas (nouveaux personas florian, franck-andrianarivony)
# redeploy trigger 2: force le rechargement pour nouveau persona stephan-savarese
# redeploy trigger 3: force le rechargement du contenu mis a jour de stephan-savarese (format message direct)
# redeploy trigger 4: force le rechargement interdiction relations 1er degre (florian + stephan-savarese)
# redeploy trigger 5: renforce l'interdiction pour couvrir explicitement "repondre" aux non-repondus
# redeploy trigger 6: precise sources investisseurs stephan-savarese (base 35k, family offices, fonds) et nuance CA
# redeploy trigger 7: suspend l'envoi d'icebreaker sur le compte florian
# redeploy trigger 8: renforce filtre geo US/Canada uniquement pour Enzo (connexions et icebreakers)
# redeploy trigger 9: force le rechargement pour nouveau persona sarah-amouyal
# redeploy trigger 10: ajoute secteur manufacture (usinage, chaudronnerie, electricite industrielle, etc.) pour Franck
# redeploy trigger 11: force le rechargement du dossier prompts/skills (nouveau skill setting-agence-ia)
# redeploy trigger 12: force le rechargement pour nouveau persona sebastien-min (onboarding client valide 03/09)













