from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional, List
import uuid
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

import tools as founder_tools


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ["DB_NAME"]]

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

app = FastAPI(title="Founder Copilot API")
api_router = APIRouter(prefix="/api")


# ---------------- Models ---------------- #
class IdeaInput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_id: str
    idea: str
    target_market: Optional[str] = ""
    business_model: Optional[str] = ""
    founders_count: Optional[int] = 1
    state: Optional[str] = ""
    stage: Optional[str] = "idea"
    dpiit_registered: Optional[bool] = False
    funding_goal: Optional[str] = "bootstrap"


class ChatIn(BaseModel):
    session_id: str
    message: str


# ---------------- Storage helpers ---------------- #
async def save_profile(session_id: str, payload: dict) -> None:
    payload = {**payload, "session_id": session_id, "updated_at": datetime.now(timezone.utc).isoformat()}
    await db.founder_profiles.update_one(
        {"session_id": session_id}, {"$set": payload}, upsert=True
    )


async def load_profile(session_id: str) -> Optional[dict]:
    doc = await db.founder_profiles.find_one({"session_id": session_id}, {"_id": 0})
    return doc


async def save_report(session_id: str, report: dict) -> None:
    await db.founder_reports.update_one(
        {"session_id": session_id},
        {"$set": {"session_id": session_id, "report": report, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


# ---------------- Core routes ---------------- #
@api_router.get("/")
async def root():
    return {"ok": True, "service": "founder-copilot"}


@api_router.post("/founder/analyze")
async def analyze(body: IdeaInput):
    session_id = body.session_id or str(uuid.uuid4())
    profile = body.model_dump()
    profile.pop("session_id", None)
    await save_profile(session_id, profile)

    validation = founder_tools.validate_idea(body.idea, body.target_market, body.business_model)
    funding = founder_tools.check_funding_eligibility(
        body.idea, body.stage, body.state, body.dpiit_registered, body.founders_count
    )
    entity = founder_tools.recommend_entity_type(body.founders_count, body.funding_goal, body.business_model)
    gtm = founder_tools.generate_gtm_playbook(body.idea, body.target_market, body.business_model)
    growth = founder_tools.find_growth_opportunities(body.idea, body.stage)

    report = {
        "validation": validation,
        "funding": funding,
        "entity": entity,
        "gtm": gtm,
        "growth": growth,
    }
    await save_report(session_id, report)
    return {"session_id": session_id, "report": report, "profile": profile}


@api_router.get("/founder/profile/{session_id}")
async def profile(session_id: str):
    p = await load_profile(session_id)
    return founder_tools.get_founder_profile(p)


@api_router.get("/founder/report/{session_id}")
async def report(session_id: str):
    doc = await db.founder_reports.find_one({"session_id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="No report yet")
    return doc


# ---------------- Chat with tool-calling (light, string-parse style) ---------------- #
SYSTEM_PROMPT = """You are Founder Copilot — an AI cofounder for early-stage Indian startup founders. Warm, direct, no corporate jargon.

You have access to a stored profile of the founder (their idea, stage, state, DPIIT status, founder count, business model) and a stored report. That profile is injected into each turn as PROFILE_CONTEXT. Use it — don't ask the founder to repeat things they already told you.

You can call these tools by emitting a single line at the very start of your reply in this exact format:
[TOOL: tool_name {"arg": "value"}]

Then continue your answer using the tool's result which the system will splice in on the next turn as TOOL_RESULT. If no tool is needed, answer directly.

Available tools:
- validate_idea(idea, target_market, business_model)
- check_funding_eligibility(idea, stage, state, dpiit_registered, founders_count)
- recommend_entity_type(founders_count, funding_goal, business_model)
- generate_gtm_playbook(idea, target_market, business_model)
- find_growth_opportunities(idea, stage)
- get_founder_profile()  → returns what you already know about the founder

Style: short paragraphs, plain talk, cofounder voice. No "As an AI…". No filler. Use Indian context (₹, DPIIT, Startup India, MSME, SIDBI) naturally.
"""


def _maybe_run_tool(text: str, profile_ctx: dict) -> Optional[str]:
    """If the assistant emitted [TOOL: name {json}] on the first line, run it and return a formatted result."""
    if not text or not text.lstrip().startswith("[TOOL:"):
        return None
    line = text.lstrip().splitlines()[0]
    try:
        inner = line[len("[TOOL:"):].rstrip("]").strip()
        # split name and json
        name, _, rest = inner.partition(" ")
        args = json.loads(rest) if rest.strip().startswith("{") else {}
    except Exception:
        return None

    # Fill in from profile where missing
    prof = profile_ctx or {}
    defaults = {
        "idea": prof.get("idea", ""),
        "target_market": prof.get("target_market", ""),
        "business_model": prof.get("business_model", ""),
        "founders_count": prof.get("founders_count", 1),
        "state": prof.get("state", ""),
        "stage": prof.get("stage", "idea"),
        "dpiit_registered": prof.get("dpiit_registered", False),
        "funding_goal": prof.get("funding_goal", "bootstrap"),
    }
    for k, v in defaults.items():
        args.setdefault(k, v)

    fn = founder_tools.TOOL_REGISTRY.get(name)
    if not fn:
        return None
    if name == "get_founder_profile":
        result = fn(prof)
    else:
        # Filter args by allowed keys — call with kwargs only that the fn accepts
        import inspect
        sig = inspect.signature(fn)
        allowed = {k: v for k, v in args.items() if k in sig.parameters}
        try:
            result = fn(**allowed)
        except Exception as e:
            result = {"error": str(e)}
    return json.dumps(result, ensure_ascii=False)


@api_router.post("/founder/chat")
async def chat(body: ChatIn):
    """Streaming SSE endpoint. Front-end reads text/event-stream."""
    session_id = body.session_id
    user_text = body.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="empty message")

    prof = await load_profile(session_id) or {}
    report_doc = await db.founder_reports.find_one({"session_id": session_id}, {"_id": 0})

    # Load chat history
    hist_doc = await db.chat_history.find_one({"session_id": session_id}, {"_id": 0}) or {"messages": []}
    history: List[dict] = hist_doc.get("messages", [])

    # Append user message
    history.append({"role": "user", "content": user_text, "ts": datetime.now(timezone.utc).isoformat()})

    profile_ctx_str = json.dumps({
        "profile": prof,
        "report_summary": {
            "validation_overall": (report_doc or {}).get("report", {}).get("validation", {}).get("overall"),
            "recommended_entity": (report_doc or {}).get("report", {}).get("entity", {}).get("entity"),
        }
    }, ensure_ascii=False)

    system = SYSTEM_PROMPT + f"\n\nPROFILE_CONTEXT: {profile_ctx_str}"

    async def event_gen():
        # A fresh LlmChat per session_id
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"fc-{session_id}",
            system_message=system,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        # Feed prior turns (skip the just-added user message; we'll send it now)
        prior = history[:-1]
        # Rebuild context by sending prior turns quickly is expensive — we rely on server-side session
        # inside LlmChat which is session_id keyed. To keep this simple, we prepend a compact summary
        # of the last few turns into the current message when history exists.
        compact = ""
        if prior:
            tail = prior[-6:]
            lines = []
            for m in tail:
                who = "Founder" if m["role"] == "user" else "You (Founder Copilot)"
                lines.append(f"{who}: {m['content']}")
            compact = "PREVIOUS_TURNS:\n" + "\n".join(lines) + "\n\nCURRENT_MESSAGE:\n"

        prompt = compact + user_text

        collected = ""
        try:
            async for ev in chat_client.stream_message(UserMessage(text=prompt)):
                if isinstance(ev, TextDelta):
                    collected += ev.content
                    yield f"data: {json.dumps({'delta': ev.content})}\n\n"
                elif isinstance(ev, StreamDone):
                    break
        except Exception as e:
            logging.exception("LLM stream failed")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        # If assistant asked to call a tool, run it and do a second pass
        tool_result = _maybe_run_tool(collected, prof)
        if tool_result:
            # tell client we're calling a tool
            yield f"data: {json.dumps({'tool_call': True})}\n\n"
            second_prompt = (
                f"TOOL_RESULT: {tool_result}\n\n"
                "Now write the final answer to the founder using this tool result. "
                "Do NOT emit another [TOOL: ...] line. Just answer plainly."
            )
            collected2 = ""
            try:
                async for ev in chat_client.stream_message(UserMessage(text=second_prompt)):
                    if isinstance(ev, TextDelta):
                        collected2 += ev.content
                        yield f"data: {json.dumps({'delta': ev.content})}\n\n"
                    elif isinstance(ev, StreamDone):
                        break
            except Exception as e:
                logging.exception("LLM 2nd pass failed")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                return
            final_text = collected2
        else:
            final_text = collected

        # Persist
        history.append({"role": "assistant", "content": final_text, "ts": datetime.now(timezone.utc).isoformat()})
        await db.chat_history.update_one(
            {"session_id": session_id},
            {"$set": {"session_id": session_id, "messages": history}},
            upsert=True,
        )
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api_router.get("/founder/chat/{session_id}")
async def chat_history(session_id: str):
    doc = await db.chat_history.find_one({"session_id": session_id}, {"_id": 0})
    return {"messages": (doc or {}).get("messages", [])}


# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def _shutdown():
    mongo_client.close()
