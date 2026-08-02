"""Agent pilote Telegram — pilote le systeme LinkedIn (n8n, GitHub, Railway) en langage naturel.

Service FastAPI separe du Brain conversationnel (main.py). Recoit les updates du bot Telegram
"System", raisonne avec Claude Agent SDK et des tools d'action, demande toujours confirmation
avant d'executer une action qui modifie l'etat (activer/desactiver un workflow, modifier du code).
"""

import asyncio
import json
import os
import urllib.request
from pathlib import Path

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
from fastapi import FastAPI, Request

import pilot_config as config

load_dotenv()

app = FastAPI(title="Pilot Agent")

PRINCIPLES = (Path(__file__).parent / "principles.md").read_text(encoding="utf-8")

# Etat de conversation en memoire — une action proposee attend confirmation avant execution.
# Cle = chat_id Telegram, valeur = dict decrivant l'action en attente.
PENDING_ACTIONS: dict[str, dict] = {}


# ============================================================================
# Tools n8n
# ============================================================================

def _n8n_headers():
    return {"X-N8N-API-KEY": config.N8N_API_KEY, "Content-Type": "application/json"}


@tool(
    "list_workflows",
    "Liste tous les workflows n8n avec leur ID, nom et etat actif/inactif. Utilise ce tool pour repondre a toute question sur l'etat du systeme (quels comptes sont actifs, etc.).",
    {},
)
async def list_workflows(args):
    req = urllib.request.Request(
        f"{config.N8N_URL}/api/v1/workflows?limit=250", headers=_n8n_headers()
    )
    data = await asyncio.to_thread(lambda: json.loads(urllib.request.urlopen(req, timeout=20).read()))
    items = [
        {"id": w["id"], "name": w["name"], "active": w["active"]}
        for w in data.get("data", [])
    ]
    return {"content": [{"type": "text", "text": json.dumps(items, ensure_ascii=False)}]}


@tool(
    "propose_workflow_action",
    (
        "Propose d'activer ou desactiver un workflow n8n precis. N'EXECUTE RIEN — cree juste une "
        "action en attente de confirmation humaine. Utilise get_available_slots... non, utilise ce "
        "tool des que l'utilisateur demande d'activer/desactiver un compte ou un workflow, JAMAIS "
        "execute_pending_action directement sans passer par ce tool d'abord. "
        "workflow_id = l'ID exact du workflow (recupere via list_workflows si besoin). "
        "action = 'activate' ou 'deactivate'. workflow_name = nom lisible pour le message de confirmation."
    ),
    {"workflow_id": str, "action": str, "workflow_name": str},
)
async def propose_workflow_action(args):
    chat_id = args.get("_chat_id", "")
    PENDING_ACTIONS[chat_id] = {
        "type": "n8n_workflow",
        "workflow_id": args["workflow_id"],
        "action": args["action"],
        "workflow_name": args["workflow_name"],
    }
    verb = "activer" if args["action"] == "activate" else "desactiver"
    return {
        "content": [
            {
                "type": "text",
                "text": f"Action proposee : {verb} le workflow '{args['workflow_name']}'. En attente de confirmation.",
            }
        ]
    }


# ============================================================================
# Tools GitHub (lecture seule pour l'instant — l'ecriture passe par confirmation explicite)
# ============================================================================

@tool(
    "read_github_file",
    "Lit le contenu d'un fichier du repo GitHub mon-setter-bot. path = chemin relatif (ex: 'prompts/principes.md').",
    {"path": str},
)
async def read_github_file(args):
    path = args["path"]
    req = urllib.request.Request(
        f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{path}",
        headers={"Authorization": f"Bearer {config.GITHUB_TOKEN}", "Accept": "application/vnd.github+json"},
    )
    try:
        data = await asyncio.to_thread(lambda: json.loads(urllib.request.urlopen(req, timeout=20).read()))
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erreur lecture : {e}"}], "is_error": True}
    import base64

    content = base64.b64decode(data["content"]).decode("utf-8")
    return {"content": [{"type": "text", "text": content}]}


# ============================================================================
# Tool Railway (statut deploiement, lecture seule)
# ============================================================================

