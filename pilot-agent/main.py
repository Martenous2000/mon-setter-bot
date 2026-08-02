"""Agent pilote Telegram — accès complet au système LinkedIn (n8n, GitHub, Railway, Unipile, LinkedIn).

Service FastAPI séparé du Brain conversationnel (main.py). Reçoit les updates du bot Telegram
"System", raisonne avec Claude Agent SDK et exécute directement les actions demandées — pas de
confirmation intermédiaire, sur demande explicite de Martin qui accepte le niveau de risque.
"""

import asyncio
import base64
import json
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

import config

load_dotenv()

app = FastAPI(title="Pilot Agent")

PRINCIPLES = (Path(__file__).parent / "principles.md").read_text(encoding="utf-8")


def _http_get_json(url: str, headers: dict, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def _http_post_json(url: str, headers: dict, payload: dict | None = None, timeout: int = 20) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else b""
    req = urllib.request.Request(url, data=data, headers={**headers, "Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


# ============================================================================
# Tools n8n — pilotage complet
# ============================================================================

def _n8n_headers():
    return {"X-N8N-API-KEY": config.N8N_API_KEY, "Content-Type": "application/json"}


@tool("list_workflows", "Liste tous les workflows n8n avec leur ID, nom et etat actif/inactif.", {})
async def list_workflows(args):
    data = await asyncio.to_thread(_http_get_json, f"{config.N8N_URL}/api/v1/workflows?limit=250", _n8n_headers())
    items = [{"id": w["id"], "name": w["name"], "active": w["active"]} for w in data.get("data", [])]
    return {"content": [{"type": "text", "text": json.dumps(items, ensure_ascii=False)}]}


@tool(
    "set_workflow_active",
    "Active ou desactive directement un workflow n8n. workflow_id = ID exact (via list_workflows). active = true pour activer, false pour desactiver.",
    {"workflow_id": str, "active": bool},
)
async def set_workflow_active(args):
    endpoint = "activate" if args["active"] else "deactivate"
    try:
        await asyncio.to_thread(_http_post_json, f"{config.N8N_URL}/api/v1/workflows/{args['workflow_id']}/{endpoint}", _n8n_headers())
        return {"content": [{"type": "text", "text": f"Workflow {args['workflow_id']} {'active' if args['active'] else 'desactive'}."}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erreur : {e}"}], "is_error": True}


@tool(
    "get_n8n_executions",
    "Liste les executions recentes d'un workflow n8n, avec leur statut (success/error). workflow_id = ID du workflow.",
    {"workflow_id": str},
)
async def get_n8n_executions(args):
    data = await asyncio.to_thread(_http_get_json, f"{config.N8N_URL}/api/v1/executions?workflowId={args['workflow_id']}&limit=10", _n8n_headers())
    items = [{"id": e["id"], "status": e["status"], "startedAt": e.get("startedAt")} for e in data.get("data", [])]
    return {"content": [{"type": "text", "text": json.dumps(items, ensure_ascii=False)}]}


# ============================================================================
# Tools GitHub — lecture et ecriture completes
# ============================================================================

def _github_headers():
    return {"Authorization": f"Bearer {config.GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}


@tool("read_github_file", "Lit le contenu d'un fichier du repo GitHub. path = chemin relatif (ex: 'prompts/principes.md').", {"path": str})
async def read_github_file(args):
    try:
        data = await asyncio.to_thread(
            _http_get_json, f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{args['path']}", _github_headers()
        )
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erreur lecture : {e}"}], "is_error": True}
    content = base64.b64decode(data["content"]).decode("utf-8")
    return {"content": [{"type": "text", "text": content}]}


@tool(
    "write_github_file",
    (
        "Ecrit/modifie un fichier du repo GitHub directement (commit immediat sur main, sans confirmation). "
        "path = chemin relatif. content = nouveau contenu complet du fichier. commit_message = message de commit court."
    ),
    {"path": str, "content": str, "commit_message": str},
)
async def write_github_file(args):
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/contents/{args['path']}"
    try:
        current = await asyncio.to_thread(_http_get_json, url, _github_headers())
        sha = current.get("sha")
    except Exception:
        sha = None
    payload = {
        "message": args["commit_message"],
        "content": base64.b64encode(args["content"].encode("utf-8")).decode("ascii"),
    }
    if sha:
        payload["sha"] = sha
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={**_github_headers(), "Content-Type": "application/json"}, method="PUT")
    try:
        result = await asyncio.to_thread(lambda: json.loads(urllib.request.urlopen(req, timeout=20).read()))
        return {"content": [{"type": "text", "text": f"Fichier {args['path']} mis a jour, commit {result.get('commit', {}).get('sha', '?')[:8]}."}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erreur ecriture : {e}"}], "is_error": True}


# ============================================================================
# Tools Railway — statut et redeploiement
# ============================================================================

def _railway_query(query: str) -> dict:
    payload = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        data=payload,
        headers={"Authorization": f"Bearer {config.RAILWAY_TOKEN}", "Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=20).read())


@tool("get_railway_deployment_status", "Verifie le statut du dernier deploiement Railway du service mon-setter-bot.", {})
async def get_railway_deployment_status(args):
    query = (
        f'query {{ deployments(input: {{ projectId: "{config.RAILWAY_PROJECT_ID}", serviceId: "{config.RAILWAY_MAIN_SERVICE_ID}" }}, first: 3) '
        "{ edges { node { id status createdAt } } } }"
    )
    try:
        data = await asyncio.to_thread(_railway_query, query)
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erreur Railway : {e}"}], "is_error": True}
    return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}


# ============================================================================
# Tools Unipile — scan et envoi de messages LinkedIn
# ============================================================================

def _unipile_headers():
    return {"X-API-KEY": config.UNIPILE_API_KEY, "accept": "application/json"}


@tool(
    "list_linkedin_chats",
    "Liste les conversations LinkedIn recentes d'un compte. account_id = ID du compte Unipile.",
    {"account_id": str, "limit": int},
)
async def list_linkedin_chats(args):
    limit = args.get("limit") or 20
    data = await asyncio.to_thread(
        _http_get_json, f"{config.UNIPILE_DSN}/api/v1/chats?account_id={args['account_id']}&limit={limit}", _unipile_headers()
    )
    items = [{"id": c["id"], "timestamp": c.get("timestamp")} for c in data.get("items", [])]
    return {"content": [{"type": "text", "text": json.dumps(items, ensure_ascii=False)}]}


@tool("get_linkedin_chat_messages", "Recupere les derniers messages d'une conversation LinkedIn. chat_id = ID du chat.", {"chat_id": str, "limit": int})
async def get_linkedin_chat_messages(args):
    limit = args.get("limit") or 10
    data = await asyncio.to_thread(
        _http_get_json, f"{config.UNIPILE_DSN}/api/v1/chats/{args['chat_id']}/messages?limit={limit}", _unipile_headers()
    )
    items = [{"text": m.get("text"), "is_sender": m.get("is_sender")} for m in data.get("items", [])]
    return {"content": [{"type": "text", "text": json.dumps(items, ensure_ascii=False)}]}


@tool(
    "send_linkedin_message",
    "Envoie directement un message LinkedIn sur une conversation (sans confirmation). chat_id = ID du chat. text = message a envoyer.",
    {"chat_id": str, "text": str},
)
async def send_linkedin_message(args):
    try:
        await asyncio.to_thread(
            _http_post_json,
            f"{config.UNIPILE_DSN}/api/v1/chats/{args['chat_id']}/messages",
            _unipile_headers(),
            {"text": args["text"]},
        )
        return {"content": [{"type": "text", "text": "Message envoye sur LinkedIn."}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erreur envoi : {e}"}], "is_error": True}


PILOT_MCP_SERVER = create_sdk_mcp_server(
    name="pilot_tools",
    version="2.0.0",
    tools=[
        list_workflows,
        set_workflow_active,
        get_n8n_executions,
        read_github_file,
        write_github_file,
        get_railway_deployment_status,
        list_linkedin_chats,
        get_linkedin_chat_messages,
        send_linkedin_message,
    ],
)

ALLOWED_TOOLS = [
    "mcp__pilot_tools__list_workflows",
    "mcp__pilot_tools__set_workflow_active",
    "mcp__pilot_tools__get_n8n_executions",
    "mcp__pilot_tools__read_github_file",
    "mcp__pilot_tools__write_github_file",
    "mcp__pilot_tools__get_railway_deployment_status",
    "mcp__pilot_tools__list_linkedin_chats",
    "mcp__pilot_tools__get_linkedin_chat_messages",
    "mcp__pilot_tools__send_linkedin_message",
]


# ============================================================================
# Telegram
# ============================================================================

async def send_telegram_message(chat_id: str, text: str) -> None:
    try:
        await asyncio.to_thread(
            _http_post_json,
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            {},
            {"chat_id": chat_id, "text": text},
        )
    except Exception:
        pass


async def run_agent(chat_id: str, user_text: str) -> None:
    options = ClaudeAgentOptions(
        model=config.MODEL,
        system_prompt=PRINCIPLES,
        mcp_servers={"pilot_tools": PILOT_MCP_SERVER},
        allowed_tools=ALLOWED_TOOLS,
        max_turns=15,
        permission_mode="bypassPermissions",
    )

    raw_chunks: list[str] = []

    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_text)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        raw_chunks.append(block.text)

    raw = "\n".join(raw_chunks).strip()
    if not raw:
        raw = "Je n'ai pas de réponse à te proposer pour cette demande."
    await send_telegram_message(chat_id, raw)


@app.post("/telegram/pilot-webhook")
async def telegram_pilot_webhook(request: Request):
    body = await request.json()

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