@tool(
    "get_railway_deployment_status",
    "Verifie le statut du dernier deploiement Railway du service mon-setter-bot (SUCCESS, BUILDING, FAILED).",
    {},
)
async def get_railway_deployment_status(args):
    query = {
        "query": (
            "query { project(id: \"%s\") { services { edges { node { id name } } } } }"
            % config.RAILWAY_PROJECT_ID
        )
    }
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        data=json.dumps(query).encode("utf-8"),
        headers={"Authorization": f"Bearer {config.RAILWAY_TOKEN}", "Content-Type": "application/json"},
    )
    try:
        data = await asyncio.to_thread(lambda: json.loads(urllib.request.urlopen(req, timeout=20).read()))
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erreur Railway : {e}"}], "is_error": True}
    return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}


PILOT_MCP_SERVER = create_sdk_mcp_server(
    name="pilot_tools",
    version="1.0.0",
    tools=[list_workflows, propose_workflow_action, read_github_file, get_railway_deployment_status],
)

ALLOWED_TOOLS = [
    "mcp__pilot_tools__list_workflows",
    "mcp__pilot_tools__propose_workflow_action",
    "mcp__pilot_tools__read_github_file",
    "mcp__pilot_tools__get_railway_deployment_status",
]


# ============================================================================
# Execution reelle d'une action en attente (appelee UNIQUEMENT apres confirmation humaine)
# ============================================================================

async def execute_pending_action(chat_id: str) -> str:
    pending = PENDING_ACTIONS.pop(chat_id, None)
    if not pending:
        return "Aucune action en attente."

    if pending["type"] == "n8n_workflow":
        endpoint = "activate" if pending["action"] == "activate" else "deactivate"
        req = urllib.request.Request(
            f"{config.N8N_URL}/api/v1/workflows/{pending['workflow_id']}/{endpoint}",
            headers=_n8n_headers(),
            method="POST",
        )
        try:
            await asyncio.to_thread(urllib.request.urlopen, req, timeout=20)
            verb = "activé" if pending["action"] == "activate" else "désactivé"
            return f"✅ Workflow '{pending['workflow_name']}' {verb}."
        except Exception as e:
            return f"❌ Échec : {e}"

    return "Type d'action inconnu."


# ============================================================================
# Telegram
# ============================================================================

async def send_telegram_message(chat_id: str, text: str, reply_markup: dict | None = None) -> None:
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        await asyncio.to_thread(urllib.request.urlopen, req, timeout=15)
    except Exception:
        pass


async def run_agent(chat_id: str, user_text: str) -> None:
    options = ClaudeAgentOptions(
        model=config.MODEL,
        system_prompt=PRINCIPLES,
        mcp_servers={"pilot_tools": PILOT_MCP_SERVER},
        allowed_tools=ALLOWED_TOOLS,
        max_turns=10,
        permission_mode="bypassPermissions",
    )

    raw_chunks: list[str] = []
    proposed_action = False

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"[chat_id interne: {chat_id}]\n\n{user_text}")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        raw_chunks.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        if block.name.endswith("propose_workflow_action"):
                            proposed_action = True

    raw = "\n".join(raw_chunks).strip()
    if not raw:
        raw = "Je n'ai pas de réponse à te proposer pour cette demande."

    if proposed_action and chat_id in PENDING_ACTIONS:
        reply_markup = {
            "inline_keyboard": [[
                {"text": "✅ Confirmer", "callback_data": f"PILOT_CONFIRM:{chat_id}"},
                {"text": "❌ Annuler", "callback_data": f"PILOT_CANCEL:{chat_id}"},
            ]]
        }
        await send_telegram_message(chat_id, raw, reply_markup)
    else:
        await send_telegram_message(chat_id, raw)


@app.post("/telegram/pilot-webhook")
async def telegram_pilot_webhook(request: Request):
    body = await request.json()

    if "callback_query" in body:
        cq = body["callback_query"]
        data = cq.get("data", "")
        chat_id = str(cq.get("message", {}).get("chat", {}).get("id", ""))
        if data.startswith("PILOT_CONFIRM:"):
            result = await execute_pending_action(chat_id)
            await send_telegram_message(chat_id, result)
        elif data.startswith("PILOT_CANCEL:"):
            PENDING_ACTIONS.pop(chat_id, None)
            await send_telegram_message(chat_id, "Action annulée.")
        return {"ok": True}

    if "message" in body:
        msg = body["message"]
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = msg.get("text", "")
        if chat_id != config.AUTHORIZED_CHAT_ID:
            return {"ok": True}
        if text:
            await run_agent(chat_id, text)
        return {"ok": True}

    return {"ok": True}


@app.get("/")
async def root():
    return {"status": "alive", "service": "pilot-agent"}
